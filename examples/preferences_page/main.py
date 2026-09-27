# Hariku Developer SDK example: preferences_page
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""
Daily Goal: a page of settings in Preferences, and an action that uses them.

What it shows:
  - core.preferences.register_panel(): a page of your own in Preferences
  - a wx.Panel with a text field, a choice and a check box, each with its
    label made right before it, so screen readers name every control right
  - apply: saving what the user chose when they press OK or Apply, with
    core.api.load_data() and core.api.save_data()
  - reading saved settings safely, with defaults for anything missing
  - core.api.open_preferences(): an action that opens the page itself
  - core.i18n.format_date(): day and month names in the user's language

Why labels come first: on Windows, NVDA names a text field or a list after
the text created just before it. Make a control first and its label after,
and every control on the page is read with the wrong name. (SetName() doesn't
change what NVDA says.) A check box and a button carry their own label.

Works on Hariku 2.0 and later.
"""

import logging
import os
from datetime import date

import wx

import core.api
import core.hotkeys
import core.preferences
from core.i18n import format_date, get_translator
from core.speech import speak

logger = logging.getLogger(__name__)

EXT_DIR = os.path.dirname(os.path.abspath(__file__))
_ = get_translator("preferences_page", os.path.join(EXT_DIR, "locales"))

EXT_NAME = "Daily Goal"         # fixed, so the keys a user picks survive a language change
DATA_KEY = "DailyGoalExample"   # the name core.api.load_data()/save_data() store it under
MAX_GOAL = 200                  # characters

DEFAULTS = {"goal": "", "interrupt": False, "say_date": True}


# ------------------------------------------------------------
# Settings
# ------------------------------------------------------------

def load_settings():
    """The saved settings, with the default for anything missing or of the
    wrong type (a file edited by hand, or saved by an older version)."""
    data = core.api.load_data(DATA_KEY)
    settings = dict(DEFAULTS)
    for key, default in DEFAULTS.items():
        if isinstance(data.get(key), type(default)):
            settings[key] = data[key]
    return settings


def save_settings(settings):
    data = core.api.load_data(DATA_KEY)
    data.update(settings)
    return core.api.save_data(DATA_KEY, data)


# ------------------------------------------------------------
# The page in Preferences
# ------------------------------------------------------------

class DailyGoalPanel(wx.Panel):
    """Every label is created right before its control."""

    def __init__(self, parent, settings):
        super().__init__(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # A text field: its label first, then the field.
        sizer.Add(wx.StaticText(self, label=_("label_goal")), 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        self.goal = wx.TextCtrl(self, value=settings["goal"])
        self.goal.SetMaxLength(MAX_GOAL)
        sizer.Add(self.goal, 0, wx.EXPAND | wx.ALL, 10)

        # A choice: the same, label first.
        sizer.Add(wx.StaticText(self, label=_("label_speech")), 0, wx.LEFT | wx.RIGHT, 10)
        self.speech = wx.Choice(self, choices=[_("speech_wait"), _("speech_interrupt")])
        self.speech.SetSelection(1 if settings["interrupt"] else 0)
        sizer.Add(self.speech, 0, wx.ALL, 10)

        # A check box says its own label; it needs no text before it.
        self.say_date = wx.CheckBox(self, label=_("label_say_date"))
        self.say_date.SetValue(settings["say_date"])
        sizer.Add(self.say_date, 0, wx.ALL, 10)

        self.SetSizer(sizer)

    def get_settings(self):
        return {
            "goal": self.goal.GetValue().strip(),
            "interrupt": self.speech.GetSelection() == 1,
            "say_date": self.say_date.GetValue(),
        }


_panel = None


def _create_panel(parent):
    """Hariku calls this the first time the user opens the page; it must
    return the wx.Panel."""
    global _panel
    _panel = DailyGoalPanel(parent, load_settings())
    return _panel


def _apply_panel():
    """Hariku calls this when the user presses OK or Apply, if the page was
    opened this time."""
    if _panel is None:
        return
    try:
        settings = _panel.get_settings()
    except RuntimeError:        # the page's window is already gone
        return
    if not save_settings(settings):
        speak(_("not_saved"))


# ------------------------------------------------------------
# Actions
# ------------------------------------------------------------

def say_goal():
    settings = load_settings()
    if not settings["goal"]:
        speak(_("no_goal"))
        return
    if settings["say_date"]:
        today = date.today()
        # format_date() gives the day and month names in the user's language.
        # The day's number goes in as it is: its %d would say "07".
        text = _("date_and_goal", weekday=format_date(today, "%A"), day=today.day,
                 month=format_date(today, "%B"), goal=settings["goal"])
    else:
        text = _("goal", goal=settings["goal"])
    speak(text, interrupt=settings["interrupt"])


def open_settings():
    # Opens Preferences on the page whose title contains this text.
    core.api.open_preferences(_("ext_name"))


def register(bus):
    # The page's title in Preferences, in the user's language.
    core.preferences.register_panel(_("ext_name"), "", _create_panel, _apply_panel)
    core.hotkeys.register_action(EXT_NAME, "say_goal", _("action_say_goal"), ord("Y"), False,
                                 say_goal, default_shift=True)      # Shift+Y
    core.hotkeys.register_action(EXT_NAME, "open_settings", _("action_open_settings"), None,
                                 False, open_settings)              # no key
    logger.info("Daily Goal loaded.")


def teardown():
    global _panel
    _panel = None
    logger.info("Daily Goal unloaded.")
