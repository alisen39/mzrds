from __future__ import annotations

import shutil
from pathlib import Path

import PyInstaller.__main__


ROOT = Path(__file__).parent
ENTRY = ROOT / "src" / "mzrds" / "cli.py"


def clean_build_dirs():
    """清理构建目录"""
    for folder in ("build", "dist", "__pycache__"):
        target = ROOT / folder
        if target.exists():
            shutil.rmtree(target)


def build():
    """构建单文件可执行程序"""
    clean_build_dirs()
    # 确保 dist 目录存在
    dist_dir = ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)
    
    PyInstaller.__main__.run(
        [
            "--onefile",
            "--name",
            "mzrds",
            "--console",
            "--clean",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(ROOT / "build"),
            "--paths",
            str(ROOT / "src"),
            str(ENTRY),
        ]
    )


if __name__ == "__main__":
    build()

