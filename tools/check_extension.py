#!/usr/bin/env python3
# Hariku Developer SDK: check an extension folder before you pack or submit it.
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""
check_extension.py: check a Hariku extension folder.

    python tools/check_extension.py my_extension [another_extension ...]
    python tools/check_extension.py --all         every extension in this repository:
                                                   top-level folders with a manifest.json,
                                                   and the folders in examples/
    python tools/check_extension.py --strict ...  warnings count as errors too

It reads your files and never imports or runs them, and it needs only Python's
standard library.

Errors are what keeps Hariku from loading the extension, or what the Extension
Store turns it down for. Warnings are likely mistakes and store rules worth a
look; they don't fail the check unless you pass --strict.

Exit code: 0 when there are no errors, 1 when there are (or warnings with
--strict), 2 for a mistake in the command line.

The rules come from DEVELOPERS.md, store_guidelines/ and the way Hariku's
extension loader (core/extension_manager.py), guides (core/guides.py) and
translations (core/i18n.py) read an extension.
"""

import argparse
import ast
import json
import os
import re
import string
import sys

REQUIRED_FIELDS = ("name", "version", "description", "main", "author", "language",
                   "minimum_core_version")

# core.guides.valid_id: the folder name is the extension's id, and the name of
# its .hrk file. Hariku finds guides and storage folders only for these.
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
# store_guidelines/coding_standards.txt, 2.3: lowercase_with_underscores.
STYLE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# core.guides.valid_language: the folder names in docs/.
LANG_RE = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})?$")
# store_guidelines 3.1 / 4 and DEVELOPERS.md: MAJOR.MINOR or MAJOR.MINOR.PATCH,
# with an optional a1, b1 or rc1. The store compares them as Python packaging
# versions, so "v1.0" or "1.0-beta" would never count as an update.
VERSION_RE = re.compile(r"^\d+(?:\.\d+){1,2}(?:(?:a|b|rc)\d+)?$")
# Hariku versions: "2.9", "2.10.0".
CORE_VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?$")

# core.i18n skips a language file whose manifest lacks one of these.
LOCALE_MANIFEST_FIELDS = ("language_name", "language_code", "translator", "email", "version")
# "key@persona" texts (core 2.10); "playful" uses the plain ones.
PERSONAS = {"sweet", "bro", "royal", "polite"}
MAX_GUIDE_BYTES = 512 * 1024            # core.guides.MAX_GUIDE_BYTES

# Official Hariku extensions (core.extension_manager, Hariku 2.11). An
# extension with one of these ids would pass as official, so the store never
# takes one.
OFFICIAL_IDS = frozenset([
    "developer_toolkit", "ghost_taskbar", "key_notifier", "ambience", "project_system",
    "window_teleporter", "markdown_reader", "lumina", "account_manager", "world_clock",
    "routines", "gcal_integration", "filter", "quick_expand", "weather", "briefing",
    "finance", "flight_radar", "clipboard_history", "sound_themes", "earthquake", "marine",
    "air_quality", "space", "edge_voices", "sleep_tracker", "piper_voices", "cockpit",
    "voice_control", "timer_alarm", "world_trip", "orbit", "dropbox", "calculator",
])

# What tools/packager.py leaves out of a .hrk.
SKIP_DIRS = {"__pycache__", ".git", ".vscode", ".idea"}
# Folders an extension may have besides its own modules.
DATA_DIRS = {"lib", "locales", "docs", "sounds"}
NATIVE_SUFFIXES = (".pyd", ".dll", ".so", ".dylib", ".exe")
SECRET_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json"}
SECRET_SUFFIXES = (".pem", ".key", ".pfx", ".p12")
HOOK_MODULES = {"keyboard", "pynput", "pyHook", "pyWinhook"}

# Hosts where plain http:// is expected (local servers, XML namespaces).
_LOCAL_HTTP_RE = re.compile(r"^http://(localhost|127\.0\.0\.1|\[::1\]|www\.w3\.org|"
                            r"schemas\.|purl\.org|ns\.adobe\.com)", re.I)
_ABS_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]|"
                          r"/home/|/Users/)", re.I)
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
_FENCE_RE = re.compile(r"^ {0,3}(```+|~~~+)")


# ------------------------------------------------------------
# Results
# ------------------------------------------------------------

class Problem:
    """One thing the check found: level is "error" or "warning"; path is
    relative to the extension folder."""

    def __init__(self, level, message, path=None, line=None):
        self.level = level
        self.message = message
        self.path = path
        self.line = line

    def where(self):
        if not self.path:
            return ""
        return f"{self.path}:{self.line}" if self.line else self.path

    def __str__(self):
        where = self.where()
        return f"{self.level}: {where}: {self.message}" if where else f"{self.level}: {self.message}"

    def __repr__(self):
        return f"Problem({self.level!r}, {self.message!r}, {self.path!r}, {self.line!r})"


class Report:
    """What check_folder() found in one extension folder."""

    def __init__(self, folder):
        self.folder = folder
        self.ext_id = os.path.basename(os.path.abspath(folder))
        self.manifest = None
        self.problems = []

    def error(self, message, path=None, line=None):
        self.problems.append(Problem("error", message, path, line))

    def warn(self, message, path=None, line=None):
        self.problems.append(Problem("warning", message, path, line))

    @property
    def errors(self):
        return [p for p in self.problems if p.level == "error"]

    @property
    def warnings(self):
        return [p for p in self.problems if p.level == "warning"]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _rel(folder, path):
    return os.path.relpath(path, folder).replace(os.sep, "/")


def _walk(folder):
    """(directory, [files]) of an extension, as the packager sees it."""
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        yield root, sorted(files)


def _read_json(report, folder, path):
    """The JSON in `path`, or None after reporting why it can't be read.
    Hariku opens JSON as UTF-8 without a byte order mark."""
    rel = _rel(folder, path)
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        report.error(f"can't be read: {e}", rel)
        return None
    if data.startswith(b"\xef\xbb\xbf"):
        report.error("starts with a byte order mark (BOM), which Hariku can't read: "
                     "save it as UTF-8 without BOM", rel)
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        report.error(f"isn't UTF-8 text ({e.reason} at byte {e.start})", rel)
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        report.error(f"isn't valid JSON: {e.msg} (column {e.colno})", rel, e.lineno)
        return None


def _list(names, limit=8):
    names = sorted(names)
    shown = ", ".join(names[:limit])
    return shown + (f" and {len(names) - limit} more" if len(names) > limit else "")


def _dotted(node):
    """"os.system" for the expression os.system, else None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _is_constant(node, value):
    return isinstance(node, ast.Constant) and node.value is value


def _version_tuple(text):
    return tuple(int(p) for p in text.split(".")[:3])


# ------------------------------------------------------------
# The folder and its id
# ------------------------------------------------------------

def _check_id(report):
    ext_id = report.ext_id
    if not ID_RE.match(ext_id):
        report.error(f'The folder name is the extension\'s id, and "{ext_id}" is not one Hariku '
                     "accepts: use 1 to 64 letters, digits, underscores or hyphens "
                     "(lowercase_with_underscores is best)")
    elif not STYLE_ID_RE.match(ext_id):
        report.warn(f'The store asks for an id (folder name) in lowercase_with_underscores; '
                    f'"{ext_id}" isn\'t')
    if ext_id in OFFICIAL_IDS:
        report.error(f'"{ext_id}" is the id of an official Hariku extension: give yours '
                     "another folder name")


# ------------------------------------------------------------
# manifest.json
# ------------------------------------------------------------

def _check_manifest(report):
    folder = report.folder
    path = os.path.join(folder, "manifest.json")
    if not os.path.isfile(path):
        report.error("There is no manifest.json: Hariku only loads a folder that has one")
        return None
    manifest = _read_json(report, folder, path)
    if manifest is None:
        return None
    if not isinstance(manifest, dict):
        report.error("must be a JSON object ({ ... })", "manifest.json")
        return None
    report.manifest = manifest

    missing = [f for f in REQUIRED_FIELDS if f not in manifest]
    if missing:
        report.error(f"Hariku won't load it without these fields: {', '.join(missing)}",
                     "manifest.json")
    for field in REQUIRED_FIELDS:
        if field in manifest and (not isinstance(manifest[field], str)
                                  or not manifest[field].strip()):
            report.error(f'"{field}" must be a text (a JSON string) that isn\'t empty',
                         "manifest.json")

    version = manifest.get("version")
    if isinstance(version, str) and version.strip() and not VERSION_RE.match(version):
        report.error(f'"version" is "{version}": use two or three numbers with dots, such as '
                     '"1.0" or "1.0.0" (a pre-release may end in a1, b1 or rc1), so the store '
                     "can tell a newer version from an older one", "manifest.json")

    minimum = manifest.get("minimum_core_version")
    if isinstance(minimum, str) and minimum.strip() and not CORE_VERSION_RE.match(minimum):
        report.error(f'"minimum_core_version" is "{minimum}": use a Hariku version such as '
                     '"2.9" or "2.10.0"', "manifest.json")

    tested = manifest.get("last_tested_core_version")
    if tested is not None:
        if not isinstance(tested, str) or not CORE_VERSION_RE.match(tested):
            report.error('"last_tested_core_version" must be a Hariku version such as "2.10"',
                         "manifest.json")
        elif (isinstance(minimum, str) and CORE_VERSION_RE.match(minimum)
              and _version_tuple(tested) < _version_tuple(minimum)):
            report.warn(f'"last_tested_core_version" ({tested}) is older than '
                        f'"minimum_core_version" ({minimum})', "manifest.json")

    language = manifest.get("language")
    if isinstance(language, str) and language.strip() and not LANG_RE.match(language):
        report.warn(f'"language" is "{language}": use a language code such as "en" or "id"',
                    "manifest.json")

    declared_id = manifest.get("id")
    if declared_id is not None and declared_id != report.ext_id:
        report.warn(f'"id" says "{declared_id}", but Hariku takes the id from the folder '
                    f'name, "{report.ext_id}"', "manifest.json")

    main = manifest.get("main")
    if isinstance(main, str) and main.strip():
        if "/" in main or "\\" in main or main.startswith(".."):
            report.error(f'"main" is "{main}": it must be a file right in the extension '
                         "folder, not in a subfolder (Hariku refuses paths there)",
                         "manifest.json")
        elif not main.endswith(".py"):
            report.error(f'"main" is "{main}": it must be a Python file ending in .py',
                         "manifest.json")
        elif not os.path.isfile(os.path.join(folder, main)):
            report.error(f'"main" names {main}, which isn\'t in the extension folder',
                         "manifest.json")
    return manifest


# ------------------------------------------------------------
# Python files
# ------------------------------------------------------------

class _Scanner(ast.NodeVisitor):
    """Patterns store_guidelines/ asks you to avoid, where a quick look at the
    code can find them. Each is a warning: some have good reasons, which you
    then explain when you submit."""

    def __init__(self, report, rel):
        self.report = report
        self.rel = rel

    def _warn(self, node, message):
        self.report.warn(message, self.rel, getattr(node, "lineno", None))

    def visit_Expr(self, node):
        # A bare string is a docstring or a comment in disguise: not checked.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func
        name = func.id if isinstance(func, ast.Name) else None
        dotted = _dotted(func)
        if name in ("eval", "exec", "compile"):
            self._warn(node, f"{name}() runs code built at run time: never give it anything "
                             "from outside your source (coding standards 10.1)")
        elif name == "print":
            self._warn(node, "print() output goes nowhere in Hariku: use logging "
                             "(coding standards 5.3)")
        elif dotted in ("os.system", "os.popen"):
            self._warn(node, f"{dotted}() runs a command through the shell: use subprocess "
                             "with a list of arguments, without shell=True")
        for kw in node.keywords:
            if kw.arg == "shell" and not _is_constant(kw.value, False):
                self._warn(kw.value, "shell=True runs a command through the shell, where text "
                                     "from outside can become a command: pass a list of "
                                     "arguments instead")
            elif kw.arg == "verify" and _is_constant(kw.value, False):
                self._warn(kw.value, "verify=False turns off certificate checks "
                                     "(coding standards 10.3)")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if _dotted(node) in ("ssl._create_unverified_context", "ssl.CERT_NONE"):
            self._warn(node, "this turns off certificate checks (coding standards 10.3)")
        self.generic_visit(node)

    def _check_import(self, node, module):
        top = (module or "").split(".")[0]
        if top in HOOK_MODULES:
            self._warn(node, f'"{top}" installs a keyboard hook, which Hariku extensions must '
                             "not do: register keys with core.hotkeys")

    def visit_Import(self, node):
        for alias in node.names:
            self._check_import(node, alias.name)

    def visit_ImportFrom(self, node):
        if node.level == 0:
            self._check_import(node, node.module)

    def visit_Constant(self, node):
        value = node.value
        if isinstance(value, str):
            if value.startswith("http://") and not _LOCAL_HTTP_RE.match(value):
                self._warn(node, f'"{value[:60]}" is plain HTTP: use https:// '
                                 "(coding standards 10.3)")
            elif _ABS_PATH_RE.match(value):
                self._warn(node, f'"{value[:60]}" looks like a path on your own computer: '
                                 "build paths at run time, with core.api.get_storage_dir() "
                                 "and os.path (submission guide 3.4)")


def _module_functions(tree):
    return {node.name for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _check_python(report):
    folder = report.folder
    manifest = report.manifest or {}
    main = manifest.get("main") if isinstance(manifest.get("main"), str) else None
    lib = os.path.join(folder, "lib")

    for root, files in _walk(folder):
        in_lib = root == lib or root.startswith(lib + os.sep)
        for name in files:
            path = os.path.join(root, name)
            rel = _rel(folder, path)
            if not name.endswith(".py"):
                continue
            try:
                with open(path, "rb") as f:
                    source = f.read()
            except OSError as e:
                report.error(f"can't be read: {e}", rel)
                continue
            try:
                tree = compile(source, rel, "exec", ast.PyCF_ONLY_AST, dont_inherit=True)
            except SyntaxError as e:
                message = f"doesn't compile: {e.msg}"
                (report.warn if in_lib else report.error)(message, rel, e.lineno)
                continue
            except (ValueError, UnicodeDecodeError) as e:
                (report.warn if in_lib else report.error)(f"doesn't compile: {e}", rel)
                continue
            if in_lib:
                continue        # bundled libraries are someone else's code
            _Scanner(report, rel).visit(tree)
            if root == folder and name == main:
                defined = _module_functions(tree)
                if "register" not in defined:
                    report.warn("defines no register(bus): Hariku calls it to start your "
                                "extension, so nothing will happen", rel)
                if "teardown" not in defined:
                    report.warn("defines no teardown(): the Extension Store requires one "
                                "(submission guide 3.7), even an empty one", rel)

    # Every extension's modules share one namespace (DEVELOPERS.md).
    prefix = report.ext_id + "_"
    for entry in sorted(os.listdir(folder)):
        path = os.path.join(folder, entry)
        if entry.endswith(".py") and os.path.isfile(path):
            module = entry[:-3]
        elif (os.path.isdir(path) and entry not in DATA_DIRS | SKIP_DIRS
              and os.path.isfile(os.path.join(path, "__init__.py"))):
            module = entry
        else:
            continue
        if entry == main or module.startswith(prefix):
            continue
        report.warn(f'Name it "{prefix}{module}": every extension\'s modules share one '
                    f'namespace, so "{module}" may import another extension\'s module or one '
                    "of Hariku's own", entry)


# ------------------------------------------------------------
# Other files
# ------------------------------------------------------------

def _check_files(report):
    folder = report.folder
    for root, files in _walk(folder):
        for name in files:
            rel = _rel(folder, os.path.join(root, name))
            lower = name.lower()
            if lower.endswith(NATIVE_SUFFIXES):
                report.warn("a compiled binary: only pure-Python libraries work in every "
                            "Hariku install (coding standards 11.2)", rel)
            if lower in SECRET_NAMES or lower.endswith(SECRET_SUFFIXES):
                report.warn("looks like a key or a secret, and the packager would put it in "
                            "your .hrk: keep it out of the extension folder", rel)


# ------------------------------------------------------------
# locales/
# ------------------------------------------------------------

def _placeholders(text):
    """The {names} in a text, or None when str.format() can't read it."""
    try:
        return {field.split(".")[0].split("[")[0]
                for _lit, field, _spec, _conv in string.Formatter().parse(text)
                if field is not None}
    except ValueError:
        return None


def _check_locales(report):
    folder = report.folder
    locales = os.path.join(folder, "locales")
    if not os.path.isdir(locales):
        return
    files = sorted(f for f in os.listdir(locales) if f.endswith(".json"))
    if not files:
        report.warn("has no language files (en.json, id.json ...)", "locales/")
        return

    languages = {}      # language code -> (relative path, messages)
    for name in files:
        path = os.path.join(locales, name)
        rel = _rel(folder, path)
        data = _read_json(report, folder, path)
        if data is None:
            continue
        if (not isinstance(data, dict) or not isinstance(data.get("manifest"), dict)
                or not isinstance(data.get("messages"), dict)):
            report.error('Hariku skips a language file without a "manifest" object and a '
                         '"messages" object', rel)
            continue
        manifest, messages = data["manifest"], data["messages"]
        missing = [f for f in LOCALE_MANIFEST_FIELDS if f not in manifest]
        if missing:
            report.error(f"Hariku skips this file: its manifest has no {', '.join(missing)}",
                         rel)
            continue
        code = manifest["language_code"]
        stem = name[:-5]
        if code != stem:
            report.warn(f'"language_code" is "{code}", but the file is {name}', rel)
        if code in languages:
            report.error(f'another file is language "{code}" too ({languages[code][0]}): '
                         "Hariku keeps only one of them", rel)
            continue
        not_text = [k for k, v in messages.items() if not isinstance(v, str)]
        if not_text:
            report.error(f"every message must be a text; these aren't: {_list(not_text)}", rel)
        for key, text in messages.items():
            if "@" in key and key.rsplit("@", 1)[1] not in PERSONAS:
                report.warn(f'"{key}": Hariku\'s personas are {", ".join(sorted(PERSONAS))} '
                            "(playful uses the plain text)", rel)
            if isinstance(text, str) and _placeholders(text) is None:
                report.warn(f'"{key}" has a lone {{ or }}: write {{{{ or }}}} for a brace, or '
                            "the text can't be filled in", rel)
        languages[code] = (rel, messages)

    if not languages:
        return
    if "en" not in languages:
        report.warn("There is no English language file (locales/en.json): Hariku falls back "
                    "to English, so without one people see your raw keys")
    reference = "en" if "en" in languages else sorted(languages)[0]
    ref_rel, ref_messages = languages[reference]
    for code, (rel, messages) in sorted(languages.items()):
        if code == reference:
            continue
        missing = set(ref_messages) - set(messages)
        extra = set(messages) - set(ref_messages)
        if missing:
            report.warn(f"lacks {len(missing)} key(s) that {ref_rel} has "
                        f"(people get the English text): {_list(missing)}", rel)
        if extra:
            report.warn(f"has {len(extra)} key(s) that {ref_rel} doesn't: {_list(extra)}", rel)
        for key in sorted(set(ref_messages) & set(messages)):
            ours, theirs = ref_messages[key], messages[key]
            if not (isinstance(ours, str) and isinstance(theirs, str)):
                continue
            a, b = _placeholders(ours), _placeholders(theirs)
            if a is not None and b is not None and a != b:
                report.warn(f'"{key}" has the placeholders {sorted(b)}, but {ref_rel} has '
                            f"{sorted(a)}", rel)


# ------------------------------------------------------------
# docs/<lang>/guide.md (Hariku 2.11)
# ------------------------------------------------------------

def _check_guide(report, path, rel):
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        report.warn(f"can't be read: {e}", rel)
        return
    if size > MAX_GUIDE_BYTES:
        report.warn("is bigger than 512 KB, and Hariku doesn't show a guide that big", rel)
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        report.warn("isn't UTF-8 text", rel)
        return
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    first = next((line for line in lines if line.strip()), "")
    if not re.match(r"^# \S", first):
        report.warn("should start with its title as a # heading, such as \"# My Extension\": "
                    "Hariku shows it as the guide's name", rel)

    in_fence = False
    level = 0
    titles = 0
    for number, line in enumerate(lines, 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if m:
            new = len(m.group(1))
            if new == 1:
                titles += 1
                if titles == 2:
                    report.warn("has a second # heading: use # once, for the title, and ## "
                                "for sections", rel, number)
            elif level and new > level + 1:
                report.warn(f"skips a heading level (from {'#' * level} to {'#' * new})",
                            rel, number)
            level = new
            continue
        plain = re.sub(r"`[^`\n]*`", "", line)
        if plain.lstrip().startswith("|"):
            report.warn("a table: Hariku's guides show tables as plain text", rel, number)
        elif re.search(r"!?\[[^\]]*\]\([^)]*\)", plain):
            report.warn("a link or image: Hariku's guides show them as plain text", rel, number)
        elif re.search(r"</?[A-Za-z][^>]*>", plain):
            report.warn("HTML: Hariku's guides show it as plain text", rel, number)


def _check_guides(report):
    folder = report.folder
    docs = os.path.join(folder, "docs")
    found = False
    if os.path.isdir(docs):
        for lang in sorted(os.listdir(docs)):
            path = os.path.join(docs, lang, "guide.md")
            if not os.path.isfile(path):
                continue
            found = True
            rel = _rel(folder, path)
            if not LANG_RE.match(lang):
                report.warn(f'Hariku only looks for guides in folders named after a language '
                            f'code (en, id, pt-BR), not "{lang}"', rel)
            _check_guide(report, path, rel)
    if not os.path.isfile(os.path.join(docs, "en", "guide.md")):
        if found:
            report.warn("There is no English guide (docs/en/guide.md): Hariku shows it when "
                        "there is none in the user's language")
        else:
            report.warn("There is no guide: write docs/en/guide.md so people can learn to use "
                        "your extension (Hariku 2.11 shows it in Help, Extension guides)")


# ------------------------------------------------------------
# Checking
# ------------------------------------------------------------

def check_folder(folder):
    """Check one extension folder; returns a Report."""
    report = Report(folder)
    if not os.path.isdir(folder):
        report.error(f"{folder} is not a folder")
        return report
    _check_id(report)
    _check_manifest(report)
    _check_python(report)
    _check_files(report)
    _check_locales(report)
    _check_guides(report)
    return report


def find_extensions(root="."):
    """Every extension in a repository: its top-level folders with a
    manifest.json, then the folders in examples/."""
    found = []
    for parent in (root, os.path.join(root, "examples")):
        if not os.path.isdir(parent):
            continue
        for name in sorted(os.listdir(parent)):
            path = os.path.join(parent, name)
            if (not name.startswith(".") and os.path.isdir(path)
                    and os.path.isfile(os.path.join(path, "manifest.json"))):
                found.append((os.path.relpath(path, root) if root == "." else path)
                             .replace(os.sep, "/"))
    return found


def _annotation(report, problem):
    """A GitHub Actions annotation, so problems show on the pull request."""
    path = os.path.join(report.folder, problem.path) if problem.path else report.folder
    try:
        path = os.path.relpath(path)
    except ValueError:          # another drive, on Windows
        pass
    path = path.replace(os.sep, "/")
    line = f",line={problem.line}" if problem.line else ""
    message = problem.message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return f"::{problem.level} file={path}{line}::{message}"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check Hariku extension folders: the manifest, the Python files, the "
                    "translations and the guide.")
    parser.add_argument("folders", nargs="*", help="extension folders to check")
    parser.add_argument("--all", action="store_true",
                        help="check every extension in this repository (top-level folders "
                             "with a manifest.json, and examples/)")
    parser.add_argument("--root", default=".", help="the repository for --all (default: .)")
    parser.add_argument("--strict", action="store_true",
                        help="count warnings as errors")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="only print problems and the summary")
    args = parser.parse_args(argv)

    folders = list(args.folders)
    if args.all:
        folders += [f for f in find_extensions(args.root) if f not in folders]
    if not folders:
        parser.error("name an extension folder, or use --all")

    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    annotate = os.environ.get("GITHUB_ACTIONS") == "true"

    errors = warnings = 0
    for folder in folders:
        report = check_folder(folder)
        errors += len(report.errors)
        warnings += len(report.warnings)
        if not args.quiet or report.problems:
            print(f"Checking {folder}")
        for problem in report.problems:
            print(f"  {problem}")
            if annotate:
                print(_annotation(report, problem))
        if not args.quiet:
            if not report.problems:
                print("  OK: no problems found.")
            elif not report.errors:
                print("  OK: no errors.")
    print(f"Checked {len(folders)} extension folder(s): {errors} error(s), "
          f"{warnings} warning(s).")
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
