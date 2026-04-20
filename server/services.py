"""
server/services.py
==================
Business-logic layer for background removal.

SRP: coordinate the request lifecycle (delegate to the processor,
     build the result object) — no HTTP, no file I/O, no validation.
DIP: depends on IBackgroundProcessor, not on RembgProcessor.
"""

import os

from .errors import ProcessingError
from .interfaces import (
    IBackgroundProcessor,
    IProcessorService,
    ProcessingOptions,
    ProcessingResult,
)


class BackgroundRemovalService(IProcessorService):
    """
    Orchestrates a single background-removal request.

    The concrete processor is injected at construction time,
    making this class independently testable and swappable (DIP).
    """

    def __init__(self, processor: IBackgroundProcessor) -> None:
        self._processor = processor

    # ------------------------------------------------------------------
    # IProcessorService implementation
    # ------------------------------------------------------------------

    def remove_background(
        self,
        image_bytes: bytes,
        filename: str,
        options: ProcessingOptions,
    ) -> ProcessingResult:
        try:
            result_bytes = self._processor.process(image_bytes, options)
        except Exception as exc:
            raise ProcessingError(f"Image processing failed: {exc}") from exc

        return ProcessingResult(
            image_bytes=result_bytes,
            original_filename=filename,
            output_filename=self._build_output_name(filename),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_output_name(original: str) -> str:
        """Return '<stem>_nobg.png' for any input filename."""
        stem = os.path.splitext(original)[0]
        return f"{stem}_nobg.png"
