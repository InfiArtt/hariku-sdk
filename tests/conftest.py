# Hariku Developer SDK tests.
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""The SDK's tools and scripts, importable from the tests, and a factory for
extension folders."""

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))

GOOD_MANIFEST = {
    "name": "My Tool",
    "version": "1.0.0",
    "author": "Someone",
    "description": "Says something useful when you press a key.",
    "main": "main.py",
    "language": "en",
    "minimum_core_version": "2.9",
}

GOOD_MAIN = '''\
import core.hotkeys
from core.speech import speak


def hello():
    speak("Hello")


def register(bus):
    core.hotkeys.register_action("My Tool", "hello", "Say hello", None, False, hello)


def teardown():
    pass
'''

GOOD_GUIDE = "# My Tool\n\nMy Tool says hello.\n\n## Keys\n\n- Shift+H: hello\n"


def locale(code, messages, **manifest):
    head = {"language_name": code, "language_code": code, "translator": "Someone",
            "email": "someone@example.com", "version": "1.0"}
    head.update(manifest)
    return {"manifest": head, "messages": messages}


@pytest.fixture
def make_ext(tmp_path):
    """make_ext(files, name="my_tool") -> the folder of a good extension, with
    `files` ({relative path: text, dict (JSON) or None to leave out}) on top."""

    def make(files=None, name="my_tool"):
        folder = tmp_path / name
        folder.mkdir()
        content = {
            "manifest.json": GOOD_MANIFEST,
            "main.py": GOOD_MAIN,
            "docs/en/guide.md": GOOD_GUIDE,
            "locales/en.json": locale("en", {"hello": "Hello, {name}!"}),
            "locales/id.json": locale("id", {"hello": "Halo, {name}!"}),
        }
        content.update(files or {})
        for rel, value in content.items():
            if value is None:
                continue
            path = folder / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(value, bytes):
                path.write_bytes(value)
            elif isinstance(value, str):
                path.write_text(value, encoding="utf-8")
            else:
                path.write_text(json.dumps(value, indent=4), encoding="utf-8")
        return str(folder)

    return make
