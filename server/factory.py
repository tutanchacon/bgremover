"""
server/factory.py
=================
Flask application factory with dependency injection.

Using the Factory Method pattern here provides two key benefits:

1. Testability — tests can inject mock implementations of
   IProcessorService and IImageValidator without monkey-patching.

2. Extensibility (OCP) — swapping the AI backend or the validator
   requires only passing a different object; no factory code changes.
"""

from flask import Flask

from .errors import register_error_handlers
from .interfaces import IImageValidator, IProcessorService
from .processors import DEFAULT_MODEL, RembgProcessor
from .routes import create_blueprint
from .services import BackgroundRemovalService
from .validators import ImageFileValidator


def create_app(
    processor_service: IProcessorService | None = None,
    validator: IImageValidator | None = None,
    model_name: str = DEFAULT_MODEL,
) -> Flask:
    """
    Build and configure a Flask application.

    Parameters
    ----------
    processor_service:
        Custom IProcessorService implementation.
        When None, the default stack (RembgProcessor →
        BackgroundRemovalService) is constructed automatically.
    validator:
        Custom IImageValidator implementation.
        When None, ImageFileValidator with default limits is used.
    model_name:
        AI model to load when using the default processor.
        Ignored if *processor_service* is provided explicitly.

    Returns
    -------
    Flask
        A fully configured Flask application instance.
    """
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Dependency wiring (only when defaults are needed)
    # ------------------------------------------------------------------
    if processor_service is None:
        processor = RembgProcessor(model_name=model_name)
        processor_service = BackgroundRemovalService(processor)

    if validator is None:
        validator = ImageFileValidator()

    # ------------------------------------------------------------------
    # Blueprint & error handlers registration
    # ------------------------------------------------------------------
    blueprint = create_blueprint(processor_service, validator)
    app.register_blueprint(blueprint)
    register_error_handlers(app)

    return app
