"""
wsgi.py
=======
Entry point para Gunicorn en el VPS.

Gunicorn lo invoca así:
    gunicorn wsgi:app

El modelo se configura via variable de entorno BGREMOVER_MODEL
para no hardcodear el nombre en el servicio systemd.
"""

import os
from server import create_app

_model = os.environ.get("BGREMOVER_MODEL", "isnet-general-use")
app = create_app(model_name=_model)
