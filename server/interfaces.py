"""
server/interfaces.py
====================
Abstract interfaces for the BGRemover HTTP server.

Applying ISP: each interface is small and focused.
Applying DIP: high-level modules depend on these abstractions,
              not on concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import NamedTuple, Tuple


# ---------------------------------------------------------------------------
# Value objects (immutable, passed between layers)
# ---------------------------------------------------------------------------

class ProcessingOptions(NamedTuple):
    """
    Options that may vary per request.
    Model is a server-level concern (session creation is expensive),
    so it is NOT included here.
    """
    threshold: int = 20


class ProcessingResult(NamedTuple):
    """Encapsulates the output of a successful processing request."""
    image_bytes: bytes
    original_filename: str
    output_filename: str


# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------

class IImageValidator(ABC):
    """
    ISP: focused solely on validating an uploaded file.
    Returns a (is_valid, error_message) tuple so callers
    do not need to catch exceptions for normal validation failures.
    """

    @abstractmethod
    def validate(self, file_storage) -> Tuple[bool, str]:
        """Return (True, '') when valid, (False, reason) when invalid."""


class IBackgroundProcessor(ABC):
    """
    Strategy interface for the low-level ML processing step.
    Swap implementations to change the underlying model or library
    without touching the service or HTTP layer (OCP + DIP).
    """

    @abstractmethod
    def process(self, image_bytes: bytes, options: ProcessingOptions) -> bytes:
        """
        Accept raw image bytes, apply background removal,
        and return the result as PNG bytes.
        """


class IProcessorService(ABC):
    """
    High-level service interface consumed by the HTTP layer.
    Orchestrates validation-free business logic (validation
    is the route handler's concern).
    """

    @abstractmethod
    def remove_background(
        self,
        image_bytes: bytes,
        filename: str,
        options: ProcessingOptions,
    ) -> ProcessingResult:
        """Remove background and return a ProcessingResult."""
