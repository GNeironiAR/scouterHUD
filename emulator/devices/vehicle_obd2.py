"""Vehicle OBD-II emulator.

Scenarios:
  - city_driving: Variable RPM 1000-3000, speed 0-60, occasional stops.
  - highway: Steady RPM ~2500, speed 100-120.
  - idle: Engine idling, RPM ~800, speed 0.
  - overheating: Coolant temp climbs gradually, triggers DTC.
"""

import time
from typing import Any

from devices.base import BaseDevice
from generators.realistic_data import (
    AlertInjector,
    CorrelatedSignal,
    CycleGenerator,
    DrainingSignal,
    SignalGenerator,
)


class VehicleOBD2(BaseDevice):

    def _setup_generators(self) -> None:
        p = self.params
        rpm_base = p.get("rpm_base", 2000)
        speed_base = p.get("speed_base", 40)
        coolant_base = p.get("coolant_temp_base", 88)
        fuel_start = p.get("fuel_pct_start", 65)

        if self.scenario == "city_driving":
            self.rpm = CycleGenerator(
                base=rpm_base, amplitude=800, cycle_seconds=20,
                noise_std=100, min_val=700, max_val=4500, decimals=0,
            )
            self.speed = CycleGenerator(
                base=speed_base, amplitude=25, cycle_seconds=25,
                noise_std=3, min_val=0, max_val=80, decimals=0,
            )
        elif self.scenario == "highway":
            self.rpm = SignalGenerator(
                base=2500, noise_std=80, min_val=2000, max_val=3200, decimals=0,
            )
            self.speed = SignalGenerator(
                base=110, noise_std=3, min_val=90, max_val=130, decimals=0,
            )
        elif self.scenario == "idle":
            self.rpm = SignalGenerator(
                base=800, noise_std=20, min_val=650, max_val=950, decimals=0,
            )
            self.speed = SignalGenerator(
                base=0, noise_std=0, min_val=0, max_val=0, decimals=0,
            )
        else:  # overheating or default
            self.rpm = SignalGenerator(
                base=rpm_base, noise_std=150, min_val=700, max_val=4500, decimals=0,
            )
            self.speed = SignalGenerator(
                base=speed_base, noise_std=5, min_val=0, max_val=120, decimals=0,
            )

        coolant_drift = 0.05 if self.scenario == "overheating" else 0.0
        self.coolant_temp = CorrelatedSignal(
            base=coolant_base, noise_std=0.5, min_val=60, max_val=130,
            source_base=rpm_base, scale=0.005, lag_seconds=8, decimals=1,
        )
        self._coolant_drift = coolant_drift
        self._coolant_extra = 0.0

        self.fuel = DrainingSignal(
            start_value=fuel_start, drain_per_sec=0.01,
            noise_std=0.05, min_val=0, max_val=100, decimals=1,
        )
        self.battery = SignalGenerator(
            base=14.1, noise_std=0.1, min_val=11.5, max_val=14.8, decimals=1,
        )

        self._alert_injector = None
        if self.scenario == "overheating":
            self._alert_injector = AlertInjector(scheduled_after_sec=120)
        self._dtc_codes: list[str] = []

    def generate_data(self) -> dict[str, Any]:
        rpm_val = self.rpm.sample()
        speed_val = self.speed.sample()

        # Coolant follows RPM + optional overheat drift
        if self.scenario == "overheating":
            self._coolant_extra += self._coolant_drift
        coolant_val = self.coolant_temp.sample(rpm_val) + self._coolant_extra

        if self._alert_injector and self._alert_injector.should_trigger():
            self._dtc_codes = ["P0217"]  # Engine overtemp

        if coolant_val > 110 and "P0217" not in self._dtc_codes:
            self._dtc_codes.append("P0217")

        return {
            "ts": int(time.time()),
            "rpm": int(rpm_val),
            "speed_kmh": int(speed_val),
            "coolant_temp_c": round(min(coolant_val, 130), 1),
            "fuel_pct": self.fuel.sample(),
            "battery_v": self.battery.sample(),
            "dtc_codes": list(self._dtc_codes),
        }

    def get_icon(self) -> str:
        return "car"

    def get_schema(self) -> dict[str, Any]:
        return {
            "rpm": {"unit": "RPM", "range": [0, 8000], "alert_above": 6000},
            "speed_kmh": {"unit": "km/h", "range": [0, 250]},
            "coolant_temp_c": {"unit": "\u00b0C", "range": [60, 130], "alert_above": 110},
            "fuel_pct": {"unit": "%", "range": [0, 100], "alert_below": 10},
            "battery_v": {"unit": "V", "range": [11, 15], "alert_below": 12},
        }
