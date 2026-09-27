# Hariku Developer SDK tests.
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""The sync script (.github/scripts/sdk_sync.py) and tools/pack.py."""

import os
import zipfile

import pytest

import pack
import sdk_sync
from conftest import ROOT

TAG_SHA = "a" * 40
MAIN_SHA = "b" * 40
RELEASE = "https://github.com/InfiArtt/hariku/releases/tag/v2.10.0"


# ------------------------------------------------------------
# The latest release
# ------------------------------------------------------------

def fake_github(responses):
    return lambda path: responses.get(path)


def test_the_release_in_the_distribution_repository():
    get = fake_github({
        "/repos/InfiArtt/hariku/releases/latest": {"tag_name": "v2.10.0", "html_url": RELEASE},
        "/repos/InfiArtt/hariku-core/git/ref/tags/v2.10.0": {"ref": "refs/tags/v2.10.0"},
    })
    assert sdk_sync.latest_release(get) == ("v2.10.0", RELEASE)


def test_a_release_in_hariku_core_comes_first():
    url = "https://github.com/InfiArtt/hariku-core/releases/tag/v2.11.0"
    get = fake_github({
        "/repos/InfiArtt/hariku-core/releases/latest": {"tag_name": "v2.11.0", "html_url": url},
        "/repos/InfiArtt/hariku/releases/latest": {"tag_name": "v2.10.0"},
        "/repos/InfiArtt/hariku-core/git/ref/tags/v2.11.0": {"ref": "refs/tags/v2.11.0"},
    })
    assert sdk_sync.latest_release(get) == ("v2.11.0", url)


@pytest.mark.parametrize("responses, text", [
    ({}, "has a release"),
    ({"/repos/InfiArtt/hariku/releases/latest": {"tag_name": "v2.10.0"}}, "no such tag"),
    ({"/repos/InfiArtt/hariku/releases/latest": {"tag_name": "2.10.0; rm -rf /"}}, "not vX.Y.Z"),
])
def test_no_usable_release(responses, text):
    with pytest.raises(sdk_sync.SyncError, match=text):
        sdk_sync.latest_release(fake_github(responses))


# ------------------------------------------------------------
# Copying
# ------------------------------------------------------------

MIT_LICENSE = "MIT License\n\nCopyright (c) 2026 Someone\n"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


@pytest.fixture
def core(tmp_path):
    tag = tmp_path / "core-tag"
    main = tmp_path / "core-main"
    write(str(tag / "DEVELOPERS.md"), "# Guide\n")
    write(str(tag / "tools" / "packager.py"), "# SPDX-License-Identifier: GPL-3.0-or-later\n")
    write(str(tag / ".vscode" / "settings.json"), "{}\n")
    # The store's policies at the release tag are older than main's...
    write(str(tag / "docs" / "en" / "extension_store" / "submission_guide.txt"), "old policy\n")
    # ...and the SDK takes main's.
    store = main / "docs" / "en" / "extension_store"
    for name in ("submission_guide.txt", "review_guidelines.txt", "security_policy.txt"):
        write(str(store / name), f"main's {name}\n")
    write(str(main / "template_extension" / "LICENSE"), MIT_LICENSE)
    write(str(main / "template_extension" / "main.py"), "# SPDX-License-Identifier: MIT\n")
    write(str(main / "template_extension" / "manifest.json"), "{}\n")
    dest = tmp_path / "sdk"
    write(str(dest / "store_guidelines" / "old_file.txt"), "gone upstream\n")
    write(str(dest / "tools" / "check_extension.py"), "# ours\n")
    return str(tag), str(main), str(dest)


def test_copy_all(core):
    tag, main, dest = core
    sdk_sync.copy_all("v2.10.0", tag, TAG_SHA, main, MAIN_SHA, RELEASE, dest)
    listed = sorted(os.listdir(os.path.join(dest, "store_guidelines")))
    assert listed == ["security_policy.txt", "submission_guide.txt"]    # no review_guidelines
    for rel in ("DEVELOPERS.md", "tools/packager.py", ".vscode/settings.json",
                "template_extension/LICENSE", "template_extension/main.py", "SYNCED_FROM.md",
                "tools/check_extension.py"):
        assert os.path.isfile(os.path.join(dest, rel)), rel
    with open(os.path.join(dest, "SYNCED_FROM.md"), encoding="utf-8") as f:
        synced = f.read()
    assert "v2.10.0" in synced and TAG_SHA in synced and MAIN_SHA in synced and RELEASE in synced


def test_store_guidelines_come_from_main(core):
    tag, main, dest = core
    sdk_sync.copy_all("v2.10.0", tag, TAG_SHA, main, MAIN_SHA, RELEASE, dest)
    with open(os.path.join(dest, "store_guidelines", "submission_guide.txt"),
              encoding="utf-8") as f:
        assert f.read() == "main's submission_guide.txt\n"
    with open(os.path.join(dest, "SYNCED_FROM.md"), encoding="utf-8") as f:
        synced = f.read()
    from_main = synced.split("## From main", 1)[1]
    assert "`store_guidelines/`" in from_main and "`template_extension/`" in from_main
    assert "`store_guidelines/`" not in synced.split("## From main", 1)[0]


def test_the_sync_lists():
    tag_sources = [src for src, _dst in sdk_sync.FROM_TAG]
    main_sources = [src for src, _dst in sdk_sync.FROM_MAIN]
    assert tag_sources == ["DEVELOPERS.md", "tools/packager.py", ".vscode"]
    assert main_sources == ["template_extension", "docs/en/extension_store"]
    assert "review_guidelines.txt" in sdk_sync.EXCLUDED_FILES


def test_synced_from_is_the_same_each_time(core):
    tag, main, dest = core
    texts = []
    for _ in range(2):
        sdk_sync.copy_all("v2.10.0", tag, TAG_SHA, main, MAIN_SHA, RELEASE, dest)
        with open(os.path.join(dest, "SYNCED_FROM.md"), encoding="utf-8") as f:
            texts.append(f.read())
    assert texts[0] == texts[1]


def test_a_template_that_isnt_mit_is_refused(core):
    tag, main, dest = core
    write(os.path.join(main, "template_extension", "main.py"),
          "# SPDX-License-Identifier: GPL-3.0-or-later\n")
    with pytest.raises(sdk_sync.SyncError, match="MIT"):
        sdk_sync.copy_all("v2.10.0", tag, TAG_SHA, main, MAIN_SHA, RELEASE, dest)
    assert not os.path.exists(os.path.join(dest, "DEVELOPERS.md"))


@pytest.mark.parametrize("tag, tag_sha", [("main", TAG_SHA), ("v2.10.0", "abc123")])
def test_bad_refs_are_refused(core, tag, tag_sha):
    tag_dir, main, dest = core
    with pytest.raises(sdk_sync.SyncError):
        sdk_sync.copy_all(tag, tag_dir, tag_sha, main, MAIN_SHA, RELEASE, dest)


# ------------------------------------------------------------
# The ZIP and the release notes
# ------------------------------------------------------------

def test_the_sdk_zip(tmp_path):
    out = str(tmp_path / sdk_sync.ZIP_NAME)
    old = os.getcwd()
    os.chdir(ROOT)
    try:
        sdk_sync.build_zip(out)
    finally:
        os.chdir(old)
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    for expected in ("README.md", "LICENSE", "NOTICE.md", "DEVELOPERS.md",
                     "template_extension/manifest.json", "examples/hello_hotkey/main.py",
                     "tools/check_extension.py", "tools/packager.py", "tools/pack.py",
                     "store_guidelines/submission_guide.txt", ".vscode/settings.json"):
        assert expected in names, expected
    assert not [n for n in names if "review_guidelines" in n or "__pycache__" in n
                or n.endswith((".pyc", ".hrk")) or n.startswith((".github/", "tests/"))]


def test_release_notes():
    notes = sdk_sync.release_notes("v2.10.0", RELEASE, TAG_SHA, MAIN_SHA)
    assert "Hariku 2.10.0" in notes and RELEASE in notes and TAG_SHA[:7] in notes
    assert sdk_sync.ZIP_NAME in notes
    assert "store guidelines come from hariku-core main" in notes


# ------------------------------------------------------------
# tools/pack.py
# ------------------------------------------------------------

def test_pack_all_leaves_out_the_template_and_the_examples(tmp_path, make_ext, monkeypatch):
    make_ext(name="my_tool")
    make_ext(name="template_extension")
    (tmp_path / "examples").mkdir()
    monkeypatch.chdir(tmp_path)
    assert pack.top_level_extensions() == ["my_tool"]


def test_pack_makes_a_hrk(tmp_path, make_ext):
    folder = make_ext()
    out = tmp_path / "dist"
    assert pack.main([folder, "--output", str(out)]) == 0
    with zipfile.ZipFile(out / "my_tool.hrk") as zf:
        names = set(zf.namelist())
    assert {"manifest.json", "main.py", "docs/en/guide.md", "locales/en.json"} <= names


def test_pack_refuses_an_extension_with_errors(tmp_path, make_ext):
    folder = make_ext({"main.py": "def (\n"})
    out = tmp_path / "dist"
    assert pack.main([folder, "--output", str(out)]) == 1
    assert not (out / "my_tool.hrk").exists()
