"""Inject the LIVE Google credentials state from /opt/data/.google-creds-state.json.

Without this, Hermes hallucinates "OAuth not configured" from training
context even when the state file plainly says ready. The file is small
(<1KB) so re-reading on every prompt build is cheap.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_STATE_PATH = Path("/opt/data/.google-creds-state.json")


def build_google_creds_block() -> Optional[str]:
    """Return a system-prompt block describing live Google creds state.

    Returns None when the state file is missing/unreadable — caller skips.
    """
    try:
        if not _STATE_PATH.exists():
            return None
        state = json.loads(_STATE_PATH.read_text())
    except Exception as exc:
        logger.debug("google-creds-state read failed: %s", exc)
        return None

    if state.get("status") == "ready":
        scopes = state.get("scopes") or []
        return (
            "\n## GOOGLE CREDS — LIVE STATE (just-read)\n"
            f"`/opt/data/.google-creds-state.json` says **status=ready**.\n"
            f"  - token path: `{state.get('path', '/opt/data/google_token.json')}`\n"
            f"  - {len(scopes)} scope(s) including: "
            f"{', '.join(s.rsplit('/', 1)[-1] for s in scopes[:5])}\n"
            f"  - client_id: `{state.get('client_id', '?')}`\n"
            f"  - validated_at: {state.get('validated_at', '?')}\n\n"
            "Therefore: Google Workspace is AVAILABLE this run. "
            "Do NOT tell the user OAuth is missing — that would be a lie "
            "the operator can verify in 5 seconds. Brief the chief: "
            "«Google Workspace доступен, scopes готовы» and spawn.\n"
        )

    reason = state.get("reason", "unknown")
    return (
        "\n## GOOGLE CREDS — LIVE STATE (just-read)\n"
        f"`/opt/data/.google-creds-state.json` says **status=missing** "
        f"(reason: {reason}).\n"
        "Therefore: Google Workspace is NOT available this run. "
        "Tell the user one line («У нас нет Google-токена, выберем "
        "локальную альтернативу — SQLite + Flask») and spawn the "
        "chief WITHOUT Google. Don't ask the operator to do OAuth.\n"
    )
