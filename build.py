from __future__ import annotations

import shutil
from pathlib import Path

import PyInstaller.__main__


ROOT = Path(__file__).parent
ENTRY = ROOT / "src" / "mzrds" / "cli.py"


def clean_build_dirs():
    for folder in ("build", "__pycache__"):
        target = ROOT / folder
        if target.exists():
            shutil.rmtree(target)


def build():
    clean_build_dirs()
    PyInstaller.__main__.run(
        [
            "--onefile",
            "--name",
            "mzrds",
            "--console",
            "--clean",
            "--paths",
            str(ROOT / "src"),
            str(ENTRY),
        ]
    )


if __name__ == "__main__":
    build()

