#!/usr/bin/env python3
"""
Background Remover - Hibrido BiRefNet + recuperacion de elementos de color
==========================================================================

Estrategia en dos pasos:
  1. BiRefNet define la silueta principal (pelo, cuerpo, bordes finos).
  2. Los pixels con color que quedaron fuera de esa mascara pero que NO son
     fondo blanco exterior se recuperan automaticamente (serpentines, confetti,
     accesorios sueltos).

De este modo el blanco interno del personaje (ojos, reloj, ropa) se preserva
porque BiRefNet ya lo incluyo en su mascara, y el fondo blanco exterior
desaparece porque el flood-fill lo detecta correctamente.

Uso:
    python bgremover.py entrada.png salida.png [verbose]
"""

from rembg import remove, new_session
from PIL import Image
import numpy as np
from collections import deque
import sys
import os
import io


def _exterior_white_mask(data, tolerance):
    """
    Devuelve una mascara booleana de los pixels blancos conectados al borde
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


def remove_background(input_path, output_path, verbose=False, tolerance=30):
    """
    Elimina el fondo usando BiRefNet como base y recuperando elementos de color
    que el modelo haya perdido (decoraciones, accesorios sueltos).

    Args:
        input_path (str): Ruta de la imagen de entrada
        output_path (str): Ruta de la imagen de salida
        verbose (bool): Mostrar informacion detallada del proceso
        tolerance (int): Tolerancia para detectar blanco exterior (default 30)

    Returns:
        bool: True si el proceso fue exitoso
    """
    try:
        if verbose:
            print(f"📸 Cargando imagen: {input_path}")

        if not os.path.exists(input_path):
            print(f"❌ Error: No se encuentra el archivo {input_path}")
            return False

        # --- Paso 1: BiRefNet define la silueta principal ---
        # Reactivo alpha matting pero con erode_size=0 para refinar los bordes del pelo
        # sin comerse los detalles finos. El erode_size=3 anterior era el culpable de
        # perder manos y decoraciones. El foreground_threshold=290 estaba fuera de rango.
        if verbose:
            print("🤖 Paso 1: Segmentando con BiRefNet + alpha matting...")

        session = new_session('birefnet-portrait')

        with open(input_path, 'rb') as f:
            input_data = f.read()

        birefnet_output = remove(
            input_data,
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=1,
        )
        birefnet_img = Image.open(io.BytesIO(birefnet_output)).convert('RGBA')
        birefnet_alpha = np.array(birefnet_img)[:, :, 3]  # canal alpha: 0=fondo, 255=sujeto

        # --- Paso 2: Detecto el fondo blanco exterior por flood-fill ---
        # Esto me da los pixels blancos conectados al borde (fondo real),
        # sin tocar los blancos internos del personaje (ojos, reloj, ropa).
        if verbose:
            print("🎯 Paso 2: Detectando fondo blanco exterior...")

        img = Image.open(input_path).convert('RGBA')
        data = np.array(img)
        exterior_white, is_white = _exterior_white_mask(data, tolerance)

        # --- Paso 3: Combino ambas mascaras ---
        # Un pixel se conserva si BiRefNet lo incluyo como primer plano
        # O si tiene color (no es blanco) y no es fondo exterior.
        # Esto recupera serpentines y confetti que BiRefNet ignoro.
        if verbose:
            print("🔀 Paso 3: Combinando mascaras...")

        birefnet_fg = birefnet_alpha > 10  # umbral bajo para no perder semitransparencias
        is_colored = ~is_white
        colored_outside_birefnet = is_colored & ~birefnet_fg & ~exterior_white

        result = data.copy()

        # Comienzo con la alpha de BiRefNet (preserva bordes suaves del pelo)
        result[:, :, 3] = birefnet_alpha

        # Elimino el fondo blanco exterior que BiRefNet haya dejado pasar
        result[exterior_white, 3] = 0

        # Limpio la neblina residual del pelo: pixels casi transparentes que estén
        # en zona de fondo exterior son artefactos del matting, no pelo real.
        # Acoto a exterior_white para no crear hoyos dentro de la silueta.
        result[(birefnet_alpha < 30) & exterior_white, 3] = 0

        # Recupero los pixels de color que BiRefNet no incluyo (decoraciones)
        result[colored_outside_birefnet, 3] = 255

        # Suavizo el borde exterior de los elementos decorativos recuperados.
        # Dilato su mascara 2px para encontrar la franja de transicion con el fondo
        # y aplico alpha proporcional a la fuerza del color, igual que en el pelo.
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

        # --- Paso 4: Descontaminacion de color blanco en bordes ---
        # Los pixels semitransparentes del borde mezclan el color real con el
        # blanco del fondo original. Calculo el color verdadero deshaciendo esa mezcla:
        # Si observed = a * F + (1-a) * 255, entonces F = (observed - 255) / a + 255
        if verbose:
            print("🧹 Paso 4: Descontaminando halo blanco en bordes...")

        semi_mask = (result[:, :, 3] > 20) & (result[:, :, 3] < 235)
        if semi_mask.any():
            a = result[semi_mask, 3].astype(np.float32) / 255.0
            for c in range(3):
                observed = result[semi_mask, c].astype(np.float32)
                true_color = (observed - 255.0) / a + 255.0
                result[semi_mask, c] = np.clip(true_color, 0, 255).astype(np.uint8)

        Image.fromarray(result).save(output_path, 'PNG')

        if verbose:
            print(f"✅ Imagen guardada en: {output_path}")

        return True

    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Funcion principal del script."""
    if len(sys.argv) < 3:
        print("Uso: python bgremover.py <imagen_entrada> <imagen_salida> [verbose]")
        print("\nEjemplos:")
        print("  python bgremover.py avatar.jpg resultado.png")
        print("  python bgremover.py imagen.png limpia.png true")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    verbose = len(sys.argv) > 3 and sys.argv[3].lower() in ['true', '1', 'yes', 'v']

    print("🎨 Background Remover - BiRefNet + recuperacion de color")
    print("=" * 55)

    success = remove_background(input_path, output_path, verbose)

    if success:
        print("\n🎉 Proceso completado exitosamente!")
    else:
        print("\n💥 Error durante el procesamiento")
        sys.exit(1)


if __name__ == "__main__":
    main()
