#!/usr/bin/env python3
import argparse
import shutil
import time
from pathlib import Path


def unique_trash_target(trash: Path, path: Path) -> Path:
    target = trash / path.name
    if target.exists():
        target = trash / f"{path.stem}.{time.strftime('%Y%m%d-%H%M%S')}{path.suffix}"
    return target


def main():
    parser = argparse.ArgumentParser(description="Move intermediate video files to macOS Trash after final outputs are verified.")
    parser.add_argument("--keep", action="append", default=[], help="Path to preserve. Must exist and be non-empty when --require-keep is true.")
    parser.add_argument("--candidates", nargs="*", default=[], help="Intermediate paths to move to Trash.")
    parser.add_argument("--require-keep", action="store_true", default=True)
    args = parser.parse_args()

    keep = {Path(p).expanduser().resolve() for p in args.keep}
    if args.require_keep:
        for path in keep:
            if not path.exists() or (path.is_file() and path.stat().st_size == 0):
                raise SystemExit(f"Required keep path missing or empty: {path}")

    trash = Path.home() / ".Trash"
    trash.mkdir(exist_ok=True)
    moved = []
    missing = []

    for raw in args.candidates:
        path = Path(raw).expanduser().resolve()
        if path in keep:
            continue
        if not path.exists():
            missing.append(path)
            continue
        target = unique_trash_target(trash, path)
        shutil.move(str(path), str(target))
        moved.append((path, target))

    print("KEEP")
    for path in sorted(keep):
        if path.exists():
            print(path)
    print("MOVED")
    for src, dst in moved:
        print(f"{src} -> {dst}")
    if missing:
        print("MISSING")
        for path in missing:
            print(path)


if __name__ == "__main__":
    main()
