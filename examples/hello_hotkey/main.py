# Hariku Developer SDK example: hello_hotkey
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""
Hello Hotkey: the smallest useful extension, one action with a default key.

What it shows:
  - register(bus): the function Hariku calls when it loads the extension
  - core.hotkeys.register_action(): an action with a default key, Shift+H
  - a callback with a tap_count argument, for a double press
  - core.speech.speak(): talking through the user's screen reader
  - locales/en.json and locales/id.json: every text the user hears
  - teardown(), which the Extension Store asks every extension for

Every action is also a command for Aruna, Hariku's command bar
(Ctrl+Alt+Backspace): Aruna matches what the user types or says against each
action's description, so "greet me" (or "sapa aku") runs this one. Users can
move the key, or make it work outside Hariku, in Preferences, Input Gestures.

Works on Hariku 2.0 and later.
"""

import logging
import os
from datetime import datetime

import core.hotkeys
from core.i18n import get_translator
from core.speech import speak

logger = logging.getLogger(__name__)

EXT_DIR = os.path.dirname(os.path.abspath(__file__))
# The domain is the extension's id, so these texts never mix with another
# extension's texts of the same name.
_ = get_translator("hello_hotkey", os.path.join(EXT_DIR, "locales"))

# The first argument of register_action(). Keep it fixed (not translated):
# Hariku saves the keys a user picks under "<extension name>.<action name>",
# so they survive a change of language.
EXT_NAME = "Hello Hotkey"


def greet(tap_count=1):
    """Shift+H once: a greeting. Twice quickly: the time as well.

    Hariku calls this at once on the first press (tap_count=1) and again if
    the same key comes back quickly (tap_count=2). A callback without a
    tap_count argument is simply called once per press."""
    if tap_count == 1:
        speak(_("hello"))
    elif tap_count == 2:
        # interrupt=True cuts the greeting short: the user asked for more.
        speak(_("time_now", time=datetime.now().strftime("%H:%M")), interrupt=True)


def register(bus):
    """Called by Hariku when it loads this extension. `bus` is Hariku's event
    bus; this extension doesn't need it."""
    core.hotkeys.register_action(
        EXT_NAME,               # shown as the group in Input Gestures
        "greet",                # the action's id within this extension
        _("action_greet"),      # its description: Input Gestures shows it, Aruna matches it
        ord("H"),               # the default key: H...
        False,                  # ...without Ctrl...
        greet,
        default_shift=True,     # ...with Shift: Shift+H, while Hariku has the focus
    )
    logger.info("Hello Hotkey loaded.")


def teardown():
    """Called by Hariku when it shuts down. This extension starts no timers
    or threads, so there is nothing to stop."""
    logger.info("Hello Hotkey unloaded.")
