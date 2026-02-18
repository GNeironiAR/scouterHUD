"""Input event types for ScouterHUD.

All input sources (keyboard, Gauntlet BLE, voice) produce InputEvent objects.
The app state machine consumes them uniformly regardless of source.
"""

from dataclasses import dataclass, field
import time
from enum import Enum, auto
from typing import Any


class EventType(Enum):
    # Navigation
    NAV_UP = auto()
    NAV_DOWN = auto()
    NAV_LEFT = auto()
    NAV_RIGHT = auto()
    CONFIRM = auto()
    CANCEL = auto()
    HOME = auto()

    # PIN/numeric entry (rotary style — Gauntlet/keyboard)
    DIGIT_UP = auto()      # increment current digit
    DIGIT_DOWN = auto()    # decrement current digit
    DIGIT_NEXT = auto()    # move to next digit
    DIGIT_PREV = auto()    # move to previous digit
    DIGIT_SUBMIT = auto()  # submit full number

    # PIN/numeric entry (direct keypad — phone app)
    DIGIT_0 = auto()
    DIGIT_1 = auto()
    DIGIT_2 = auto()
    DIGIT_3 = auto()
    DIGIT_4 = auto()
    DIGIT_5 = auto()
    DIGIT_6 = auto()
    DIGIT_7 = auto()
    DIGIT_8 = auto()
    DIGIT_9 = auto()
    DIGIT_BACKSPACE = auto()

    # Device management
    NEXT_DEVICE = auto()
    PREV_DEVICE = auto()
    SCAN_QR = auto()
    QRLINK_RECEIVED = auto()  # QR-Link URL received from phone app

    # System
    TOGGLE_VOICE = auto()
    LOCK = auto()
    QUIT = auto()


@dataclass
class InputEvent:
    type: EventType
    value: Any = None
    source: str = ""  # "keyboard", "gauntlet", "voice"
    timestamp: float = field(default_factory=time.monotonic)
