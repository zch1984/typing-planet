"""Standalone entry point for PyInstaller.

Uses an absolute import so the frozen exe does not hit the
"relative import with no known parent package" error that ``__main__.py``
triggers when PyInstaller runs it as a top-level script.
"""
from typingplanet.cli import app

if __name__ == "__main__":
    app()
