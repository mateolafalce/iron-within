#!/usr/bin/env python3
"""Build the Cinnamon Spices tree for iron-within-panel@mateo.

The development checkout keeps one copy of the engine at the repo root.
This script writes a self-contained applet for linuxmint/cinnamon-spices-applets.
Symlinks are copied as real files.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

UUID = "iron-within-panel@mateo"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def png_size(path):
    data = path.read_bytes()
    if data[:8] != PNG_MAGIC or data[12:16] != b"IHDR":
        raise SystemExit("%s is not a png" % path)
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def _copy(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


def pack(repo, spice_dir, screenshot=None):
    repo = Path(repo)
    spice_dir = Path(spice_dir)
    if spice_dir.name != UUID:
        raise SystemExit("spice directory must be named %s" % UUID)
    allowed = spice_dir.resolve() == (repo / "dist" / UUID).resolve()
    if not allowed and not str(spice_dir.resolve()).startswith(tempfile.gettempdir()):
        raise SystemExit("refusing to write outside dist/ or the temp dir: %s" % spice_dir)
    shot = Path(screenshot) if screenshot else repo / "packaging" / "mint" / "screenshot.png"
    if not shot.is_file():
        raise SystemExit("missing screenshot: %s" % shot)

    applet = spice_dir / "files" / UUID
    if spice_dir.exists():
        shutil.rmtree(spice_dir)
    applet.mkdir(parents=True)

    _copy(repo / "packaging" / "mint" / "info.json", spice_dir / "info.json")
    _copy(repo / "packaging" / "mint" / "README.md", spice_dir / "README.md")
    _copy(shot, spice_dir / "screenshot.png")
    for name in ("metadata.json", "applet.js", "settings-schema.json", "icon.png", "icon-active.png"):
        _copy(repo / "panel" / name, applet / name)
    for name in ("gradeEngine.js", "gradeLogic.js", "presets.json", "LICENSE"):
        _copy(repo / name, applet / name)
    for name in ("grade.glsl", "sharpen.glsl"):
        _copy(repo / "shaders" / name, applet / "shaders" / name)

    check(spice_dir)
    return spice_dir


def check(spice_dir):
    spice_dir = Path(spice_dir)
    uuid = spice_dir.name
    required = [
        spice_dir / "info.json",
        spice_dir / "screenshot.png",
        spice_dir / "README.md",
        spice_dir / "files" / uuid / "metadata.json",
        spice_dir / "files" / uuid / "applet.js",
        spice_dir / "files" / uuid / "icon.png",
        spice_dir / "files" / uuid / "icon-active.png",
        spice_dir / "files" / uuid / "settings-schema.json",
        spice_dir / "files" / uuid / "gradeEngine.js",
        spice_dir / "files" / uuid / "gradeLogic.js",
        spice_dir / "files" / uuid / "presets.json",
        spice_dir / "files" / uuid / "shaders" / "grade.glsl",
        spice_dir / "files" / uuid / "shaders" / "sharpen.glsl",
        spice_dir / "files" / uuid / "LICENSE",
    ]
    for path in required:
        if not path.is_file():
            raise SystemExit("missing %s" % path)
        if path.is_symlink():
            raise SystemExit("symlink in the spice tree: %s" % path)
    files_dir = spice_dir / "files"
    names = sorted(p.name for p in files_dir.iterdir())
    if names != [uuid]:
        raise SystemExit("files/ must contain only %s" % uuid)
    info = json.loads((spice_dir / "info.json").read_text())
    author = info.get("author", "")
    if not author or any(ch.isspace() for ch in author):
        raise SystemExit("info.json author is missing or has whitespace")
    meta_path = spice_dir / "files" / uuid / "metadata.json"
    raw = meta_path.read_bytes()
    raw.decode("ascii")
    metadata = json.loads(raw.decode("ascii"))
    for field in ("icon", "dangerous", "last-edited"):
        if field in metadata:
            raise SystemExit("forbidden metadata field %s" % field)
    for field in ("uuid", "name", "description"):
        if field not in metadata:
            raise SystemExit("metadata missing %s" % field)
    if metadata["uuid"] != uuid:
        raise SystemExit("metadata uuid does not match the directory")
    width, height = png_size(spice_dir / "files" / uuid / "icon.png")
    if width != height or width < 16:
        raise SystemExit("icon.png must be a square of at least 16px")
    active_w, active_h = png_size(spice_dir / "files" / uuid / "icon-active.png")
    if (active_w, active_h) != (width, height):
        raise SystemExit("icon-active.png size does not match icon.png")


def main(argv):
    repo = Path(__file__).resolve().parents[1]
    dest = pack(repo, repo / "dist" / UUID)
    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
