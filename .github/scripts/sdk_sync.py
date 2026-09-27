#!/usr/bin/env python3
# Hariku Developer SDK: keep the SDK in step with Hariku's releases.
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""
sdk_sync.py: what .github/workflows/sync.yml runs. Standard library only.

    sdk_sync.py latest
        Print tag=... and release_url=... (for $GITHUB_OUTPUT): the latest
        Hariku release. Hariku's releases are published in InfiArtt/hariku
        from tags of InfiArtt/hariku-core; a release in hariku-core itself
        is used first, should there ever be one. The tag must exist in
        hariku-core.

    sdk_sync.py copy --tag T --tag-dir D --tag-sha S --main-dir M --main-sha S2 --release-url U
        Copy into the SDK (the current folder, or --dest): from hariku-core at
        the tag DEVELOPERS.md, tools/packager.py and .vscode/; from main,
        template_extension/ (which must be MIT) and docs/en/extension_store/
        as store_guidelines/ (never the internal review_guidelines.txt).
        Write SYNCED_FROM.md.

    sdk_sync.py zip --output PATH
        Build Hariku_V2_Developer_SDK.zip from the SDK.

    sdk_sync.py notes --tag T --release-url U --tag-sha S --main-sha S2
        Print the notes of the SDK release for that Hariku release.
"""

import argparse
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
import zipfile

CORE_REPO = "InfiArtt/hariku-core"
DIST_REPO = "InfiArtt/hariku"           # where Hariku's releases are published
SDK_REPO = "InfiArtt/hariku-sdk"
API = "https://api.github.com"
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# (path in hariku-core, path in the SDK). What describes a Hariku version (the
# API guide, the packager) comes from the latest release; the template and the
# store's policies, which aren't tied to a version, come from main.
FROM_TAG = [
    ("DEVELOPERS.md", "DEVELOPERS.md"),
    ("tools/packager.py", "tools/packager.py"),
    (".vscode", ".vscode"),
]
FROM_MAIN = [
    ("template_extension", "template_extension"),
    ("docs/en/extension_store", "store_guidelines"),
]
# Never in the SDK: the store's internal review guidelines are for reviewers.
EXCLUDED_FILES = {"review_guidelines.txt"}
SKIPPED_DIRS = {"__pycache__", ".git"}
SKIPPED_SUFFIXES = (".pyc", ".pyo", ".hrk")

ZIP_NAME = "Hariku_V2_Developer_SDK.zip"
ZIP_CONTENTS = ["README.md", "LICENSE", "NOTICE.md", "SYNCED_FROM.md", "DEVELOPERS.md",
                "template_extension", "examples", "tools", "store_guidelines", ".vscode"]


class SyncError(Exception):
    pass


# ------------------------------------------------------------
# The latest Hariku release
# ------------------------------------------------------------

def github_json(path, token=None):
    """GET a GitHub API path; the parsed JSON, or None for 404."""
    request = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "hariku-sdk-sync",
    })
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise SyncError(f"GitHub answered {e.code} for {path}") from e


def latest_release(get_json):
    """(tag, release page URL) of the latest Hariku release. get_json(path)
    returns the JSON of a GitHub API path, or None for 404."""
    for repo in (CORE_REPO, DIST_REPO):
        release = get_json(f"/repos/{repo}/releases/latest")
        if not release or not release.get("tag_name"):
            continue
        tag = release["tag_name"]
        if not TAG_RE.match(tag):
            raise SyncError(f"{repo}'s latest release has the tag {tag!r}, not vX.Y.Z")
        if not get_json(f"/repos/{CORE_REPO}/git/ref/tags/{tag}"):
            raise SyncError(f"{repo}'s latest release is {tag}, but {CORE_REPO} has no such tag")
        url = release.get("html_url") or f"https://github.com/{repo}/releases/tag/{tag}"
        return tag, url
    raise SyncError(f"Neither {CORE_REPO} nor {DIST_REPO} has a release")


# ------------------------------------------------------------
# Copying
# ------------------------------------------------------------

def _copy_tree(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if d not in SKIPPED_DIRS)
        for name in sorted(files):
            if name in EXCLUDED_FILES or name.endswith(SKIPPED_SUFFIXES):
                continue
            source = os.path.join(root, name)
            target = os.path.join(dst, os.path.relpath(source, src))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(source, target)


def _copy(src_root, pairs, dest):
    for src_rel, dst_rel in pairs:
        src = os.path.join(src_root, *src_rel.split("/"))
        dst = os.path.join(dest, *dst_rel.split("/"))
        if os.path.isdir(src):
            _copy_tree(src, dst)
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
            shutil.copyfile(src, dst)
        else:
            raise SyncError(f"hariku-core has no {src_rel}")


def check_template_license(folder):
    """The SDK promises an MIT template: refuse a template that isn't."""
    license_path = os.path.join(folder, "LICENSE")
    try:
        with open(license_path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        raise SyncError("template_extension/ has no LICENSE; the SDK expects the MIT one")
    if "MIT License" not in text:
        raise SyncError("template_extension/LICENSE isn't the MIT License")
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIPPED_DIRS]
        for name in files:
            if name.endswith(".py"):
                with open(os.path.join(root, name), encoding="utf-8") as f:
                    head = f.read(1000)
                if "SPDX-License-Identifier: MIT" not in head:
                    raise SyncError(f"template_extension/{name} has no MIT license header")


def assert_nothing_internal(dest):
    for root, dirs, files in os.walk(dest):
        dirs[:] = [d for d in dirs if d != ".git"]
        leaked = EXCLUDED_FILES.intersection(files)
        if leaked:
            raise SyncError(f"Internal files in the SDK: {sorted(leaked)} in {root}")


def synced_from_text(tag, tag_sha, main_sha, release_url):
    core = f"https://github.com/{CORE_REPO}"
    return f"""# Synced from Hariku core

These files come from [{CORE_REPO}]({core}), Hariku's source, and
`.github/workflows/sync.yml` updates them every day. Change them there, not here.

## From the latest Hariku release: {tag}

- Release: {release_url}
- Commit: [{tag_sha[:7]}]({core}/commit/{tag_sha}) (`{tag_sha}`)

Files:

- `DEVELOPERS.md`
- `tools/packager.py`
- `.vscode/`

## From main

- Commit: [{main_sha[:7]}]({core}/commit/{main_sha}) (`{main_sha}`)

Files (the template and the store's policies aren't tied to a Hariku version):

- `template_extension/`
- `store_guidelines/`, from `docs/en/extension_store/` (without the store's internal review
  guidelines, which are for reviewers only)
"""


def copy_all(tag, tag_dir, tag_sha, main_dir, main_sha, release_url, dest="."):
    if not TAG_RE.match(tag):
        raise SyncError(f"{tag!r} is not a release tag like v2.10.0")
    for name, sha in (("tag", tag_sha), ("main", main_sha)):
        if not SHA_RE.match(sha or ""):
            raise SyncError(f"The {name} commit {sha!r} is not a full commit SHA")
    check_template_license(os.path.join(main_dir, "template_extension"))
    _copy(tag_dir, FROM_TAG, dest)
    _copy(main_dir, FROM_MAIN, dest)
    with open(os.path.join(dest, "SYNCED_FROM.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(synced_from_text(tag, tag_sha, main_sha, release_url))
    assert_nothing_internal(dest)


# ------------------------------------------------------------
# The SDK ZIP and its release notes
# ------------------------------------------------------------

def build_zip(output, root="."):
    """Hariku_V2_Developer_SDK.zip: the SDK without its workflows and tests."""
    names = []
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in ZIP_CONTENTS:
            path = os.path.join(root, entry)
            if os.path.isfile(path):
                zf.write(path, entry)
                names.append(entry)
                continue
            if not os.path.isdir(path):
                raise SyncError(f"The SDK has no {entry}")
            for folder, dirs, files in os.walk(path):
                dirs[:] = sorted(d for d in dirs if d not in SKIPPED_DIRS)
                for name in sorted(files):
                    if name in EXCLUDED_FILES or name.endswith(SKIPPED_SUFFIXES):
                        continue
                    source = os.path.join(folder, name)
                    arcname = os.path.relpath(source, root).replace(os.sep, "/")
                    zf.write(source, arcname)
                    names.append(arcname)
    return names


def release_notes(tag, release_url, tag_sha, main_sha):
    version = tag[1:]
    core = f"https://github.com/{CORE_REPO}"
    return f"""The Hariku Developer SDK for Hariku {version}.

- Hariku {version}: {release_url}
- `DEVELOPERS.md` and the packager come from hariku-core {tag}
  ([{tag_sha[:7]}]({core}/commit/{tag_sha})).
- The template and the store guidelines come from hariku-core main
  ([{main_sha[:7]}]({core}/commit/{main_sha})).

Download `{ZIP_NAME}` below, or press "Use this template" on
https://github.com/{SDK_REPO} to start a repository for your own extension.
The template and the examples are under the MIT License.
"""


# ------------------------------------------------------------
# Command line
# ------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync the Hariku SDK from Hariku core.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("latest", help="print the latest Hariku release tag and page")

    copy = sub.add_parser("copy", help="copy the synced files and write SYNCED_FROM.md")
    copy.add_argument("--tag", required=True)
    copy.add_argument("--tag-dir", required=True)
    copy.add_argument("--tag-sha", required=True)
    copy.add_argument("--main-dir", required=True)
    copy.add_argument("--main-sha", required=True)
    copy.add_argument("--release-url", required=True)
    copy.add_argument("--dest", default=".")

    zip_cmd = sub.add_parser("zip", help=f"build {ZIP_NAME}")
    zip_cmd.add_argument("--output", default=ZIP_NAME)

    notes = sub.add_parser("notes", help="print the SDK release notes")
    notes.add_argument("--tag", required=True)
    notes.add_argument("--release-url", required=True)
    notes.add_argument("--tag-sha", required=True)
    notes.add_argument("--main-sha", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "latest":
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            tag, url = latest_release(lambda path: github_json(path, token))
            print(f"tag={tag}")
            print(f"release_url={url}")
        elif args.command == "copy":
            copy_all(args.tag, args.tag_dir, args.tag_sha, args.main_dir, args.main_sha,
                     args.release_url, args.dest)
            print(f"Synced from {CORE_REPO} {args.tag} and main.")
        elif args.command == "zip":
            names = build_zip(args.output)
            print(f"Wrote {args.output} ({len(names)} files).")
        elif args.command == "notes":
            sys.stdout.write(release_notes(args.tag, args.release_url, args.tag_sha,
                                           args.main_sha))
    except SyncError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
