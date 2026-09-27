# Hariku Developer SDK example: aruna_command
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""
Aruna Shopping List: a shopping list you keep by talking to Aruna, Hariku's
command bar (Ctrl+Alt+Backspace), by typing or by voice.

What it shows:
  - actions with aliases, more ways to say them in English and Indonesian
    (core.commands.add_aliases, Hariku 2.7)
  - an action that only answers, so Aruna stays open and shows what it said
    (core.commands.add_answer_actions, Hariku 2.8)
  - a command with content, an intent: "add milk to my shopping list" gives
    the handler "milk" (core.commands.add_intent, Hariku 2.9)
  - Reply(say=..., confirm=...): Aruna asks the question, and runs your
    function when the user answers yes
  - an action that opens a dialog, for which Aruna closes first
  - teardown() taking the aliases and the intent back

Needs Hariku 2.9 or later, so the manifest says "minimum_core_version": "2.9".
"""

import logging
import os

import core.api
import core.commands
import core.hotkeys
from core.commands import Reply
from core.i18n import get_translator
from core.speech import speak

logger = logging.getLogger(__name__)

EXT_DIR = os.path.dirname(os.path.abspath(__file__))
_ = get_translator("aruna_command", os.path.join(EXT_DIR, "locales"))

EXT_NAME = "Aruna Shopping List"    # fixed, so the keys a user picks survive a language change
DATA_KEY = "ArunaShoppingList"      # the name core.api.load_data()/save_data() store it under
INTENT_ID = f"{EXT_NAME}.add_item"
MAX_ITEMS = 100

# More ways to say each action. Aliases work in every language, whatever
# language Hariku speaks. Two or three distinctive words work best; Aruna
# ignores fillers such as "please", "tolong", "the" and "my".
ALIASES = {
    "read_list": ["daftar belanja", "apa saja yang harus dibeli",
                  "shopping list", "what do i need to buy"],
    "clear_list": ["kosongkan daftar belanja", "hapus daftar belanja",
                   "clear my shopping list", "empty the shopping list"],
}

# The intent's patterns. Each has exactly one {text}, and its other words are
# matched word for word (a misheard letter is forgiven, a missing word is
# not), so write each way of saying it that people use.
PATTERNS = [
    "tambahkan {text} ke daftar belanja",
    "masukkan {text} ke daftar belanja",
    "add {text} to my shopping list",
    "add {text} to the shopping list",
    "put {text} on my shopping list",
]


def action_id(name):
    """How Hariku names an action: "<extension name>.<action name>"."""
    return f"{EXT_NAME}.{name}"


def load_items():
    items = core.api.load_data(DATA_KEY).get("items", [])
    return [item for item in items if isinstance(item, str)]


def save_items(items):
    data = core.api.load_data(DATA_KEY)
    data["items"] = items
    return core.api.save_data(DATA_KEY, data)


# ------------------------------------------------------------
# Actions (they get a key in Input Gestures, and Aruna runs them by name)
# ------------------------------------------------------------

def read_list():
    """Says the list. It only speaks, so it is named in add_answer_actions()
    and Aruna stays open with the answer shown."""
    items = load_items()
    if items:
        speak(_("list_items", count=len(items), items=", ".join(items)))
    else:
        speak(_("list_empty"))


def clear_list():
    """Empties the list after asking. It opens a dialog, so it is NOT an
    answer action: Aruna closes, gives the focus back, then runs it."""
    items = load_items()
    if not items:
        speak(_("list_empty"))
        return
    if core.api.prompt_yes_no(_("clear_title"), _("clear_question", count=len(items))):
        if save_items([]):
            speak(_("list_cleared"))
        else:
            speak(_("not_saved"))


# ------------------------------------------------------------
# The intent
# ------------------------------------------------------------

def on_add(request):
    """Aruna calls this on the UI thread when a sentence matches one of the
    PATTERNS; request.text is what {text} held, as typed or heard, with its
    capitals kept. Keep it quick: no network, nothing slow.

    Return None when the text isn't for you (Aruna tries the next intent, then
    handles the text as it would without you), a string to say, or a Reply."""
    item = request.text.strip(" .,!?")
    if not item:
        return None
    items = load_items()
    if any(existing.casefold() == item.casefold() for existing in items):
        return _("already_there", item=item)       # a string: Aruna just says it
    if len(items) >= MAX_ITEMS:
        return _("list_full")

    def add():
        # Runs when the user answers yes (Enter, "ya", "yes"). What it
        # returns (a string, a Reply or None) is Aruna's answer.
        current = load_items()          # read again: the list may have changed
        current.append(item)
        if not save_items(current):
            return _("not_saved")
        return _("added", item=item, count=len(current))

    # A question: Aruna says it and waits. "No" or Escape says "OK, cancelled"
    # (pass cancel=... to run something then too).
    return Reply(say=_("confirm_add", item=item), confirm=add)


# ------------------------------------------------------------
# Loading and unloading
# ------------------------------------------------------------

def register(bus):
    # No default keys: users give them one in Input Gestures if they like.
    core.hotkeys.register_action(EXT_NAME, "read_list", _("action_read_list"), None, False,
                                 read_list)
    core.hotkeys.register_action(EXT_NAME, "clear_list", _("action_clear_list"), None, False,
                                 clear_list)
    for name, aliases in ALIASES.items():
        core.commands.add_aliases(action_id(name), aliases)
    core.commands.add_answer_actions(action_id("read_list"))
    core.commands.add_intent(INTENT_ID, PATTERNS, on_add, title=_("intent_title"))
    logger.info("Aruna Shopping List loaded.")


def teardown():
    core.commands.remove_intent(INTENT_ID)
    for name in ALIASES:
        core.commands.remove_aliases(action_id(name))
    logger.info("Aruna Shopping List unloaded.")
