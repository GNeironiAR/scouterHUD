"""Keyboard input backend for desktop development.

Maps keyboard keys to InputEvents so the full app can be tested
without Gauntlet hardware. Uses pygame key events.

Key mapping (mirrors Gauntlet pad layout):
  Arrow keys  → NAV_UP/DOWN/LEFT/RIGHT
  Enter       → CONFIRM
  Escape      → CANCEL
  H           → HOME
  N           → NEXT_DEVICE
  P           → PREV_DEVICE
  Q           → QUIT
  S           → SCAN_QR

In numeric mode (set externally):
  UP/DOWN     → DIGIT_UP/DIGIT_DOWN
  LEFT/RIGHT  → DIGIT_PREV/DIGIT_NEXT
  Enter       → DIGIT_SUBMIT
"""

import logging
from collections import deque

from scouterhud.input.backend import InputBackend
from scouterhud.input.events import EventType, InputEvent

log = logging.getLogger("scouterhud.input.keyboard")

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class KeyboardInput(InputBackend):
    """Reads keyboard input via pygame events."""

    def __init__(self):
        self._queue: deque[InputEvent] = deque(maxlen=32)
        self._running = False
        self._numeric_mode = False

    @property
    def name(self) -> str:
        return "keyboard"

    @property
    def numeric_mode(self) -> bool:
        return self._numeric_mode

    @numeric_mode.setter
    def numeric_mode(self, value: bool) -> None:
        self._numeric_mode = value

    def start(self) -> None:
        if not _HAS_PYGAME:
            log.warning("pygame not available, keyboard input disabled")
            return
        self._running = True
        log.info("Keyboard input started")

    def stop(self) -> None:
        self._running = False

    def poll(self) -> InputEvent | None:
        if not self._running or not _HAS_PYGAME:
            return None

        # Pump pygame events and convert key presses
        for event in pygame.event.get(eventtype=pygame.KEYDOWN):
            mapped = self._map_key(event.key)
            if mapped:
                self._queue.append(mapped)

        # Also drain QUIT events
        for event in pygame.event.get(eventtype=pygame.QUIT):
            self._queue.append(InputEvent(type=EventType.QUIT, source="keyboard"))

        # Put back any other events so display backend can see them
        pygame.event.pump()

        return self._queue.popleft() if self._queue else None

    def _map_key(self, key: int) -> InputEvent | None:
        if self._numeric_mode:
            return self._map_key_numeric(key)
        return self._map_key_nav(key)

    def _map_key_nav(self, key: int) -> InputEvent | None:
        mapping = {
            pygame.K_UP: EventType.NAV_UP,
            pygame.K_DOWN: EventType.NAV_DOWN,
            pygame.K_LEFT: EventType.NAV_LEFT,
            pygame.K_RIGHT: EventType.NAV_RIGHT,
            pygame.K_RETURN: EventType.CONFIRM,
            pygame.K_ESCAPE: EventType.CANCEL,
            pygame.K_h: EventType.HOME,
            pygame.K_n: EventType.NEXT_DEVICE,
            pygame.K_p: EventType.PREV_DEVICE,
            pygame.K_q: EventType.QUIT,
            pygame.K_s: EventType.SCAN_QR,
        }
        event_type = mapping.get(key)
        if event_type:
            return InputEvent(type=event_type, source="keyboard")
        return None

    def _map_key_numeric(self, key: int) -> InputEvent | None:
        mapping = {
            pygame.K_UP: EventType.DIGIT_UP,
            pygame.K_DOWN: EventType.DIGIT_DOWN,
            pygame.K_LEFT: EventType.DIGIT_PREV,
            pygame.K_RIGHT: EventType.DIGIT_NEXT,
            pygame.K_RETURN: EventType.DIGIT_SUBMIT,
            pygame.K_ESCAPE: EventType.CANCEL,
        }
        event_type = mapping.get(key)
        if event_type:
            return InputEvent(type=event_type, source="keyboard")
        return None


class StdinKeyboardInput(InputBackend):
    """Fallback keyboard input using stdin (for --preview mode without pygame window).

    Uses non-blocking reads. Single key presses:
      w/a/s/d → NAV, Enter → CONFIRM, x → CANCEL, q → QUIT
      n → NEXT_DEVICE, p → PREV_DEVICE
    """

    def __init__(self):
        self._queue: deque[InputEvent] = deque(maxlen=32)
        self._running = False
        self._numeric_mode = False
        self._old_settings = None

    @property
    def name(self) -> str:
        return "keyboard-stdin"

    @property
    def numeric_mode(self) -> bool:
        return self._numeric_mode

    @numeric_mode.setter
    def numeric_mode(self, value: bool) -> None:
        self._numeric_mode = value

    def start(self) -> None:
        try:
            import sys
            import termios
            import tty
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            self._running = True
            log.info("Stdin keyboard input started (w/a/s/d=nav, enter=confirm, x=cancel, q=quit)")
        except Exception:
            log.warning("Cannot set terminal to cbreak mode, stdin input disabled")

    def stop(self) -> None:
        self._running = False
        if self._old_settings:
            import sys
            import termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)

    def poll(self) -> InputEvent | None:
        if not self._running:
            return None

        import sys
        import select

        # Non-blocking read
        if select.select([sys.stdin], [], [], 0)[0]:
            ch = sys.stdin.read(1)
            mapped = self._map_char(ch)
            if mapped:
                return mapped

        return None

    def _map_char(self, ch: str) -> InputEvent | None:
        if self._numeric_mode:
            mapping = {
                "w": EventType.DIGIT_UP,
                "s": EventType.DIGIT_DOWN,
                "a": EventType.DIGIT_PREV,
                "d": EventType.DIGIT_NEXT,
                "\n": EventType.DIGIT_SUBMIT,
                "\r": EventType.DIGIT_SUBMIT,
                "x": EventType.CANCEL,
            }
        else:
            mapping = {
                "w": EventType.NAV_UP,
                "s": EventType.NAV_DOWN,
                "a": EventType.NAV_LEFT,
                "d": EventType.NAV_RIGHT,
                "\n": EventType.CONFIRM,
                "\r": EventType.CONFIRM,
                "x": EventType.CANCEL,
                "h": EventType.HOME,
                "n": EventType.NEXT_DEVICE,
                "p": EventType.PREV_DEVICE,
                "q": EventType.QUIT,
            }

        event_type = mapping.get(ch)
        if event_type:
            return InputEvent(type=event_type, source="keyboard-stdin")
        return None

    @property
    def is_available(self) -> bool:
        return self._running
