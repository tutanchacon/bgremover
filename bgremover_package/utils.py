"""
Utilidades auxiliares del paquete bgremover_package.
"""

import os
from PIL import Image


def is_supported_image(path: str) -> bool:
    """Verifico si la extensión del archivo corresponde a un formato de imagen soportado."""
    return path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))


def ensure_dir(path: str) -> None:
    """Creo el directorio si no existe."""
    os.makedirs(path, exist_ok=True)


def load_image(path: str) -> Image.Image:
    """Cargo una imagen como RGBA."""
    return Image.open(path).convert('RGBA')
