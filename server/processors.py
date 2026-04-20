"""
server/processors.py
====================
Concrete Strategy implementations of IBackgroundProcessor.

Each class encapsulates a specific ML backend.
To add a new backend, create a new class implementing
IBackgroundProcessor — no other file needs to change (OCP).

NOTE: Works entirely in-memory (bytes → bytes) with no file I/O,
which is the correct approach for an HTTP service.
"""

import io

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

from .interfaces import IBackgroundProcessor, ProcessingOptions

# ---------------------------------------------------------------------------
# Model registry — single source of truth for available models
# ---------------------------------------------------------------------------

AVAILABLE_MODELS: dict[str, str] = {
    "isnet-general-use": "ISNet — best general-purpose quality (default)",
    "u2net":             "U²Net — fast, good quality",
    "u2netp":            "U²Net-p — lightweight, lower accuracy",
    "silueta":           "Silueta — optimised for portraits / people",
}

DEFAULT_MODEL = "isnet-general-use"


# ---------------------------------------------------------------------------
# Concrete processor
# ---------------------------------------------------------------------------

class RembgProcessor(IBackgroundProcessor):
    """
    Background processor backed by the rembg library.

    Implements the same processing pipeline as BackgroundRemover
    (bgremover_package/core.py) but operates entirely on bytes
    so it integrates cleanly with the HTTP layer — no temp files.

    Responsibilities (SRP):
      - Run AI segmentation via rembg.
      - Apply transparency correction.
      - Apply conservative edge smoothing.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        if model_name not in AVAILABLE_MODELS:
            raise ValueError(
                f"Unknown model '{model_name}'. "
                f"Available: {', '.join(AVAILABLE_MODELS)}"
            )
        self._model_name = model_name
        # Session creation is expensive; keep it for the server lifetime.
        self._session = new_session(model_name)

    # ------------------------------------------------------------------
    # IBackgroundProcessor implementation
    # ------------------------------------------------------------------

    def process(self, image_bytes: bytes, options: ProcessingOptions) -> bytes:
        """Remove background and return PNG bytes."""
        segmented_bytes = remove(image_bytes, session=self._session)

        result_array = np.array(Image.open(io.BytesIO(segmented_bytes)))

        result_array = self._fix_transparencies(result_array, options.threshold)
        result_array = self._smooth_edges(result_array)

        buffer = io.BytesIO()
        Image.fromarray(result_array).save(buffer, format="PNG")
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # Private pipeline steps
    # ------------------------------------------------------------------

    @staticmethod
    def _fix_transparencies(img: np.ndarray, threshold: int) -> np.ndarray:
        """
        Snap partial alpha values to either 0 or 255.
        - alpha < threshold  → noise → fully transparent
        - threshold ≤ alpha < 255 → character element → fully opaque
        This preserves all foreground elements (globes, accessories…)
        and discards only very faint artefacts.
        """
        result = img.copy()
        alpha = result[:, :, 3]
        result[(alpha > 0) & (alpha < threshold), 3] = 0    # noise
        result[(alpha >= threshold) & (alpha < 255), 3] = 255  # element
        return result

    @staticmethod
    def _smooth_edges(img: np.ndarray) -> np.ndarray:
        """
        Apply light Gaussian smoothing exclusively on edge pixels.
        Interior (solid) pixels are left untouched to avoid blurring
        fine details like hair or thin accessories.
        """
        result = img.copy()
        alpha = result[:, :, 3].astype(np.float32)

        alpha_smooth = cv2.GaussianBlur(alpha, (3, 3), 0.5)

        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(
            (alpha > 0).astype(np.uint8), cv2.MORPH_GRADIENT, kernel
        )
        alpha[edges > 0] = alpha_smooth[edges > 0]

        result[:, :, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
        return result
