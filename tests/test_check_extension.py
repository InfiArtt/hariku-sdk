# Hariku Developer SDK tests.
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""tools/check_extension.py: good and bad manifests, compile errors, language
files, guides, warnings and the exit code."""

import os

import pytest

import check_extension as ce
from conftest import GOOD_MANIFEST, ROOT, locale


def messages(report, level=None):
    return [p.message for p in report.problems if level is None or p.level == level]


def has(report, level, text):
    return any(text in m for m in messages(report, level))


# ------------------------------------------------------------
# A good extension, and the SDK's own
# ------------------------------------------------------------

def test_a_good_extension_has_no_problems(make_ext):
    report = ce.check_folder(make_ext())
    assert report.problems == []


@pytest.mark.parametrize("folder", ce.find_extensions(ROOT))
def test_the_template_and_every_example_pass(folder):
    report = ce.check_folder(folder)
    assert not report.errors, [str(p) for p in report.problems]
    assert not report.warnings, [str(p) for p in report.problems]


def test_find_extensions_sees_the_template_and_the_examples():
    names = {os.path.basename(f) for f in ce.find_extensions(ROOT)}
    assert {"template_extension", "hello_hotkey", "aruna_command", "preferences_page",
            "background_task", "extension_guide"} <= names


# ------------------------------------------------------------
# The folder name (the id)
# ------------------------------------------------------------

def test_an_id_hariku_cant_use_is_an_error(make_ext):
    report = ce.check_folder(make_ext(name="my.tool"))
    assert has(report, "error", "is not one Hariku accepts")


def test_an_id_not_in_lowercase_with_underscores_is_a_warning(make_ext):
    report = ce.check_folder(make_ext(name="My-Tool"))
    assert not report.errors and has(report, "warning", "lowercase_with_underscores")


def test_an_official_id_is_an_error(make_ext):
    report = ce.check_folder(make_ext(name="weather"))
    assert has(report, "error", "official Hariku extension")


def test_a_missing_folder_is_an_error(tmp_path):
    report = ce.check_folder(str(tmp_path / "nothing_here"))
    assert has(report, "error", "is not a folder")


# ------------------------------------------------------------
# manifest.json
# ------------------------------------------------------------

def test_no_manifest(make_ext):
    report = ce.check_folder(make_ext({"manifest.json": None}))
    assert has(report, "error", "There is no manifest.json")


def test_invalid_json_gives_the_line(make_ext):
    report = ce.check_folder(make_ext({"manifest.json": '{\n  "name": "x",\n  oops\n}'}))
    problem = next(p for p in report.errors if p.path == "manifest.json")
    assert "isn't valid JSON" in problem.message and problem.line == 3


def test_a_byte_order_mark_is_an_error(make_ext):
    import json
    data = b"\xef\xbb\xbf" + json.dumps(GOOD_MANIFEST).encode("utf-8")
    report = ce.check_folder(make_ext({"manifest.json": data}))
    assert has(report, "error", "byte order mark")


def test_not_an_object(make_ext):
    report = ce.check_folder(make_ext({"manifest.json": "[1, 2]"}))
    assert has(report, "error", "must be a JSON object")


@pytest.mark.parametrize("field", ce.REQUIRED_FIELDS)
def test_each_required_field(make_ext, field):
    manifest = {k: v for k, v in GOOD_MANIFEST.items() if k != field}
    report = ce.check_folder(make_ext({"manifest.json": manifest}))
    assert has(report, "error", field)


@pytest.mark.parametrize("field, value", [("name", 3), ("author", ""), ("version", 1.0),
                                          ("minimum_core_version", 2.9), ("main", None)])
def test_fields_must_be_texts(make_ext, field, value):
    report = ce.check_folder(make_ext({"manifest.json": dict(GOOD_MANIFEST, **{field: value})}))
    assert has(report, "error", f'"{field}" must be a text')


# The rule in store_guidelines (3.1 and 4) and DEVELOPERS.md: MAJOR.MINOR or
# MAJOR.MINOR.PATCH, with an optional a1, b1 or rc1.
@pytest.mark.parametrize("version", ["1.0", "1.0.0", "2.3.1", "10.20.30", "1.0.0b1", "2.0rc1",
                                     "1.1a2"])
def test_good_versions(make_ext, version):
    report = ce.check_folder(make_ext({"manifest.json": dict(GOOD_MANIFEST, version=version)}))
    assert not report.errors


@pytest.mark.parametrize("version", ["v1.0", "1", "1.0-beta", "one", "1.2.3.4", "1.0.0.0.0",
                                     "1.0.0-rc1", "1.0.0 beta"])
def test_bad_versions(make_ext, version):
    report = ce.check_folder(make_ext({"manifest.json": dict(GOOD_MANIFEST, version=version)}))
    assert has(report, "error", '"version" is')


@pytest.mark.parametrize("value, ok", [("2.9", True), ("2.10.0", True), ("2", False),
                                       ("2.x", False), ("v2.9", False)])
def test_minimum_core_version(make_ext, value, ok):
    manifest = dict(GOOD_MANIFEST, minimum_core_version=value)
    report = ce.check_folder(make_ext({"manifest.json": manifest}))
    assert has(report, "error", '"minimum_core_version" is') is not ok


def test_last_tested_core_version(make_ext):
    older = dict(GOOD_MANIFEST, last_tested_core_version="2.8")
    report = ce.check_folder(make_ext({"manifest.json": older}))
    assert not report.errors and has(report, "warning", "older than")
    bad = dict(GOOD_MANIFEST, last_tested_core_version="latest")
    assert has(ce.check_folder(make_ext({"manifest.json": bad}, name="other")), "error",
               "last_tested_core_version")


@pytest.mark.parametrize("main, text", [("src/main.py", "not in a subfolder"),
                                        ("..\\main.py", "not in a subfolder"),
                                        ("main.txt", "ending in .py"),
                                        ("start.py", "isn't in the extension folder")])
def test_bad_main(make_ext, main, text):
    report = ce.check_folder(make_ext({"manifest.json": dict(GOOD_MANIFEST, main=main)}))
    assert has(report, "error", text)


def test_an_id_field_that_differs_from_the_folder(make_ext):
    report = ce.check_folder(make_ext({"manifest.json": dict(GOOD_MANIFEST, id="other")}))
    assert not report.errors and has(report, "warning", "takes the id from the folder")


def test_a_language_that_isnt_a_code(make_ext):
    manifest = dict(GOOD_MANIFEST, language="English")
    report = ce.check_folder(make_ext({"manifest.json": manifest}))
    assert has(report, "warning", "language code")


# ------------------------------------------------------------
# Python files
# ------------------------------------------------------------

def test_a_compile_error_is_an_error_with_its_line(make_ext):
    report = ce.check_folder(make_ext({"main.py": "def register(bus):\n    return (\n"}))
    problem = next(p for p in report.errors if p.path == "main.py")
    assert "doesn't compile" in problem.message and problem.line


def test_a_compile_error_in_another_module(make_ext):
    report = ce.check_folder(make_ext({"my_tool_util.py": "x = = 1\n"}))
    assert any(p.path == "my_tool_util.py" and p.line == 1 for p in report.errors)


def test_a_compile_error_in_lib_is_only_a_warning(make_ext):
    report = ce.check_folder(make_ext({"lib/old/__init__.py": "print 'python 2'\n"}))
    assert not report.errors and has(report, "warning", "doesn't compile")


def test_no_register_and_no_teardown(make_ext):
    report = ce.check_folder(make_ext({"main.py": "x = 1\n"}))
    assert not report.errors
    assert has(report, "warning", "no register(bus)") and has(report, "warning", "no teardown()")


def test_extra_modules_should_carry_the_id(make_ext):
    report = ce.check_folder(make_ext({"utils.py": "X = 1\n", "my_tool_ui.py": "Y = 2\n",
                                       "helpers/__init__.py": ""}))
    warned = {p.path for p in report.warnings if "namespace" in p.message}
    assert warned == {"utils.py", "helpers"}


@pytest.mark.parametrize("code, text", [
    ("eval(user_text)", "eval()"),
    ("exec(downloaded)", "exec()"),
    ("compile(src, 'x', 'exec')", "compile()"),
    ("import subprocess\nsubprocess.run(cmd, shell=True)", "shell=True"),
    ("import os\nos.system('dir')", "os.system()"),
    ("import requests\nrequests.get(url, verify=False)", "verify=False"),
    ("import ssl\nctx = ssl._create_unverified_context()", "certificate checks"),
    ("print('debug')", "print()"),
    ("import keyboard", "keyboard hook"),
    ("URL = 'http://api.example.com/data'", "plain HTTP"),
    ("PATH = 'C:\\\\Users\\\\me\\\\data.json'", "path on your own computer"),
])
def test_patterns_the_guidelines_warn_about(make_ext, code, text):
    report = ce.check_folder(make_ext({"my_tool_extra.py": code + "\n"}))
    assert not report.errors
    assert has(report, "warning", text), messages(report)


@pytest.mark.parametrize("code", [
    "import re\nPATTERN = re.compile(r'x')",
    "import subprocess\nsubprocess.run(['git', 'status'], shell=False)",
    "LOCAL = 'http://localhost:8080/'",
    "NS = 'http://www.w3.org/2000/svg'",
    '"""A docstring may say http://example.com or C:\\\\Users\\\\me."""',
    "import logging\nlogging.getLogger(__name__).info('eval(x) in a message')",
])
def test_harmless_code_isnt_flagged(make_ext, code):
    report = ce.check_folder(make_ext({"my_tool_extra.py": code + "\n"}))
    assert report.problems == [], messages(report)


def test_code_in_lib_isnt_scanned(make_ext):
    report = ce.check_folder(make_ext({"lib/vendor/__init__.py": "eval('1')\nprint(1)\n"}))
    assert report.problems == []


def test_binaries_and_secrets(make_ext):
    report = ce.check_folder(make_ext({"lib/fast.pyd": b"MZ", "server.pem": "-----BEGIN"}))
    assert has(report, "warning", "compiled binary") and has(report, "warning", "secret")


# ------------------------------------------------------------
# locales/
# ------------------------------------------------------------

def test_a_missing_key_is_a_warning(make_ext):
    report = ce.check_folder(make_ext({
        "locales/en.json": locale("en", {"a": "A", "b": "B", "c": "C"}),
        "locales/id.json": locale("id", {"a": "A"}),
    }))
    assert not report.errors
    problem = next(p for p in report.warnings if p.path == "locales/id.json")
    assert "lacks 2 key(s)" in problem.message and "b, c" in problem.message


def test_a_key_only_in_another_language_is_a_warning(make_ext):
    report = ce.check_folder(make_ext({
        "locales/en.json": locale("en", {"a": "A"}),
        "locales/id.json": locale("id", {"a": "A", "z": "Z"}),
    }))
    assert has(report, "warning", "that locales/en.json doesn't: z")


def test_placeholders_must_match(make_ext):
    report = ce.check_folder(make_ext({
        "locales/en.json": locale("en", {"a": "Hello {name}, {count} new"}),
        "locales/id.json": locale("id", {"a": "Halo {nama}, {count} baru"}),
    }))
    assert has(report, "warning", "placeholders")


def test_a_lone_brace_is_a_warning(make_ext):
    report = ce.check_folder(make_ext({
        "locales/en.json": locale("en", {"a": "Opens with { only", "b": "Closes with } only"}),
        "locales/id.json": locale("id", {"a": "Pakai {{ saja", "b": "Pakai }} saja"}),
    }))
    lone = [p for p in report.warnings if "lone {" in p.message]
    assert [p.path for p in lone] == ["locales/en.json", "locales/en.json"]


def test_a_language_file_hariku_would_skip_is_an_error(make_ext):
    no_messages = {"manifest": locale("id", {})["manifest"]}
    report = ce.check_folder(make_ext({"locales/id.json": no_messages}))
    assert has(report, "error", '"messages"')
    head = locale("id", {"a": "A"})
    del head["manifest"]["email"]
    report = ce.check_folder(make_ext({"locales/id.json": head}, name="other"))
    assert has(report, "error", "manifest has no email")


def test_a_broken_language_file(make_ext):
    report = ce.check_folder(make_ext({"locales/id.json": "{ not json"}))
    assert any(p.path == "locales/id.json" and "valid JSON" in p.message for p in report.errors)


def test_messages_must_be_texts(make_ext):
    report = ce.check_folder(make_ext({"locales/id.json": locale("id", {"hello": ["x"]})}))
    assert has(report, "error", "every message must be a text")


def test_the_file_name_and_the_language_code(make_ext):
    report = ce.check_folder(make_ext({"locales/id.json": locale("ms", {"hello": "Hi {name}"})}))
    assert has(report, "warning", '"language_code" is "ms"')


def test_no_english_file(make_ext):
    report = ce.check_folder(make_ext({"locales/en.json": None}))
    assert has(report, "warning", "no English language file")


def test_persona_keys(make_ext):
    report = ce.check_folder(make_ext({
        "locales/en.json": locale("en", {"hello": "Hi {name}", "hello@royal": "Greetings {name}",
                                         "hello@pirate": "Ahoy {name}"}),
        "locales/id.json": locale("id", {"hello": "Hai {name}", "hello@royal": "Salam {name}",
                                         "hello@pirate": "Ahoy {name}"}),
    }))
    assert has(report, "warning", '"hello@pirate"')
    assert not any('"hello@royal"' in m for m in messages(report))


# ------------------------------------------------------------
# Guides
# ------------------------------------------------------------

def test_no_guide_is_a_warning(make_ext):
    report = ce.check_folder(make_ext({"docs/en/guide.md": None}))
    assert not report.errors and has(report, "warning", "There is no guide")


def test_only_a_guide_in_another_language(make_ext):
    report = ce.check_folder(make_ext({"docs/en/guide.md": None, "docs/id/guide.md": "# Alat\n"}))
    assert has(report, "warning", "no English guide")


def test_a_guide_without_a_title(make_ext):
    report = ce.check_folder(make_ext({"docs/en/guide.md": "My Tool\n\n## Keys\n"}))
    assert not report.errors and has(report, "warning", "should start with its title")


def test_what_the_guide_converter_shows_as_text(make_ext):
    guide = ("# My Tool\n\n### Skipped a level\n\n| a | b |\n\nSee [the site](https://x.y).\n\n"
             "<b>bold</b>\n\n# Again\n\n```\n| not a table in code |\n```\n")
    report = ce.check_folder(make_ext({"docs/en/guide.md": guide}))
    found = messages(report, "warning")
    for text in ("skips a heading level", "a table", "a link", "HTML", "second # heading"):
        assert any(text in m for m in found), (text, found)
    assert sum("a table" in m for m in found) == 1


def test_a_guide_folder_that_isnt_a_language(make_ext):
    report = ce.check_folder(make_ext({"docs/english/guide.md": "# My Tool\n"}))
    assert has(report, "warning", "named after a language code")


# ------------------------------------------------------------
# The command line
# ------------------------------------------------------------

def test_exit_codes(make_ext, capsys):
    good = make_ext()
    warned = make_ext({"docs/en/guide.md": None}, name="warned")
    broken = make_ext({"main.py": "def (\n"}, name="broken")
    assert ce.main([good]) == 0
    assert ce.main([warned]) == 0
    assert ce.main(["--strict", warned]) == 1
    assert ce.main([good, broken]) == 1
    out = capsys.readouterr().out
    assert "error: main.py:1: doesn't compile" in out
    assert "Checked 2 extension folder(s): 1 error(s)" in out


def test_no_folder_is_a_usage_error():
    with pytest.raises(SystemExit) as e:
        ce.main([])
    assert e.value.code == 2


def test_all_checks_the_repository(capsys):
    assert ce.main(["--all", "--root", ROOT, "--quiet"]) == 0
    assert "Checked 6 extension folder(s): 0 error(s), 0 warning(s)." in capsys.readouterr().out


def test_github_annotations(make_ext, capsys, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    ce.main([make_ext({"main.py": "def (\n"})])
    assert "::error file=" in capsys.readouterr().out
