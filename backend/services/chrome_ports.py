"""Predictable Chrome remote-debugging ports per LinkedIn account slot."""

from __future__ import annotations

import os

BASE_CHROME_DEBUG_PORT = 9222


def account_port_for_slot(slot_1_indexed: int) -> int:
    """Account slot 1 -> 9222, slot 2 -> 9223, slot 3 -> 9224, …"""
    if slot_1_indexed < 1:
        slot_1_indexed = 1
    return BASE_CHROME_DEBUG_PORT + slot_1_indexed - 1


def account_port_for_bot_id(bot_id: str | None) -> int:
    """Map supervisor ``BOT_ID`` to a port when ``CHROME_DEBUG_PORT`` is unset."""
    bid = (bot_id or "").strip() or "main"
    if bid == "main":
        return account_port_for_slot(1)
    if bid.isdigit():
        # Primary is slot 1; LINKEDIN_USERNAME_<n> uses id ``n`` at slot n+1.
        return account_port_for_slot(int(bid) + 1)
    return BASE_CHROME_DEBUG_PORT


def resolve_chrome_debug_port() -> int:
    """Port for ``--remote-debugging-port`` (env override, then BOT_ID mapping)."""
    for key in ("CHROME_DEBUG_PORT", "ACCOUNT_PORT"):
        raw = (os.getenv(key) or "").strip()
        if raw.isdigit():
            return int(raw)
    return account_port_for_bot_id(os.getenv("BOT_ID"))
