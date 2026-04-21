"""
server/routes.py
================
HTTP route definitions for the BGRemover API.

Design decisions:
  - Routes are created via a factory function, not declared at module level.
    This allows dependencies (service, validator) to be injected rather than
    imported directly — honoring DIP and enabling isolated testing.
  - Route handlers are thin: validate input, call service, return response.
    No business logic lives here (SRP).
  - All endpoints are versioned under /api/v1 for forward compatibility.

Available endpoints:
  GET  /api/v1/health      — liveness probe
  GET  /api/v1/models      — list available AI models
  POST /api/v1/remove-bg   — process an image

POST /api/v1/remove-bg
  Form fields:
    image     (file, required)  — the input image
    threshold (int, optional)   — alpha threshold 0-255, default 20
  Response:
    200 application/png  — processed image as attachment
    400                  — validation error (JSON)
    422                  — processing error (JSON)
"""

import io
import os
import secrets

from flask import Blueprint, jsonify, request, send_file

from .errors import AuthenticationError, ValidationError
from .interfaces import IImageValidator, IProcessorService, ProcessingOptions
from .processors import AVAILABLE_MODELS, DEFAULT_MODEL

# Token leído una vez al arrancar. Si la variable no está definida, la API
# queda abierta — útil en desarrollo local, nunca en producción.
_API_TOKEN: str | None = os.environ.get("BGREMOVER_API_TOKEN")

_THRESHOLD_MIN = 0
_THRESHOLD_MAX = 255
_THRESHOLD_DEFAULT = 20


def create_blueprint(
    service: IProcessorService,
    validator: IImageValidator,
) -> Blueprint:
    """
    Factory Method that wires the injected dependencies into route closures.
    Returns a Blueprint ready to be registered on any Flask app.
    """
    bp = Blueprint("api", __name__, url_prefix="/api/v1")

    # ------------------------------------------------------------------
    # Autenticación — se ejecuta antes de cada request al blueprint,
    # excepto en /health que debe ser accesible para monitoreo sin token.
    # ------------------------------------------------------------------

    @bp.before_request
    def require_token():
        if _API_TOKEN is None:
            return  # sin token configurado, acceso libre
        if request.endpoint == "api.health":
            return  # health check siempre público
        token = _extract_token(request)
        if not secrets.compare_digest(token, _API_TOKEN):
            raise AuthenticationError("Token inválido o ausente.")

    # ------------------------------------------------------------------
    # GET /api/v1/health
    # ------------------------------------------------------------------

    @bp.get("/health")
    def health():
        """Liveness probe — no auth required."""
        return jsonify({"status": "ok", "service": "bgremover"})

    # ------------------------------------------------------------------
    # GET /api/v1/models
    # ------------------------------------------------------------------

    @bp.get("/models")
    def models():
        """Return the list of available AI models."""
        return jsonify({
            "models": [
                {"id": mid, "description": desc}
                for mid, desc in AVAILABLE_MODELS.items()
            ],
            "default": DEFAULT_MODEL,
        })

    # ------------------------------------------------------------------
    # POST /api/v1/remove-bg
    # ------------------------------------------------------------------

    @bp.post("/remove-bg")
    def remove_bg():
        """
        Accept a multipart/form-data request with an image file,
        remove its background, and return the result as a PNG download.
        """
        file = request.files.get("image")

        is_valid, error_msg = validator.validate(file)
        if not is_valid:
            raise ValidationError(error_msg)

        options = ProcessingOptions(
            threshold=_parse_threshold(request.form.get("threshold"))
        )

        result = service.remove_background(
            image_bytes=file.read(),
            filename=file.filename,
            options=options,
        )

        return send_file(
            io.BytesIO(result.image_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name=result.output_filename,
        )

    return bp


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_token(req) -> str:
    """
    Acepta el token en dos formas para compatibilidad con clientes distintos:
      Authorization: Bearer <token>
      X-API-Key: <token>
    Devuelve cadena vacía si no viene ninguno, para que compare_digest
    no falle y siempre rechace en tiempo constante.
    """
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return req.headers.get("X-API-Key", "")


def _parse_threshold(value) -> int:
    """Parse threshold from request form data, clamping to valid range."""
    try:
        return max(_THRESHOLD_MIN, min(_THRESHOLD_MAX, int(value)))
    except (TypeError, ValueError):
        return _THRESHOLD_DEFAULT
