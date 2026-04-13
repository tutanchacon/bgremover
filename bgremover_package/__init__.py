"""
bgremover_package — interfaz pública del removedor de fondos.

Exporto BackgroundRemover como único punto de entrada para que los módulos
consumidores no dependan de la estructura interna del paquete.
"""

from .core import BackgroundRemover

__all__ = ['BackgroundRemover']
