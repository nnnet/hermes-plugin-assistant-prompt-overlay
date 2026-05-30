"""ACTIVE RUNTIME identity block — authoritative model/provider info.

Without this, the agent answers "what am I running on" from conversation
memory (session DB / hindsight recall) and reproduces stale provider
names from earlier sessions after the operator switches providers.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def build_runtime_identity_line(agent: Any) -> Optional[str]:
    """Return a system-prompt block naming the current model/provider/base_url.

    Returns None when the agent exposes none of these — caller skips append.
    """
    bits: list[str] = []
    if getattr(agent, "model", ""):
        bits.append(f"model={agent.model}")
    if getattr(agent, "provider", ""):
        bits.append(f"provider={agent.provider}")
    if getattr(agent, "base_url", ""):
        bits.append(f"base_url={agent.base_url}")
    if not bits:
        return None

    block = (
        "## CURRENT ACTIVE RUNTIME (authoritative)\n\n"
        + "\n".join(f"- {b}" for b in bits)
        + "\n\n"
        "This block is the ONLY source of truth for the agent's current "
        "model, provider, and inference base URL. When asked anything about "
        "infrastructure, what you are running on, what provider/model is in "
        "use, или \"что у тебя под капотом\" — quote these values exactly. "
        "Conversation memory, hindsight recall, prior session notes, and "
        "anything reproduced from training data MUST NOT override this block. "
        "If any stored note mentions a different provider name (for example "
        "`anthropic_custom`, `anthropic-custom`, `clr-gateway`, "
        "`claude-agent-sdk`, `openai`, `openrouter`), that note is STALE — "
        "ignore it and report the values above. This block is regenerated "
        "from live config on every fresh system-prompt build; trust it."
    )
    try:
        logger.warning(
            "ACTIVE_RUNTIME_INJECTED session=%s bits=%s",
            getattr(agent, "session_id", "?"), bits,
        )
    except Exception:
        pass
    return block
