"""File-based display backend for environments without a display server.

Saves each frame as a PNG file that can be viewed in VSCode or any
image viewer. Includes an optional auto-refresh HTML viewer.
"""

import time
from pathlib import Path

from PIL import Image

from scouterhud.display.backend import DisplayBackend, DISPLAY_WIDTH, DISPLAY_HEIGHT


class PreviewBackend(DisplayBackend):
    """Saves display frames as PNG files for preview."""

    def __init__(self, output_path: str = "/tmp/scouterhud_live.png", fps_limit: float = 2.0):
        self._output_path = Path(output_path)
        self._min_interval = 1.0 / fps_limit
        self._last_write = 0.0
        self._frame_count = 0

        self.clear()

    def show(self, image: Image.Image) -> None:
        now = time.monotonic()
        if now - self._last_write < self._min_interval:
            return

        if image.size != (DISPLAY_WIDTH, DISPLAY_HEIGHT):
            image = image.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT))

        if image.mode != "RGB":
            image = image.convert("RGB")

        # Scale up 3x for visibility
        scaled = image.resize((DISPLAY_WIDTH * 3, DISPLAY_HEIGHT * 3), Image.NEAREST)
        scaled.save(str(self._output_path))
        self._last_write = now
        self._frame_count += 1

    def set_brightness(self, level: int) -> None:
        pass

    def clear(self) -> None:
        img = Image.new("RGB", (DISPLAY_WIDTH * 3, DISPLAY_HEIGHT * 3), (0, 0, 0))
        img.save(str(self._output_path))

    def close(self) -> None:
        pass

    @property
    def output_path(self) -> str:
        return str(self._output_path)
