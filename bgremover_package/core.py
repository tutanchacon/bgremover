"""
Clase BackgroundRemover — envuelve la lógica de bgremover.py en una interfaz
orientada a objetos para que otros módulos puedan instanciarla sin depender
del script de línea de comandos directamente.
"""

import io
import os
from collections import deque

import numpy as np
from PIL import Image
from rembg import remove, new_session


def _exterior_white_mask(data, tolerance):
    """
    Devuelvo una máscara booleana de los píxeles blancos conectados al borde
    de la imagen. Solo elimino el fondo exterior, no los blancos internos.
    """
    r = data[:, :, 0].astype(np.int32)
    g = data[:, :, 1].astype(np.int32)
    b = data[:, :, 2].astype(np.int32)

    is_white = (r >= 255 - tolerance) & (g >= 255 - tolerance) & (b >= 255 - tolerance)
    h, w = is_white.shape

    visited = np.zeros((h, w), dtype=bool)
    queue = deque()

    def seed(y, x):
        if is_white[y, x] and not visited[y, x]:
            visited[y, x] = True
            queue.append((y, x))

    for x in range(w):
        seed(0, x)
        seed(h - 1, x)
    for y in range(1, h - 1):
        seed(y, 0)
        seed(y, w - 1)

    neighbors = ((-1, 0), (1, 0), (0, -1), (0, 1))
    while queue:
        y, x = queue.popleft()
        for dy, dx in neighbors:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                seed(ny, nx)

    return visited, is_white


class BackgroundRemover:
    """
    Quito el fondo de una imagen usando BiRefNet como segmentador principal
    y recupero los elementos de color que el modelo haya perdido (decoraciones,
    accesorios, confetti). El fondo blanco exterior se elimina por flood-fill
    para no tocar los blancos internos del personaje.
    """

    def __init__(self, tolerance: int = 30):
        # Cacheo la sesión para no recargar el modelo en cada imagen
        self._session = None
        self.tolerance = tolerance

    def _get_session(self):
        if self._session is None:
            self._session = new_session('birefnet-portrait')
        return self._session

    def remove_background(self, input_path: str, output_path: str, verbose: bool = False) -> bool:
        """
        Elimino el fondo de input_path y guardo el resultado en output_path.

        Returns:
            True si el proceso fue exitoso, False en caso contrario.
        """
        try:
            if not os.path.exists(input_path):
                print(f"Error: No se encuentra el archivo {input_path}")
                return False

            session = self._get_session()

            with open(input_path, 'rb') as f:
                input_data = f.read()

            # Paso 1: BiRefNet define la silueta principal con alpha matting
            birefnet_output = remove(
                input_data,
                session=session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10,
                alpha_matting_erode_size=1,
            )
            birefnet_img = Image.open(io.BytesIO(birefnet_output)).convert('RGBA')
            birefnet_alpha = np.array(birefnet_img)[:, :, 3]

            # Paso 2: detecto el fondo blanco exterior por flood-fill
            img = Image.open(input_path).convert('RGBA')
            data = np.array(img)
            exterior_white, is_white = _exterior_white_mask(data, self.tolerance)

            # Paso 3: combino ambas máscaras, recuperando elementos de color
            birefnet_fg = birefnet_alpha > 10
            is_colored = ~is_white
            colored_outside_birefnet = is_colored & ~birefnet_fg & ~exterior_white

            result = data.copy()
            result[:, :, 3] = birefnet_alpha
            result[exterior_white, 3] = 0
            result[(birefnet_alpha < 30) & exterior_white, 3] = 0
            result[colored_outside_birefnet, 3] = 255

            # Suavizo el borde exterior de los elementos decorativos recuperados
            deco_border = colored_outside_birefnet.copy()
            for _ in range(4):
                deco_border = (
                    np.roll(deco_border, 1, axis=0) | np.roll(deco_border, -1, axis=0) |
                    np.roll(deco_border, 1, axis=1) | np.roll(deco_border, -1, axis=1)
                )
            deco_border_zone = deco_border & ~colored_outside_birefnet & exterior_white

            r_ch = data[:, :, 0].astype(np.int32)
            g_ch = data[:, :, 1].astype(np.int32)
            b_ch = data[:, :, 2].astype(np.int32)
            whiteness = np.minimum(r_ch, np.minimum(g_ch, b_ch))
            color_strength = np.clip((1.0 - whiteness / 255.0) * 2.5, 0.0, 1.0)
            result[deco_border_zone, 3] = (255 * color_strength[deco_border_zone]).astype(np.uint8)

            # Paso 4: descontaminación del halo blanco en bordes semitransparentes
            semi_mask = (result[:, :, 3] > 20) & (result[:, :, 3] < 235)
            if semi_mask.any():
                a = result[semi_mask, 3].astype(np.float32) / 255.0
                for c in range(3):
                    observed = result[semi_mask, c].astype(np.float32)
                    true_color = (observed - 255.0) / a + 255.0
                    result[semi_mask, c] = np.clip(true_color, 0, 255).astype(np.uint8)

            Image.fromarray(result).save(output_path, 'PNG')
            return True

        except Exception as e:
            print(f"Error durante el procesamiento: {e}")
            import traceback
            traceback.print_exc()
            return False
