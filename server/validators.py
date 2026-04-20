"""
server/validators.py
====================
Concrete implementation of IImageValidator.

SRP: this module is responsible only for deciding whether
     an uploaded file is acceptable input — nothing else.
"""

from typing import FrozenSet, Tuple

from werkzeug.datastructures import FileStorage

from .interfaces import IImageValidator

# ---------------------------------------------------------------------------
# Module-level constants (defaults, override via constructor if needed)
# ---------------------------------------------------------------------------

_ALLOWED_EXTENSIONS: FrozenSet[str] = frozenset(
    {"png", "jpg", "jpeg", "webp", "bmp", "tiff", "gif"}
)

_DEFAULT_MAX_MB = 20
_DEFAULT_MAX_BYTES = _DEFAULT_MAX_MB * 1024 * 1024


# ---------------------------------------------------------------------------
# Concrete validator
# ---------------------------------------------------------------------------

class ImageFileValidator(IImageValidator):
    """
    Validates uploaded image files against:
      - presence (file must exist and have a name)
      - extension (must be in the allowed set)
      - size     (must not exceed the configured maximum)

    Dependencies are injected so the validator is trivially
    testable and configurable without subclassing (OCP via composition).
    """

    def __init__(
        self,
        allowed_extensions: FrozenSet[str] = _ALLOWED_EXTENSIONS,
        max_size_bytes: int = _DEFAULT_MAX_BYTES,
    ) -> None:
        self._allowed_extensions = allowed_extensions
        self._max_size_bytes = max_size_bytes

    # ------------------------------------------------------------------
    # IImageValidator implementation
    # ------------------------------------------------------------------

    def validate(self, file_storage: FileStorage) -> Tuple[bool, str]:
        """Return (True, '') or (False, human-readable reason)."""

        if not file_storage or not file_storage.filename:
            return False, "No image file provided. Use the field name 'image'."

        ext = self._extract_extension(file_storage.filename)
        if ext not in self._allowed_extensions:
            accepted = ", ".join(sorted(self._allowed_extensions))
            return False, f"File type '.{ext}' is not allowed. Accepted: {accepted}"

        size = self._measure_size(file_storage)
        if size > self._max_size_bytes:
            limit_mb = self._max_size_bytes // (1024 * 1024)
            return False, f"File exceeds the {limit_mb} MB size limit."

        return True, ""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_extension(filename: str) -> str:
        return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    @staticmethod
    def _measure_size(file_storage: FileStorage) -> int:
        """Measure file size without consuming the stream."""
        file_storage.seek(0, 2)   # seek to end
        size = file_storage.tell()
        file_storage.seek(0)      # reset to beginning
        return size
