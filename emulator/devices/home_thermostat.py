"""Home thermostat / climate sensor emulator.

Scenarios:
  - daily_cycle: Temperature follows a day/night sine curve.
"""

import time
from typing import Any

from devices.base import BaseDevice
from generators.realistic_data import CycleGenerator, SignalGenerator


class HomeThermostat(BaseDevice):

    def _setup_generators(self) -> None:
        p = self.params
        temp_base = p.get("temp_c_base", 22.0)
        humidity_base = p.get("humidity_base", 45)

        if self.scenario == "daily_cycle":
            # 10-min cycle simulates 24h day compressed (for demo)
            self.temp = CycleGenerator(
                base=temp_base, amplitude=3.0, cycle_seconds=600,
                noise_std=0.2, min_val=10, max_val=40, decimals=1,
            )
        else:
            self.temp = SignalGenerator(
                base=temp_base, noise_std=0.3, min_val=10, max_val=40, decimals=1,
            )

        self.humidity = SignalGenerator(
            base=humidity_base, noise_std=1.5, min_val=15, max_val=95, decimals=0,
        )
        self._target_temp = p.get("target_temp_c", temp_base)

    def generate_data(self) -> dict[str, Any]:
        temp_val = self.temp.sample()

        if temp_val < self._target_temp - 1:
            mode = "heating"
        elif temp_val > self._target_temp + 1:
            mode = "cooling"
        else:
            mode = "idle"

        return {
            "ts": int(time.time()),
            "temp_c": temp_val,
            "humidity_pct": int(self.humidity.sample()),
            "target_temp_c": self._target_temp,
            "mode": mode,
        }

    def get_icon(self) -> str:
        return "thermometer"

    def get_schema(self) -> dict[str, Any]:
        return {
            "temp_c": {"unit": "\u00b0C", "range": [10, 40]},
            "humidity_pct": {"unit": "%", "range": [0, 100]},
            "target_temp_c": {"unit": "\u00b0C", "range": [15, 30]},
            "mode": {"unit": "", "values": ["heating", "cooling", "idle"]},
        }
