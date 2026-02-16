"""Unified input manager that polls all backends.

Merges events from keyboard, Gauntlet, voice, etc. into a single stream.
The app state machine calls input_manager.poll() to get the next event.
"""

import logging

from scouterhud.input.backend import InputBackend
from scouterhud.input.events import InputEvent

log = logging.getLogger("scouterhud.input")


class InputManager:
    """Polls multiple input backends and returns events in priority order."""

    def __init__(self, backends: list[InputBackend] | None = None):
        self._backends: list[InputBackend] = backends or []

    def add_backend(self, backend: InputBackend) -> None:
        self._backends.append(backend)
        log.info(f"Input backend added: {backend.name}")

    def start(self) -> None:
        for backend in self._backends:
            try:
                backend.start()
            except Exception as e:
                log.warning(f"Failed to start input backend {backend.name}: {e}")

    def stop(self) -> None:
        for backend in self._backends:
            try:
                backend.stop()
            except Exception:
                pass

    def poll(self) -> InputEvent | None:
        """Non-blocking poll of all backends. Returns first event found."""
        for backend in self._backends:
            if not backend.is_available:
                continue
            event = backend.poll()
            if event:
                return event
        return None

    def set_numeric_mode(self, enabled: bool) -> None:
        """Switch all backends that support numeric mode."""
        for backend in self._backends:
            if hasattr(backend, "numeric_mode"):
                backend.numeric_mode = enabled
