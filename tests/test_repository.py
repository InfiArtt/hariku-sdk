# Hariku Developer SDK tests.
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""What this public repository must and must not contain."""

import json
import os
import re

import pytest

from conftest import ROOT

# Never in the SDK: the store's internal review guidelines, and personal
# files that live next to Hariku's source.
FORBIDDEN_NAMES = {"review_guidelines.txt", "how-to.txt", "news.txt", "body.html",
                   "hariku_v2_journey.md", "signpath-application.txt"}
FORBIDDEN_PATTERNS = [re.compile(r".*_post\.md$")]
SECRET_RE = re.compile(r"(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
                       r"-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16})")
EXAMPLES = ["hello_hotkey", "aruna_command", "preferences_page", "background_task",
            "extension_guide"]
TEXT_SUFFIXES = (".py", ".md", ".txt", ".json", ".yml", ".yaml")


def repository_files():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".pytest_cache")]
        for name in files:
            yield os.path.join(root, name)


def test_nothing_private_or_internal():
    found = [os.path.relpath(p, ROOT) for p in repository_files()
             if os.path.basename(p) in FORBIDDEN_NAMES
             or any(r.match(os.path.basename(p)) for r in FORBIDDEN_PATTERNS)]
    assert found == []


def test_no_secrets():
    found = []
    for path in repository_files():
        if path.endswith(TEXT_SUFFIXES):
            with open(path, encoding="utf-8", errors="replace") as f:
                if SECRET_RE.search(f.read()):
                    found.append(os.path.relpath(path, ROOT))
    assert found == []


@pytest.mark.parametrize("name", EXAMPLES)
def test_every_example_is_mit_and_bilingual(name):
    folder = os.path.join(ROOT, "examples", name)
    with open(os.path.join(folder, "main.py"), encoding="utf-8") as f:
        assert "SPDX-License-Identifier: MIT" in f.read(600)
    for rel in ("locales/en.json", "locales/id.json", "docs/en/guide.md", "docs/id/guide.md"):
        assert os.path.isfile(os.path.join(folder, rel)), rel


def test_minimum_core_versions():
    wanted = {"hello_hotkey": "2.0", "aruna_command": "2.9", "preferences_page": "2.0",
              "background_task": "2.0", "extension_guide": "2.11"}
    for name, version in wanted.items():
        with open(os.path.join(ROOT, "examples", name, "manifest.json"), encoding="utf-8") as f:
            assert json.load(f)["minimum_core_version"] == version, name


def test_the_template_is_mit():
    with open(os.path.join(ROOT, "template_extension", "LICENSE"), encoding="utf-8") as f:
        assert "MIT License" in f.read()


def test_the_readme_has_both_languages():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        text = f.read()
    assert "## Bahasa Indonesia" in text and "## Quick start" in text
    assert "### Mulai cepat" in text
