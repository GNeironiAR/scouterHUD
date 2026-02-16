"""Abstract display backend interface.

All rendering goes through this ABC. Concrete backends:
- DesktopBackend (pygame) for development on laptop/PC
- SPIBackend (ST7789) for Raspberry Pi hardware (future)
"""

from abc import ABC, abstractmethod

from PIL import Image


# Display resolution (matches ST7789 1.3" TFT)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240


class DisplayBackend(ABC):

    @abstractmethod
    def show(self, image: Image.Image) -> None:
        """Render a PIL Image to the display."""

    @abstractmethod
    def set_brightness(self, level: int) -> None:
        """Set brightness (0-255). Not all backends support this."""

    @abstractmethod
    def clear(self) -> None:
        """Clear the display to black."""

    @abstractmethod
    def close(self) -> None:
        """Release display resources."""

    @property
    def width(self) -> int:
        return DISPLAY_WIDTH

    @property
    def height(self) -> int:
        return DISPLAY_HEIGHT
