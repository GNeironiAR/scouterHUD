"""Realistic data generators for virtual devices.

Produces believable sensor values using gaussian noise, temporal drift,
cross-variable correlations, and random alert injection.
"""

import math
import random
import time


class SignalGenerator:
    """Generates a single signal with base value, gaussian noise, and optional drift."""

    def __init__(
        self,
        base: float,
        noise_std: float,
        min_val: float,
        max_val: float,
        drift_per_sec: float = 0.0,
        decimals: int = 1,
    ):
        self.base = base
        self.noise_std = noise_std
        self.min_val = min_val
        self.max_val = max_val
        self.drift_per_sec = drift_per_sec
        self.decimals = decimals
        self._current = base
        self._last_time = time.monotonic()

    def sample(self) -> float:
        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        # Apply drift
        self._current += self.drift_per_sec * dt

        # Add gaussian noise around current value
        value = self._current + random.gauss(0, self.noise_std)

        # Clamp
        value = max(self.min_val, min(self.max_val, value))

        return round(value, self.decimals)

    def reset(self, new_base: float | None = None):
        self._current = new_base if new_base is not None else self.base
        self._last_time = time.monotonic()

    def set_drift(self, drift_per_sec: float):
        self.drift_per_sec = drift_per_sec


class CorrelatedSignal:
    """A signal that follows another signal with a delay and scaling factor.

    Example: coolant temperature follows RPM with a ~5s lag.
    """

    def __init__(
        self,
        base: float,
        noise_std: float,
        min_val: float,
        max_val: float,
        source_base: float,
        scale: float,
        lag_seconds: float = 3.0,
        decimals: int = 1,
    ):
        self.base = base
        self.noise_std = noise_std
        self.min_val = min_val
        self.max_val = max_val
        self.source_base = source_base
        self.scale = scale
        self.lag_seconds = lag_seconds
        self.decimals = decimals
        self._target = base
        self._current = base
        self._last_time = time.monotonic()

    def sample(self, source_value: float) -> float:
        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        # Target based on source deviation from its base
        deviation = source_value - self.source_base
        self._target = self.base + deviation * self.scale

        # Exponential smoothing toward target (simulates thermal lag)
        alpha = 1 - math.exp(-dt / self.lag_seconds) if self.lag_seconds > 0 else 1.0
        self._current += (self._target - self._current) * alpha

        value = self._current + random.gauss(0, self.noise_std)
        value = max(self.min_val, min(self.max_val, value))
        return round(value, self.decimals)


class CycleGenerator:
    """Generates values following a repeating cycle pattern.

    Useful for industrial machines (pressure cycles), daily temperature, etc.
    """

    def __init__(
        self,
        base: float,
        amplitude: float,
        cycle_seconds: float,
        noise_std: float,
        min_val: float,
        max_val: float,
        decimals: int = 1,
    ):
        self.base = base
        self.amplitude = amplitude
        self.cycle_seconds = cycle_seconds
        self.noise_std = noise_std
        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals
        self._start_time = time.monotonic()

    def sample(self) -> float:
        elapsed = time.monotonic() - self._start_time
        phase = (elapsed % self.cycle_seconds) / self.cycle_seconds
        # Sine wave cycle
        value = self.base + self.amplitude * math.sin(2 * math.pi * phase)
        value += random.gauss(0, self.noise_std)
        value = max(self.min_val, min(self.max_val, value))
        return round(value, self.decimals)


class AlertInjector:
    """Injects anomalous events at random or scheduled times."""

    def __init__(
        self,
        probability_per_tick: float = 0.0,
        scheduled_after_sec: float | None = None,
    ):
        self.probability_per_tick = probability_per_tick
        self.scheduled_after_sec = scheduled_after_sec
        self._start_time = time.monotonic()
        self._triggered = False

    def should_trigger(self) -> bool:
        if self._triggered:
            return False

        elapsed = time.monotonic() - self._start_time

        # Scheduled trigger
        if self.scheduled_after_sec is not None and elapsed >= self.scheduled_after_sec:
            self._triggered = True
            return True

        # Random trigger
        if self.probability_per_tick > 0 and random.random() < self.probability_per_tick:
            self._triggered = True
            return True

        return False

    def reset(self):
        self._triggered = False
        self._start_time = time.monotonic()


class DrainingSignal:
    """A signal that decreases over time (fuel, battery).

    Decreases linearly with noise, can have variable drain rate.
    """

    def __init__(
        self,
        start_value: float,
        drain_per_sec: float,
        noise_std: float,
        min_val: float,
        max_val: float,
        decimals: int = 1,
    ):
        self.noise_std = noise_std
        self.min_val = min_val
        self.max_val = max_val
        self.drain_per_sec = drain_per_sec
        self.decimals = decimals
        self._current = start_value
        self._last_time = time.monotonic()

    def sample(self) -> float:
        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        self._current -= self.drain_per_sec * dt
        value = self._current + random.gauss(0, self.noise_std)
        value = max(self.min_val, min(self.max_val, value))
        return round(value, self.decimals)
