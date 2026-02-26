#!/usr/bin/env python3
"""Convenience launcher for ScouterHUD.

Equivalent to `python -m scouterhud.main` but avoids -m runner issues
on some Python versions (e.g. Python 3.13 on Pi Zero 2W).
"""
from scouterhud.main import main

main()
