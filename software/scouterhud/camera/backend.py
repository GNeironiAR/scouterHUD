"""Abstract camera backend interface.

Concrete backends:
- DesktopCameraBackend: loads QR from file or captures via webcam (OpenCV)
- PiCameraBackend: captures from Pi Camera via picamera2 (future)
"""

from abc import ABC, abstractmethod

from PIL import Image


class CameraBackend(ABC):

    @abstractmethod
    def capture_frame(self) -> Image.Image:
        """Capture a single frame and return as PIL Image."""

    @abstractmethod
    def start(self) -> None:
        """Start the camera / open the source."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the camera / release resources."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if camera is available and ready."""
