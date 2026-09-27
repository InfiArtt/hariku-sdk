# Licensing of the files in this repository

This repository mixes files the SDK owns with files synced from Hariku's own source,
[InfiArtt/hariku-core](https://github.com/InfiArtt/hariku-core). Each keeps its own license.

## MIT License: the SDK's own files

These are under the MIT License in [LICENSE](LICENSE), copyright InfiArtt (Rafli):

- `README.md`, `NOTICE.md`, `CONTRIBUTING.md`, `SYNCED_FROM.md`, `.gitignore`
- `examples/`, every file in it
- `tools/check_extension.py` and `tools/pack.py`
- `tests/`
- `.github/`: the workflows, their script and the issue forms

## MIT License: the extension template

`template_extension/` is under the MIT License too, in its own
[template_extension/LICENSE](template_extension/LICENSE). It is synced from Hariku's main branch,
where its owner relicensed it from the GPL so that anyone can copy it into an extension.

## Hariku's license: files synced from hariku-core

These are part of Hariku, which is free software under the GNU General Public License,
version 3 or later, with the Hariku Extension Exception. They keep that license and any
license header they carry:

- `DEVELOPERS.md`
- `tools/packager.py` (its header says so)
- `store_guidelines/`
- `.vscode/`

`SYNCED_FROM.md` records the Hariku release and the commits they come from. The full texts
are in hariku-core: [LICENSE](https://github.com/InfiArtt/hariku-core/blob/main/LICENSE) and
[LICENSE-EXCEPTION](https://github.com/InfiArtt/hariku-core/blob/main/LICENSE-EXCEPTION).

## Your extension

Your extension is yours. Under the Hariku Extension Exception, an extension that works with
Hariku only through its documented extension API (the `core.*` modules, the manifest and the
extension loader) may use any license you choose, open source or proprietary. Copying the
MIT template or examples into it is fine under any license, as long as you keep their MIT
notice with the parts you keep. Running the packager or the checker on your extension doesn't
change your extension's license.

An extension that copies Hariku's own GPL source code, rather than calling its API, is a
derivative of Hariku and must be under the GPL. Read the exception itself for the exact terms;
this summary is not legal advice.
