"""
Configuración de procesamiento.

Centralizo todos los parámetros en un único dataclass para que tanto
el engine como la UI hablen el mismo lenguaje sin acoplarse entre sí.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

# Modelos disponibles en rembg — clave interna : etiqueta visible
AVAILABLE_MODELS: Dict[str, str] = {
    "birefnet-general":      "BiRefNet General",
    "birefnet-portrait":     "BiRefNet Portrait",
    "birefnet-general-lite": "BiRefNet Lite (rápido)",
    "u2net_human_seg":       "U2Net Personas",
    "isnet-general-use":     "ISNet General",
}

# Opciones de fondo de salida — clave interna : etiqueta visible
BACKGROUND_OPTIONS: Dict[str, str] = {
    "transparent": "Transparente",
    "white":       "Blanco",
    "black":       "Negro",
    "custom":      "Personalizado",
}


@dataclass
class ProcessingConfig:
    """
    Todos los parámetros que controlan una inferencia.
    Los defaults reproducen el comportamiento original del script bgremover.py.
    """

    # ── Modelo ────────────────────────────────────────────────────────────────
    model: str = "birefnet-general"

    # ── Alpha matting ─────────────────────────────────────────────────────────
    alpha_matting: bool = True
    alpha_matting_foreground_threshold: int = 290  # probado y funciona bien
    alpha_matting_background_threshold: int = 30
    alpha_matting_erode_size: int = 3

    # ── Post-procesamiento ────────────────────────────────────────────────────
    post_alpha_cleanup: int = 0      # 0 = off; >0 = umbral de limpieza de alpha parcial
    post_edge_smooth: float = 0.0    # 0 = off; >0 = sigma del suavizado de bordes

    # ── Fondo de salida ───────────────────────────────────────────────────────
    background: str = "transparent"
    background_color: Tuple[int, int, int] = (255, 255, 255)
