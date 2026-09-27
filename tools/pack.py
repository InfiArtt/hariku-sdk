#!/usr/bin/env python3
# Hariku Developer SDK: check an extension, then pack it with the official packager.
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""
pack.py: check an extension folder with check_extension.py, then pack it
into a .hrk with Hariku's own packager (tools/packager.py).

    python tools/pack.py my_extension              ->  dist/my_extension.hrk
    python tools/pack.py my_extension --output out ->  out/my_extension.hrk
    python tools/pack.py --all                     every top-level extension folder
                                                   of this repository, except
                                                   template_extension/ and examples/
    python tools/pack.py my_extension --no-check   skip the check

An extension with errors isn't packed. The packager runs as a separate
program, exactly as `python tools/packager.py <folder> --output <dir>`.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_extension  # noqa: E402  (the checker next to this file)

PACKAGER = os.path.join(HERE, "packager.py")
# The untouched template: rename (copy) it to your extension's id first.
NOT_PACKED_BY_ALL = {"template_extension"}


def top_level_extensions(root="."):
    """The folders --all packs: top-level folders with a manifest.json,
    without the template (examples/ isn't looked in)."""
    found = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if (name.startswith(".") or name in NOT_PACKED_BY_ALL or not os.path.isdir(path)
                or not os.path.isfile(os.path.join(path, "manifest.json"))):
            continue
        found.append((os.path.relpath(path) if root == "." else path).replace(os.sep, "/"))
    return found


def pack(folder, output, check=True):
    """Check and pack one folder; True when the .hrk was written."""
    if check:
        report = check_extension.check_folder(folder)
        for problem in report.problems:
            print(f"  {problem}")
        if report.errors:
            print(f"Not packing {folder}: fix the {len(report.errors)} error(s) first.")
            return False
    # UTF-8 output, so a name in any script prints on any console.
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run([sys.executable, PACKAGER, folder, "--output", output], env=env)
    return result.returncode == 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check and pack Hariku extensions into .hrk files.")
    parser.add_argument("folders", nargs="*", help="extension folders to pack")
    parser.add_argument("--all", action="store_true",
                        help="pack every top-level extension folder (not template_extension/ "
                             "or examples/)")
    parser.add_argument("--output", "-o", default="dist",
                        help="where to write the .hrk files (default: dist)")
    parser.add_argument("--no-check", action="store_true", help="don't run check_extension.py")
    args = parser.parse_args(argv)

    folders = list(args.folders)
    if args.all:
        found = top_level_extensions()
        if "template_extension" in os.listdir(".") and not found:
            print("Only template_extension/ is here: copy it to a folder named after your "
                  "extension's id, and pack that.")
        folders += [f for f in found if f not in folders]
    if not folders:
        if args.all:
            print("No extension folders to pack.")
            return 0
        parser.error("name an extension folder, or use --all")

    os.makedirs(args.output, exist_ok=True)
    failed = [f for f in folders if not pack(f, args.output, check=not args.no_check)]
    if failed:
        print(f"Couldn't pack: {', '.join(failed)}")
        return 1
    print(f"Packed {len(folders)} extension(s) into {args.output}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
