"""
server/errors.py
================
Custom exception hierarchy and Flask error handler registration.

SRP: this module owns the error taxonomy and the mapping
     from exception type → HTTP response — nothing else.
"""

from flask import Flask, jsonify


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class BGRemoverError(Exception):
    """
    Base class for all domain errors raised by the server.
    Carries an HTTP status code so the error handler needs
    no isinstance branching for known error types.
    """

    status_code: int = 500

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class AuthenticationError(BGRemoverError):
    """Raised when the request lacks a valid API token."""
    status_code = 401


class ValidationError(BGRemoverError):
    """Raised when request input does not meet requirements."""
    status_code = 400


class ProcessingError(BGRemoverError):
    """Raised when the image could not be processed by the ML pipeline."""
    status_code = 422


# ---------------------------------------------------------------------------
# Flask error handler registration
# ---------------------------------------------------------------------------

def register_error_handlers(app: Flask) -> None:
    """
    Attach all error handlers to *app*.
    Called once from the app factory — keeps factory.py clean.
    """

    @app.errorhandler(BGRemoverError)
    def handle_domain_error(error: BGRemoverError):
        response = jsonify({"error": error.message})
        if error.status_code == 401:
            response.headers["WWW-Authenticate"] = 'Bearer realm="bgremover"'
        return response, error.status_code

    @app.errorhandler(413)
    def handle_payload_too_large(_err):
        return jsonify({"error": "Request payload too large."}), 413

    @app.errorhandler(404)
    def handle_not_found(_err):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_err):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        app.logger.exception("Unhandled exception: %s", error)
        return jsonify({"error": "Internal server error."}), 500
