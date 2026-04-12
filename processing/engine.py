"""
Motor de procesamiento de imágenes.

Facade sobre rembg que encapsula:
  - Caché de sesiones por modelo (evita recargar ~1.5 GB en cada inferencia)
  - Pipeline de post-procesamiento configurable (patrón Strategy)
  - Composición del fondo de salida

La UI solo necesita llamar a process() y escuchar los callbacks de progreso —
no sabe nada de rembg, numpy ni cv2.
"""

import io
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from .config import ProcessingConfig

# Tipos de conveniencia
PostProcessStep = Callable[[np.ndarray], np.ndarray]
ProgressCallback = Callable[[str], None]


class ProcessingEngine:
    """
    Responsabilidad única: ejecutar una inferencia completa dado un
    ProcessingConfig y devolver una PIL.Image lista para mostrar o guardar.
    """

    def __init__(self) -> None:
        # Cacheo sesiones por nombre de modelo para no recargar pesos entre imágenes
        self._sessions: Dict[str, object] = {}

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def process(
        self,
        input_data: bytes,
        config: ProcessingConfig,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Image.Image:
        """
        Ejecuta el pipeline completo: segmentación AI → post-procesamiento → fondo.

        Args:
            input_data:  Bytes de la imagen de entrada.
            config:      Parámetros de procesamiento.
            on_progress: Callback opcional que recibe mensajes de estado.

        Returns:
            PIL.Image con el fondo eliminado y el fondo de salida aplicado.
        """
        session = self._get_or_create_session(config.model, on_progress)

        self._notify(on_progress, "Aplicando segmentación AI...")
        raw_bytes = self._run_rembg(input_data, session, config)

        result = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")

        steps = self._build_post_steps(config)
        if steps:
            self._notify(on_progress, "Aplicando post-procesamiento...")
            result = self._apply_steps(result, steps)

        return self._compose_background(result, config)

    # ── Sesiones ──────────────────────────────────────────────────────────────

    def _get_or_create_session(
        self,
        model: str,
        on_progress: Optional[ProgressCallback],
    ) -> object:
        if model not in self._sessions:
            self._notify(on_progress, f"Cargando modelo {model}...")
            from rembg import new_session
            self._sessions[model] = new_session(model)
        return self._sessions[model]

    # ── Inferencia rembg ──────────────────────────────────────────────────────

    @staticmethod
    def _run_rembg(
        input_data: bytes,
        session: object,
        config: ProcessingConfig,
    ) -> bytes:
        from rembg import remove

        kwargs: dict = {"session": session}
        if config.alpha_matting:
            kwargs.update({
                "alpha_matting": True,
                "alpha_matting_foreground_threshold": config.alpha_matting_foreground_threshold,
                "alpha_matting_background_threshold": config.alpha_matting_background_threshold,
                "alpha_matting_erode_size": config.alpha_matting_erode_size,
            })
        return remove(input_data, **kwargs)

    # ── Pipeline de post-procesamiento (Strategy) ─────────────────────────────

    def _build_post_steps(self, config: ProcessingConfig) -> List[PostProcessStep]:
        """
        Construyo la lista de pasos según la config.
        Agregar un nuevo paso es tan simple como añadir una condición aquí
        sin tocar nada más — abierto a extensión, cerrado a modificación.
        """
        steps: List[PostProcessStep] = []

        if config.post_alpha_cleanup > 0:
            steps.append(self._make_alpha_cleanup(config.post_alpha_cleanup))

        if config.post_edge_smooth > 0.0:
            steps.append(self._make_edge_smooth(config.post_edge_smooth))

        return steps

    @staticmethod
    def _apply_steps(img: Image.Image, steps: List[PostProcessStep]) -> Image.Image:
        arr = np.array(img)
        for step in steps:
            arr = step(arr)
        return Image.fromarray(arr)

    # ── Fábrica de pasos ──────────────────────────────────────────────────────
    # Uso @staticmethod con parámetros explícitos para evitar closures con
    # variables mutables que podrían capturar el valor incorrecto.

    @staticmethod
    def _make_alpha_cleanup(threshold: int) -> PostProcessStep:
        """Elimina transparencias parciales: por debajo del umbral → 0, encima → 255."""
        def step(arr: np.ndarray) -> np.ndarray:
            out = arr.copy()
            alpha = out[:, :, 3]
            out[(alpha > 0) & (alpha < threshold), 3] = 0
            out[(alpha >= threshold) & (alpha < 255), 3] = 255
            return out
        return step

    @staticmethod
    def _make_edge_smooth(sigma: float) -> PostProcessStep:
        """Suaviza el canal alpha solo en los píxeles de borde."""
        import cv2

        def step(arr: np.ndarray) -> np.ndarray:
            import cv2 as _cv2
            out = arr.copy()
            alpha = out[:, :, 3].astype(np.float32)
            alpha_smooth = _cv2.GaussianBlur(alpha, (0, 0), sigma)
            kernel = np.ones((3, 3), np.uint8)
            edges = _cv2.morphologyEx(
                (alpha > 0).astype(np.uint8), _cv2.MORPH_GRADIENT, kernel
            )
            alpha[edges > 0] = alpha_smooth[edges > 0]
            out[:, :, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
            return out
        return step

    # ── Composición de fondo ──────────────────────────────────────────────────

    @staticmethod
    def _compose_background(img: Image.Image, config: ProcessingConfig) -> Image.Image:
        if config.background == "transparent":
            return img

        color_map: Dict[str, Tuple[int, int, int]] = {
            "white":  (255, 255, 255),
            "black":  (0, 0, 0),
            "custom": config.background_color,
        }
        color = color_map.get(config.background, (255, 255, 255))
        background = Image.new("RGBA", img.size, (*color, 255))
        background.paste(img, mask=img.split()[3])
        # Si el fondo no es transparente no tiene sentido guardar alpha
        return background.convert("RGB")

    # ── Helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _notify(callback: Optional[ProgressCallback], msg: str) -> None:
        if callback:
            callback(msg)
