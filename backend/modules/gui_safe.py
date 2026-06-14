"""Display-safe wrappers around pyautogui.

The job-applier bot was written for desktop use: it pops GUI dialogs
(alert/confirm) and presses keys to keep the screen awake. On a Linux
server with no display, ``import pyautogui`` crashes outright and any
dialog would hang an unattended run forever.

These wrappers use real pyautogui when a display exists, and logging
no-op fallbacks otherwise. ``confirm`` auto-picks the "keep going"
button so unattended runs never stall waiting for a human.
"""

import logging
import os
import sys


def _display_available() -> bool:
    if os.name == "nt" or sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


HAS_DISPLAY = _display_available()

_pyautogui = None
if HAS_DISPLAY:
    try:
        import pyautogui as _pyautogui

        _pyautogui.FAILSAFE = False
    except Exception:
        HAS_DISPLAY = False
        _pyautogui = None

# pyautogui compatibility attribute (some callers set it directly).
FAILSAFE = False


def alert(text="", title="", button="OK", *args, **kwargs):
    if _pyautogui:
        return _pyautogui.alert(text, title, button)
    logging.warning(f"[headless] ALERT suppressed ({title}): {text}")
    return button  # truthy — behaves as if the user clicked the button


_CONTINUE_WORDS = ("continue", "okay", "submit", "look")


def confirm(text="", title="", buttons=("OK",), *args, **kwargs):
    if _pyautogui:
        return _pyautogui.confirm(text, title, buttons)
    choice = None
    for b in buttons:
        if any(w in str(b).lower() for w in _CONTINUE_WORDS):
            choice = b
            break
    if choice is None:
        choice = list(buttons)[-1]
    logging.warning(
        f"[headless] CONFIRM suppressed ({title}): auto-selected {choice!r}"
    )
    return choice


def press(key, *args, **kwargs):
    if _pyautogui:
        return _pyautogui.press(key, *args, **kwargs)
    return None
