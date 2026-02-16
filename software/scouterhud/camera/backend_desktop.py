"""Desktop camera backend.

Two modes:
1. File mode: loads a QR code image from disk (for testing without camera).
2. Webcam mode: captures frames via OpenCV (if available).
"""

import logging
from pathlib import Path

from PIL import Image

from scouterhud.camera.backend import CameraBackend

log = logging.getLogger(__name__)


class DesktopCameraBackend(CameraBackend):
    """Camera backend for desktop development."""

    def __init__(self, qr_image_path: str | None = None, use_webcam: bool = False):
        self._qr_image_path = qr_image_path
        self._use_webcam = use_webcam
        self._webcam = None

    def start(self) -> None:
        if self._use_webcam:
            try:
                import cv2
                self._webcam = cv2.VideoCapture(0)
                if self._webcam.isOpened():
                    log.info("Webcam opened successfully")
                else:
                    log.warning("Webcam not available, falling back to file mode")
                    self._webcam = None
                    self._use_webcam = False
            except ImportError:
                log.warning("OpenCV not installed, falling back to file mode")
                self._use_webcam = False

    def stop(self) -> None:
        if self._webcam is not None:
            self._webcam.release()
            self._webcam = None

    def is_available(self) -> bool:
        if self._use_webcam:
            return self._webcam is not None and self._webcam.isOpened()
        return self._qr_image_path is not None and Path(self._qr_image_path).exists()

    def capture_frame(self) -> Image.Image:
        if self._use_webcam and self._webcam is not None:
            import cv2
            ret, frame = self._webcam.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(rgb)
            raise RuntimeError("Failed to capture frame from webcam")

        if self._qr_image_path:
            return Image.open(self._qr_image_path).convert("RGB")

        raise RuntimeError("No camera source configured")

    def set_qr_image(self, path: str) -> None:
        """Change the QR image file to load (for testing)."""
        self._qr_image_path = path
