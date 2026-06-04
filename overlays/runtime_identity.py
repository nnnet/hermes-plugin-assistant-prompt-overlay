"""ACTIVE RUNTIME identity block — authoritative model/provider info.

Without this, the agent answers "what am I running on" from conversation
memory (session DB / hindsight recall) and reproduces stale provider
names from earlier sessions after the operator switches providers.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _slug_from_base_url(base_url: str) -> str:
    """Resolve the user-config provider key whose base_url matches.

    For config-defined providers Hermes labels ``agent.provider`` with
    the generic string ``"custom"`` (see hermes_cli/runtime_provider).
    That label travels into the system prompt and the LLM faithfully
    echoes it back when asked which provider it is on, which is useless
    for the operator. Look the real slug up by base_url so the runtime
    block carries the name the operator actually picked from /model
    (e.g. ``claude-bifrost``, ``openrouter_custom``).
    """
    if not base_url:
        return ""
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
    except Exception:
        return ""
    providers = (cfg or {}).get("providers") or {}
    if not isinstance(providers, dict):
        return ""
    target = base_url.strip().rstrip("/").lower()
    for slug, entry in providers.items():
        if not isinstance(entry, dict):
            continue
        entry_url = str(
            entry.get("base_url")
            or entry.get("url")
            or entry.get("api")
            or ""
        ).strip().rstrip("/").lower()
        if entry_url and entry_url == target:
            return str(slug)
    return ""


def build_runtime_identity_line(agent: Any) -> Optional[str]:
    """Return a system-prompt block naming the current model/provider/base_url.

    Returns None when the agent exposes none of these — caller skips append.
    """
    bits: list[str] = []
    if getattr(agent, "model", ""):
        bits.append(f"model={agent.model}")
    provider = str(getattr(agent, "provider", "") or "").strip()
    base_url = str(getattr(agent, "base_url", "") or "").strip()
    # Replace the generic "custom" label with the matching config.yaml
    # provider slug so the LLM reports the name the operator chose.
    if provider.lower() == "custom" and base_url:
        resolved = _slug_from_base_url(base_url)
        if resolved:
            provider = resolved
    if provider:
        bits.append(f"provider={provider}")
    if base_url:
        bits.append(f"base_url={base_url}")
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
