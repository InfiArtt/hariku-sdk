# Contributing to the Hariku Developer SDK

Thank you for helping other people build Hariku extensions. This is a short guide to where
things live and what a change needs.

## Where to change what

- The SDK's own files (`README.md`, `examples/`, `tools/check_extension.py`, `tools/pack.py`,
  `tests/`, `.github/`): change them here, with a pull request.
- Files synced from Hariku (`DEVELOPERS.md`, `tools/packager.py`, `store_guidelines/`,
  `.vscode/`, `template_extension/`): change them in
  [InfiArtt/hariku-core](https://github.com/InfiArtt/hariku-core). The sync workflow copies
  them here, and would overwrite a change made here. `SYNCED_FROM.md` says where they came from.

## Before you open a pull request

- Run the checker and the tests:

  ```
  python tools/check_extension.py --all
  python -m pip install pytest
  python -m pytest tests -q
  ```

- Keep the examples small, commented and true to `DEVELOPERS.md`: use only the documented
  API, set `minimum_core_version` to the oldest Hariku the example really runs on, and give
  every text in both `locales/en.json` and `locales/id.json`.
- Update an example's guides (`docs/en/guide.md` and `docs/id/guide.md`) when you change what
  it does.
- In anything a user will see or hear, make each label right before its control, and test with
  a screen reader when you can.
- Write for people using a screen reader: clear headings, steps as numbered lists, no tables
  for anything essential, and plain words. Indonesian text speaks to the reader as "kamu".
- Update the Indonesian section of `README.md` along with the English one.
- `tools/` stays standard library only, and runs on Python 3.10 (the Python Hariku runs).

## License

The SDK's own files are under the MIT License. By contributing to them you agree to license
your contribution under the MIT License too. See [NOTICE.md](NOTICE.md) for the other files.
