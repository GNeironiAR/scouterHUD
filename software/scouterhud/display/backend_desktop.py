"""Desktop display backend using pygame.

Renders the 240x240 display in a scaled window for development.
Black pixels = transparent on the real beam splitter, so the
background is always black.
"""

import pygame
from PIL import Image

from scouterhud.display.backend import DisplayBackend, DISPLAY_WIDTH, DISPLAY_HEIGHT


class DesktopBackend(DisplayBackend):
    """Renders ScouterHUD display in a pygame window."""

    def __init__(self, scale: int = 3, title: str = "ScouterHUD"):
        self.scale = scale
        self._brightness = 255

        pygame.init()
        self._window_w = DISPLAY_WIDTH * scale
        self._window_h = DISPLAY_HEIGHT * scale
        self.screen = pygame.display.set_mode((self._window_w, self._window_h))
        pygame.display.set_caption(title)

        self.clear()

    def show(self, image: Image.Image) -> None:
        # Ensure correct size
        if image.size != (DISPLAY_WIDTH, DISPLAY_HEIGHT):
            image = image.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT))

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Scale up for visibility
        scaled = image.resize(
            (self._window_w, self._window_h), Image.NEAREST
        )

        # PIL -> pygame surface
        raw = scaled.tobytes()
        surface = pygame.image.frombuffer(raw, scaled.size, "RGB")
        self.screen.blit(surface, (0, 0))
        pygame.display.flip()

        # Process pygame events to keep window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt("Window closed")

    def set_brightness(self, level: int) -> None:
        self._brightness = max(0, min(255, level))

    def clear(self) -> None:
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def close(self) -> None:
        pygame.quit()
