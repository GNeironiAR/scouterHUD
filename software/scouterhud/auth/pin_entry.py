"""PIN entry screen for QR-Link authentication.

Renders a numeric PIN entry UI on the display and handles input events
from the Gauntlet (or keyboard in dev mode). The user navigates digits
with LEFT/RIGHT and changes values with UP/DOWN, then submits with CONFIRM.

This mirrors the Gauntlet Modo 2 (numeric) described in gauntlet-tech-doc.md.
"""

import logging
from typing import Any

from PIL import Image, ImageDraw

from scouterhud.display.backend import DISPLAY_WIDTH, DISPLAY_HEIGHT
from scouterhud.display.widgets import (
    BLACK, CYAN, DIM, GREEN, RED, WHITE, YELLOW,
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_TINY,
)
from scouterhud.input.events import EventType, InputEvent

log = logging.getLogger("scouterhud.auth.pin")


class PinEntry:
    """Interactive PIN entry with digit-by-digit navigation."""

    def __init__(self, pin_length: int = 4, device_name: str = ""):
        self.pin_length = pin_length
        self.device_name = device_name
        self._digits = [0] * pin_length
        self._cursor = 0  # which digit is selected
        self._submitted = False
        self._cancelled = False
        self._attempts = 0
        self._error_msg = ""

    @property
    def is_done(self) -> bool:
        return self._submitted or self._cancelled

    @property
    def was_cancelled(self) -> bool:
        return self._cancelled

    @property
    def pin_value(self) -> str:
        """The current PIN as a string."""
        return "".join(str(d) for d in self._digits)

    # Direct digit event types mapped to their integer value
    _DIRECT_DIGITS = {
        EventType.DIGIT_0: 0, EventType.DIGIT_1: 1, EventType.DIGIT_2: 2,
        EventType.DIGIT_3: 3, EventType.DIGIT_4: 4, EventType.DIGIT_5: 5,
        EventType.DIGIT_6: 6, EventType.DIGIT_7: 7, EventType.DIGIT_8: 8,
        EventType.DIGIT_9: 9,
    }

    def handle_event(self, event: InputEvent) -> None:
        """Process an input event. Called from the app main loop."""
        # Direct digit entry (phone numpad)
        if event.type in self._DIRECT_DIGITS:
            self._digits[self._cursor] = self._DIRECT_DIGITS[event.type]
            self._cursor = min(self._cursor + 1, self.pin_length - 1)
            self._error_msg = ""

        elif event.type == EventType.DIGIT_BACKSPACE:
            self._digits[self._cursor] = 0
            self._cursor = max(self._cursor - 1, 0)
            self._error_msg = ""

        # Rotary digit entry (Gauntlet/keyboard +/-)
        elif event.type in (EventType.DIGIT_UP, EventType.NAV_UP):
            self._digits[self._cursor] = (self._digits[self._cursor] + 1) % 10
            self._error_msg = ""

        elif event.type in (EventType.DIGIT_DOWN, EventType.NAV_DOWN):
            self._digits[self._cursor] = (self._digits[self._cursor] - 1) % 10
            self._error_msg = ""

        elif event.type in (EventType.DIGIT_NEXT, EventType.NAV_RIGHT):
            self._cursor = min(self._cursor + 1, self.pin_length - 1)

        elif event.type in (EventType.DIGIT_PREV, EventType.NAV_LEFT):
            self._cursor = max(self._cursor - 1, 0)

        elif event.type in (EventType.DIGIT_SUBMIT, EventType.CONFIRM):
            self._submitted = True
            self._attempts += 1

        elif event.type == EventType.CANCEL:
            self._cancelled = True

    def set_error(self, msg: str) -> None:
        """Show an error (e.g. 'Invalid PIN') and reset for retry."""
        self._error_msg = msg
        self._submitted = False
        self._digits = [0] * self.pin_length
        self._cursor = 0

    def render(self) -> Image.Image:
        """Render the PIN entry screen. Returns a 240x240 PIL Image."""
        img = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), BLACK)
        draw = ImageDraw.Draw(img)

        # Header
        draw.text((60, 15), "PIN REQUIRED", fill=YELLOW, font=FONT_MEDIUM)

        # Device name
        if self.device_name:
            name = self.device_name[:28]
            draw.text((10, 40), name, fill=DIM, font=FONT_TINY)

        # Separator
        draw.line([(0, 55), (240, 55)], fill=DIM, width=1)

        # Instructions
        draw.text((30, 65), "\u25c4\u25ba move   \u25b2\u25bc change", fill=DIM, font=FONT_TINY)

        # Digit boxes
        box_width = 40
        gap = 10
        total_width = self.pin_length * box_width + (self.pin_length - 1) * gap
        start_x = (DISPLAY_WIDTH - total_width) // 2
        y = 90

        for i in range(self.pin_length):
            x = start_x + i * (box_width + gap)

            # Box background
            if i == self._cursor:
                # Selected digit — highlighted
                draw.rectangle([(x, y), (x + box_width, y + 50)], outline=CYAN, width=2)
                digit_color = CYAN
            else:
                draw.rectangle([(x, y), (x + box_width, y + 50)], outline=DIM, width=1)
                digit_color = WHITE

            # Digit value
            digit_str = str(self._digits[i])
            # Center the digit in the box
            draw.text((x + 10, y + 8), digit_str, fill=digit_color, font=FONT_LARGE)

            # Up/down arrows for selected digit
            if i == self._cursor:
                draw.text((x + 14, y - 14), "\u25b2", fill=CYAN, font=FONT_TINY)
                draw.text((x + 14, y + 52), "\u25bc", fill=CYAN, font=FONT_TINY)

        # Attempt counter
        if self._attempts > 0:
            draw.text((10, 165), f"Attempt {self._attempts + 1}", fill=DIM, font=FONT_TINY)

        # Error message
        if self._error_msg:
            draw.rectangle([(0, 180), (240, 200)], fill=(80, 0, 0))
            draw.text((10, 182), self._error_msg, fill=RED, font=FONT_SMALL)

        # Bottom bar
        draw.line([(0, 215), (240, 215)], fill=DIM, width=1)
        draw.text((10, 220), "ENTER=Submit", fill=GREEN, font=FONT_TINY)
        draw.text((140, 220), "ESC=Cancel", fill=DIM, font=FONT_TINY)

        return img
