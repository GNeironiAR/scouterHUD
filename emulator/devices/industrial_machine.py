"""Industrial pressure gauge / machine emulator.

Scenarios:
  - production_cycle: Repeating pressure cycles with variation.
"""

import time
from typing import Any

from devices.base import BaseDevice
from generators.realistic_data import CorrelatedSignal, CycleGenerator, SignalGenerator


class IndustrialMachine(BaseDevice):

    def _setup_generators(self) -> None:
        p = self.params
        pressure_base = p.get("pressure_bar_base", 150)
        temp_base = p.get("temp_c_base", 45)
        cycle_time = p.get("cycle_time_sec", 12)

        self.pressure = CycleGenerator(
            base=pressure_base, amplitude=pressure_base * 0.3,
            cycle_seconds=cycle_time, noise_std=2,
            min_val=0, max_val=pressure_base * 2, decimals=1,
        )
        self.temp = CorrelatedSignal(
            base=temp_base, noise_std=0.3, min_val=20, max_val=120,
            source_base=pressure_base, scale=0.05, lag_seconds=5, decimals=1,
        )
        self._cycle_counter = SignalGenerator(
            base=0, noise_std=0, min_val=0, max_val=999999, decimals=0,
        )
        self._cycles = 0
        self._cycle_time = cycle_time
        self._last_cycle = time.monotonic()

    def generate_data(self) -> dict[str, Any]:
        now = time.monotonic()
        if now - self._last_cycle >= self._cycle_time:
            self._cycles += 1
            self._last_cycle = now

        pressure_val = self.pressure.sample()
        temp_val = self.temp.sample(pressure_val)

        if pressure_val > self.params.get("pressure_bar_base", 150) * 1.4:
            status = "warning"
        elif pressure_val < 10:
            status = "idle"
        else:
            status = "running"

        return {
            "ts": int(time.time()),
            "pressure_bar": pressure_val,
            "temp_c": temp_val,
            "cycle_count": self._cycles,
            "status": status,
        }

    def get_icon(self) -> str:
        return "gauge"

    def get_schema(self) -> dict[str, Any]:
        return {
            "pressure_bar": {
                "unit": "bar",
                "range": [0, self.params.get("pressure_bar_base", 150) * 2],
                "alert_above": self.params.get("pressure_bar_base", 150) * 1.4,
            },
            "temp_c": {"unit": "\u00b0C", "range": [20, 120], "alert_above": 90},
            "cycle_count": {"unit": "", "range": [0, 999999]},
            "status": {"unit": "", "values": ["running", "idle", "warning", "error"]},
        }
