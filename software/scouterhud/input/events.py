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

    # PIN/numeric entry
    DIGIT_UP = auto()      # increment current digit
    DIGIT_DOWN = auto()    # decrement current digit
    DIGIT_NEXT = auto()    # move to next digit
    DIGIT_PREV = auto()    # move to previous digit
    DIGIT_SUBMIT = auto()  # submit full number

    # Device management
    NEXT_DEVICE = auto()
    PREV_DEVICE = auto()
    SCAN_QR = auto()

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
