"""Medical respiratory monitor emulator.

Scenarios:
  - stable_patient: Normal vitals with minimal fluctuation.
  - gradual_decline: SpO2 drops ~0.1/min, HR compensates upward, alert after ~5 min.
  - sudden_alert: Random sudden desaturation event.
"""

import time
from typing import Any

from devices.base import BaseDevice
from generators.realistic_data import AlertInjector, SignalGenerator


class MedicalMonitor(BaseDevice):

    def _setup_generators(self) -> None:
        p = self.params
        spo2_base = p.get("spo2_base", 97)
        hr_base = p.get("heart_rate_base", 72)
        rr_base = p.get("resp_rate_base", 16)
        temp_base = p.get("temp_c_base", 36.8)

        if self.scenario == "gradual_decline":
            spo2_drift = -0.1 / 60  # -0.1 per minute
            hr_drift = 0.15 / 60
        else:
            spo2_drift = 0.0
            hr_drift = 0.0

        self.spo2 = SignalGenerator(
            base=spo2_base, noise_std=0.3, min_val=70, max_val=100,
            drift_per_sec=spo2_drift, decimals=0,
        )
        self.heart_rate = SignalGenerator(
            base=hr_base, noise_std=1.5, min_val=30, max_val=220,
            drift_per_sec=hr_drift, decimals=0,
        )
        self.resp_rate = SignalGenerator(
            base=rr_base, noise_std=0.5, min_val=5, max_val=40, decimals=0,
        )
        self.temp = SignalGenerator(
            base=temp_base, noise_std=0.05, min_val=35.0, max_val=42.0, decimals=1,
        )

        self._alert_injector = None
        if self.scenario == "sudden_alert":
            self._alert_injector = AlertInjector(
                probability_per_tick=0.003,  # ~once every ~5 min at 1 tick/sec
            )
        elif self.scenario == "gradual_decline":
            self._alert_injector = AlertInjector(scheduled_after_sec=300)

        self._in_alert = False
        self._alert_start: float | None = None

    def generate_data(self) -> dict[str, Any]:
        # Check alert trigger
        if self._alert_injector and not self._in_alert:
            if self._alert_injector.should_trigger():
                self._in_alert = True
                self._alert_start = time.monotonic()
                self.spo2.set_drift(-2.0)  # rapid drop
                self.heart_rate.set_drift(3.0)  # tachycardia compensation

        # Alert lasts ~30 seconds then stabilizes
        if self._in_alert and self._alert_start:
            if time.monotonic() - self._alert_start > 30:
                self._in_alert = False
                self.spo2.set_drift(0.5)  # slow recovery
                self.heart_rate.set_drift(-0.5)

        spo2_val = self.spo2.sample()
        hr_val = self.heart_rate.sample()

        alerts = []
        if spo2_val < 90:
            alerts.append("LOW_SPO2")
        if hr_val > 120:
            alerts.append("TACHYCARDIA")
        if hr_val < 50:
            alerts.append("BRADYCARDIA")

        status = "critical" if alerts else "stable"

        return {
            "ts": int(time.time()),
            "spo2": int(spo2_val),
            "heart_rate": int(hr_val),
            "resp_rate": int(self.resp_rate.sample()),
            "temp_c": self.temp.sample(),
            "alerts": alerts,
            "status": status,
        }

    def get_icon(self) -> str:
        return "lungs"

    def get_schema(self) -> dict[str, Any]:
        return {
            "spo2": {"unit": "%", "range": [0, 100], "alert_below": 90},
            "heart_rate": {"unit": "bpm", "range": [30, 220], "alert_above": 120},
            "resp_rate": {"unit": "rpm", "range": [5, 40]},
            "temp_c": {"unit": "\u00b0C", "range": [35, 42]},
        }
