"""Abstract base class for input backends.

Each backend (keyboard, Gauntlet BLE, voice) implements this interface.
The InputManager polls all backends and merges events into one queue.
"""

from abc import ABC, abstractmethod

from scouterhud.input.events import InputEvent


class InputBackend(ABC):
    """Base class for all input sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this input source."""
        ...

    @abstractmethod
    def start(self) -> None:
        """Initialize the input source."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Clean up resources."""
        ...

    @abstractmethod
    def poll(self) -> InputEvent | None:
        """Non-blocking check for the next input event. Returns None if no event."""
        ...

    @property
    def is_available(self) -> bool:
        """Whether this backend is currently connected/available."""
        return True
