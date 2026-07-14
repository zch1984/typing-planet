#!/usr/bin/env python3
"""Build TypingPlanet as a single-file Windows executable.

Usage:
    uv run python build_exe.py        # build with uv
    python build_exe.py               # build with system python

Output:
    dist/TypingPlanet.exe             # standalone exe, no other files needed
"""
import subprocess
import sys

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "TypingPlanet",
    "--collect-all", "pygame",
    "--collect-all", "typingplanet",
    "--hidden-import", "pydantic",
    "--hidden-import", "typer",
    "--exclude-module", "tkinter",
    "--exclude-module", "unittest",
    "--noconfirm",
    "--clean",
    "run.py",
]

print("Building single-file exe...")
print("  " + " ".join(cmd))
print()
subprocess.run(cmd, check=True)
print()
print("Done! Output: dist/TypingPlanet.exe")
