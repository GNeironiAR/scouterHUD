# Contributing to ScouterHUD

Thanks for your interest in ScouterHUD! Whether you're reporting a bug, proposing a feature, or submitting code — you're helping build open-source AR for everyone.

## Quick start

For the full contribution guide — interfaces, high-impact areas, architecture, and design principles — see **[Community Guide](docs/community-guide.md)**.

## How to report a bug

1. Open an [issue](https://github.com/GNeironiAR/scouterHUD/issues) with a clear title
2. Describe what happened vs. what you expected
3. Include steps to reproduce, logs, and your environment (OS, Python version, Flutter version)

## How to propose a feature

1. Open an [issue](https://github.com/GNeironiAR/scouterHUD/issues) with the `feature` label
2. Describe the use case — *who* needs it and *why*
3. If possible, reference which [interface](docs/community-guide.md#the-interfaces) it connects to (QR-Link, MQTT, layout, panel, bridge, frame)

## How to submit a pull request

1. Fork the repo and create a feature branch
2. Make sure tests pass:
   ```bash
   # Python tests (179 tests)
   cd software && PYTHONPATH=. ../.venv/bin/python -m pytest tests/ -q

   # Flutter tests (32 tests)
   cd app/flutter/scouter_app && ~/flutter/bin/flutter test
   ```
3. Open a PR against `main` with a clear description of what changed and why

## Hard rules

These are non-negotiable — contributions that violate them will not be accepted:

- **No camera on the base HUD** — privacy by design, not a feature
- **No cloud dependencies for core functionality** — the HUD works fully offline
- **No cloud for health/personal data** — AI inference and data processing stay on-device
- **Open source everything** — Software: MIT, Hardware: CERN-OHL-S v2

## Code of Conduct

Be respectful, be constructive, be welcoming. We're building something for nurses, mechanics, engineers, and makers around the world. Treat every contributor the way you'd want to be treated in an open workshop.

---

*See [Community Guide](docs/community-guide.md) for the full picture — where to plug in, what has the most impact, and how the ecosystem works.*
