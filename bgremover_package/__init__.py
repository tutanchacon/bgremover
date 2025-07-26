"""
BGRemover Package - Professional Background Removal Library
===========================================================

A Python package for professional background removal with element preservation.

Usage:
    from bgremover_package import BackgroundRemover
    
    remover = BackgroundRemover()
    result = remover.remove_background('input.jpg', 'output.png')

CLI Usage:
    bgremover input.jpg output.png --threshold 20 --verbose
"""

__version__ = "1.0.0"
__author__ = "Tu Nombre"
__email__ = "tu.email@ejemplo.com"

from .core import BackgroundRemover
from .utils import validate_image, get_supported_formats

__all__ = ['BackgroundRemover', 'validate_image', 'get_supported_formats']
