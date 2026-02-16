"""Server / cloud infrastructure emulator.

Scenarios:
  - normal_load: CPU 20-40%, stable memory.
  - spike: CPU spikes to 95% for ~2 min, then drops.
  - cost_alert: Monthly cost gradually exceeds threshold.
"""

import time
from typing import Any

from devices.base import BaseDevice
from generators.realistic_data import AlertInjector, SignalGenerator


class ServerInfra(BaseDevice):

    def _setup_generators(self) -> None:
        p = self.params
        cost_base = p.get("monthly_cost_base", 234.56)
        self._instance_type = p.get("instance_type", "t3.large")
        self._instance_id = p.get("instance_id", f"i-{self.id[:8]}")

        if self.scenario == "spike":
            cpu_base = 30.0
        else:
            cpu_base = 30.0

        self.cpu = SignalGenerator(
            base=cpu_base, noise_std=5, min_val=1, max_val=100, decimals=1,
        )
        self.mem = SignalGenerator(
            base=65, noise_std=2, min_val=20, max_val=99, decimals=1,
        )
        self.disk = SignalGenerator(
            base=45, noise_std=0.2, min_val=10, max_val=99,
            drift_per_sec=0.001, decimals=1,
        )
        self.cost = SignalGenerator(
            base=cost_base, noise_std=0,  min_val=0, max_val=99999,
            drift_per_sec=0.02 if self.scenario == "cost_alert" else 0.0,
            decimals=2,
        )

        self._spike_injector = None
        self._in_spike = False
        self._spike_start: float | None = None

        if self.scenario == "spike":
            self._spike_injector = AlertInjector(scheduled_after_sec=30)

    def generate_data(self) -> dict[str, Any]:
        # Handle CPU spike
        if self._spike_injector and not self._in_spike:
            if self._spike_injector.should_trigger():
                self._in_spike = True
                self._spike_start = time.monotonic()
                self.cpu.reset(92)
                self.cpu = SignalGenerator(
                    base=92, noise_std=3, min_val=80, max_val=100, decimals=1,
                )

        if self._in_spike and self._spike_start:
            if time.monotonic() - self._spike_start > 120:  # 2 min spike
                self._in_spike = False
                self.cpu = SignalGenerator(
                    base=30, noise_std=5, min_val=1, max_val=100, decimals=1,
                )

        cpu_val = self.cpu.sample()
        cost_val = self.cost.sample()

        active_alerts = 0
        if cpu_val > 90:
            active_alerts += 1
        if cost_val > self.params.get("monthly_cost_base", 234.56) * 1.2:
            active_alerts += 1

        return {
            "ts": int(time.time()),
            "cpu_pct": cpu_val,
            "mem_pct": self.mem.sample(),
            "disk_pct": self.disk.sample(),
            "monthly_cost_usd": cost_val,
            "active_alerts": active_alerts,
            "instance_id": self._instance_id,
        }

    def get_icon(self) -> str:
        return "server"

    def get_schema(self) -> dict[str, Any]:
        return {
            "cpu_pct": {"unit": "%", "range": [0, 100], "alert_above": 90},
            "mem_pct": {"unit": "%", "range": [0, 100], "alert_above": 90},
            "disk_pct": {"unit": "%", "range": [0, 100], "alert_above": 85},
            "monthly_cost_usd": {"unit": "USD", "range": [0, 99999]},
            "active_alerts": {"unit": "", "range": [0, 100]},
        }
