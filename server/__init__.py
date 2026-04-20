"""
server package
==============
Public API surface: only create_app is exported.
Internal modules are considered implementation details.
"""

from .factory import create_app

__all__ = ["create_app"]
