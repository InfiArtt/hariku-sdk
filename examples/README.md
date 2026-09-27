# Examples

Five small extensions, each showing one part of Hariku's extension API. Every one is a
complete extension: a `manifest.json`, a commented `main.py`, its texts in English and
Indonesian (`locales/`), and a guide for its users in both languages (`docs/en/guide.md`,
`docs/id/guide.md`). They are under the MIT License: copy what you need into your own extension.

## hello_hotkey

An action with a default key (Shift+H) that speaks, and a double press that says more.
The smallest useful extension. Hariku 2.0 or later.

## aruna_command

A shopping list kept by talking to Aruna, Hariku's command bar: actions with aliases in two
languages, an action that only answers, and a command with content ("add milk to my shopping
list") that asks before it saves, with `Reply(confirm=...)`. Hariku 2.9 or later.

## preferences_page

A page of settings in Preferences, with a label made right before each control so screen
readers name them right, saved when the user presses OK. Hariku 2.0 or later.

## background_task

Counting the files in a folder on a worker thread with `core.api.run_thread()`, then saying
the result, without ever freezing Hariku; the same key stops it, and so does `teardown()`.
Hariku 2.0 or later.

## extension_guide

An extension that ships its own guide (`docs/<language>/guide.md`) and opens it with
`core.guides`. Needs Hariku 2.11, which is coming: on older versions the Extension Manager
lists it as needing Hariku 2.11 and doesn't load it.

## Trying one

Copy an example's folder into `%APPDATA%\Hariku2\extensions\`, keeping its folder name (that
is its id), and restart Hariku. Or pack it first:

```
python tools/pack.py examples/hello_hotkey
```

and put `dist/hello_hotkey.hrk` in that folder instead. Hariku asks before it loads a `.hrk`
that isn't in the Extension Store, since it can't vouch for it.
