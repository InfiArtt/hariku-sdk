# Hariku Developer SDK example: extension_guide
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""
Proverbs: says an old proverb, and ships a guide that Hariku shows.

What it shows:
  - docs/en/guide.md and docs/id/guide.md: the extension's guide, in each
    language. Its first line, the # heading, is its title. Hariku lists it in
    Help, Extension guides..., opens it from the Extension Manager's Guide
    button, and Aruna opens it too ("guide for proverbs", "panduan peribahasa")
    without any code here.
  - core.guides.open_guide(): opening your own guide from an action, such
    as a Help button on a window of yours
  - core.guides.has_guide(): whether it is there to open

Hariku 2.11 is the first with guides and core.guides, so the manifest says
"minimum_core_version": "2.11": older versions list this extension as
needing Hariku 2.11 and don't load it. (Hariku 2.11 is coming; see the
SDK's README for the Hariku version these examples match.)
"""

import logging
import os
import random

import core.guides
import core.hotkeys
from core.i18n import get_current_language, get_translator
from core.speech import speak

logger = logging.getLogger(__name__)

EXT_DIR = os.path.dirname(os.path.abspath(__file__))
# The extension's id is its folder's name: the same whether Hariku loads the
# folder or unpacks the .hrk (my_extension.hrk becomes a folder named
# my_extension), so this works however the extension is installed.
EXT_ID = os.path.basename(EXT_DIR)
_ = get_translator("extension_guide", os.path.join(EXT_DIR, "locales"))

EXT_NAME = "Proverbs"           # fixed, so the keys a user picks survive a language change

# Old proverbs, free for anyone to use.
PROVERBS = {
    "en": [
        "Many hands make light work.",
        "Rome wasn't built in a day.",
        "Where there's a will, there's a way.",
        "Actions speak louder than words.",
        "A journey of a thousand miles begins with a single step.",
    ],
    "id": [
        "Sedikit demi sedikit, lama-lama menjadi bukit.",
        "Berat sama dipikul, ringan sama dijinjing.",
        "Bersatu kita teguh, bercerai kita runtuh.",
        "Di mana ada kemauan, di situ ada jalan.",
        "Hemat pangkal kaya.",
    ],
}


def say_proverb():
    proverbs = PROVERBS.get(get_current_language(), PROVERBS["en"])
    speak(random.choice(proverbs))


def open_my_guide():
    """Open this extension's guide in the web browser, in the language Hariku
    speaks, else in English. NVDA reads it in browse mode: H jumps from
    heading to heading."""
    if not core.guides.has_guide(EXT_ID):
        speak(_("no_guide"))
    elif not core.guides.open_guide(EXT_ID):
        speak(_("guide_failed"))
    # To show the guide as text in a window when no browser opens, as Hariku
    # itself does, call ui.guides_dialog.show_guide(parent, EXT_ID) instead.


def register(bus):
    core.hotkeys.register_action(EXT_NAME, "say_proverb", _("action_say_proverb"), None, False,
                                 say_proverb)
    core.hotkeys.register_action(EXT_NAME, "open_guide", _("action_open_guide"), None, False,
                                 open_my_guide)
    logger.info("Proverbs loaded.")


def teardown():
    logger.info("Proverbs unloaded.")
