# Hariku Developer SDK example: background_task
# Copyright (C) 2026 InfiArtt (Rafli)
#
# SPDX-License-Identifier: MIT
"""
Folder Counter: counts the files in your Documents folder on a worker
thread, and says the result when it's done. Hariku keeps answering keys and
speaking the whole time.

What it shows:
  - core.api.run_thread(work, done): work() runs on a worker thread, and
    done(result) runs on the UI thread afterwards, with work()'s return
    value, or with None when work() raised an exception
  - the worker touches no wx and doesn't speak; the done callback does
  - one job at a time: the same key again stops it
  - a threading.Event the worker checks, so teardown() can stop it too

Anything slow belongs on a worker like this: network requests, reading many
files, big calculations. A frozen Hariku is a silent Hariku for a screen
reader user.

Works on Hariku 2.0 and later.
"""

import logging
import os
import threading
import time

import core.api
import core.hotkeys
from core.i18n import get_translator
from core.speech import speak

logger = logging.getLogger(__name__)

EXT_DIR = os.path.dirname(os.path.abspath(__file__))
_ = get_translator("background_task", os.path.join(EXT_DIR, "locales"))

EXT_NAME = "Folder Counter"     # fixed, so the keys a user picks survive a language change

_stop = None    # the running job's threading.Event, or None when nothing runs


def documents_folder():
    """The user's Documents folder, else their home folder. Built at run
    time: never write a path from your own computer into an extension."""
    home = os.path.expanduser("~")
    documents = os.path.join(home, "Documents")
    return documents if os.path.isdir(documents) else home


def count_files(folder, stop):
    """The slow part. It runs on the worker thread, so it must not touch wx
    or speak: it only returns its result. Returns None when stopped."""
    started = time.monotonic()
    files = 0
    size = 0
    for root, _dirs, names in os.walk(folder):     # os.walk skips folders it can't open
        if stop.is_set():
            return None
        for name in names:
            try:
                size += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue        # a file that went away, or that we may not read
            files += 1
    return {"files": files, "size": size, "seconds": time.monotonic() - started}


def size_text(size):
    if size >= 1024 ** 3:
        return _("size_gb", value=f"{size / 1024 ** 3:.1f}")
    if size >= 1024 ** 2:
        return _("size_mb", value=f"{size / 1024 ** 2:.1f}")
    return _("size_kb", value=f"{size / 1024:.0f}")


def start_or_stop():
    """The action: start counting, or stop the count that is running."""
    global _stop
    if _stop is not None:
        _stop.set()
        _stop = None
        speak(_("stopped"), interrupt=True)
        return

    stop = threading.Event()
    _stop = stop
    folder = documents_folder()
    speak(_("counting", folder=os.path.basename(folder) or folder))

    # run_thread() takes a function without arguments. A nested def (rather
    # than a lambda or functools.partial) keeps a name for Hariku's log.
    def work():
        return count_files(folder, stop)

    def done(result):
        # Back on the UI thread: safe to speak and to use wx here.
        global _stop
        if stop.is_set():
            return              # stopped by the user or by teardown(): stay quiet
        _stop = None
        if result is None:
            speak(_("failed"))  # work() raised; Hariku's log has the error
            return
        speak(_("result", files=result["files"], size=size_text(result["size"]),
                folder=os.path.basename(folder) or folder,
                seconds=f"{result['seconds']:.0f}"))

    core.api.run_thread(work, done)


def register(bus):
    core.hotkeys.register_action(EXT_NAME, "count_documents", _("action_count"), ord("J"),
                                 False, start_or_stop, default_shift=True)   # Shift+J
    logger.info("Folder Counter loaded.")


def teardown():
    """Stop a count that is still running, so the worker ends on its own."""
    global _stop
    if _stop is not None:
        _stop.set()
        _stop = None
    logger.info("Folder Counter unloaded.")
