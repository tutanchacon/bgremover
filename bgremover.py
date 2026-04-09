#!/usr/bin/env python3
"""
Background Remover - Eliminacion profesional de fondos
=======================================================

Usa BiRefNet con alpha matting para resultados de calidad profesional,
similar a remove.bg.

Uso:
    python bgremover.py input.png output.png [verbose]

Ejemplos:
    python bgremover.py avatar.jpg resultado.png
    python bgremover.py imagen.png limpio.png true
"""

from rembg import remove, new_session
from PIL import Image
import sys
import os
import io


def remove_background(input_path, output_path, verbose=False):
    """
    Elimina el fondo de una imagen usando BiRefNet con alpha matting.

    Args:
        input_path (str): Ruta de la imagen de entrada
        output_path (str): Ruta de la imagen de salida
        verbose (bool): Mostrar informacion detallada del proceso

    Returns:
        bool: True si el proceso fue exitoso
    """
    try:
        if verbose:
            print(f"📸 Cargando imagen: {input_path}")

        # Verifico que el archivo existe
        if not os.path.exists(input_path):
            print(f"❌ Error: No se encuentra el archivo {input_path}")
            return False

        # Creo sesion BiRefNet (modelo mas avanzado)
        if verbose:
            print("🤖 Inicializando modelo BiRefNet...")
        session = new_session('birefnet-general')

        # Cargo la imagen
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()

        # Proceso con alpha matting optimizado
        if verbose:
            print("🎯 Aplicando segmentacion con alpha matting...")
        output_data = remove(
            input_data,
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=290,
            alpha_matting_background_threshold=30,
            alpha_matting_erode_size=3
        )

        # Guardo resultado
        result = Image.open(io.BytesIO(output_data))
        result.save(output_path, format='PNG')

        if verbose:
            print(f"✅ Imagen guardada en: {output_path}")

        return True

    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
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

    print("🎨 Background Remover - BiRefNet + Alpha Matting")
    print("=" * 50)

    success = remove_background(input_path, output_path, verbose)

    if success:
        print("\n🎉 Proceso completado exitosamente!")
    else:
        print("\n💥 Error durante el procesamiento")
        sys.exit(1)


if __name__ == "__main__":
    main()
