"""
Runtime hook — se ejecuta antes que cualquier módulo de la app.

Cuando PyInstaller congela la app, sys.frozen == True y sys._MEIPASS apunta
a la carpeta temporal donde se descomprimieron los archivos.
Necesito corregir algunas rutas antes de que los paquetes se inicialicen.
"""

import os
import sys

if getattr(sys, 'frozen', False):
    # ── Caché de modelos rembg ─────────────────────────────────────────────
    # Por defecto rembg guarda los modelos en ~/.u2net/.
    # Si bundleé los modelos en el paquete, los redirijo desde ahí para que
    # el usuario no necesite descargarlos.
    bundled_models = os.path.join(sys._MEIPASS, 'bundled_models')
    if os.path.isdir(bundled_models):
        os.environ['U2NET_HOME'] = bundled_models
    else:
        # Sin modelos bundleados: uso el directorio estándar del usuario.
        # Lo creo si no existe para evitar que rembg falle al intentar escribir.
        user_cache = os.path.join(os.path.expanduser('~'), '.u2net')
        os.makedirs(user_cache, exist_ok=True)
        os.environ.setdefault('U2NET_HOME', user_cache)

    # ── onnxruntime: desactivo la búsqueda de providers externos ──────────
    # Dentro del bundle no hay un PATH útil, y onnxruntime puede lanzar
    # advertencias o fallar si intenta cargar providers que no están presentes.
    os.environ.setdefault('ORT_DISABLE_ALL_EPS_EXCEPT_CPU', '0')
