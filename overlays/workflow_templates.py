"""Inject live inventory of workflow templates from /opt/hermes-workflows/.

So Hermes can name a matching template in the chief brief — every brief
would otherwise force the chief to hand-roll N kanban tasks even when
workflow_run was the correct answer.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_WF_DIR = Path("/opt/hermes-workflows")


def build_workflow_templates_block() -> Optional[str]:
    """Return a system-prompt block listing available workflow templates.

    Returns None when the directory is missing or empty.
    """
    try:
        if not _WF_DIR.is_dir():
            return None
        entries: list[str] = []
        for yaml_path in sorted(_WF_DIR.glob("*.yaml")):
            text = yaml_path.read_text(encoding="utf-8")
            name_m = re.search(r"^name:\s*(\S+)", text, re.MULTILINE)
            desc_m = re.search(
                r"^description:\s*>?\s*\n?(.+?)(?=\n\w|\n$)",
                text, re.MULTILINE | re.DOTALL,
            )
            if not name_m:
                continue
            name = name_m.group(1)
            desc = (
                " ".join(desc_m.group(1).split())[:140]
                if desc_m else ""
            )
            entries.append(f"  - `{name}` — {desc}")
        if not entries:
            return None
        return (
            "\n## WORKFLOW TEMPLATES — LIVE INVENTORY (just-read)\n"
            "These are TEAM-SHAPE templates (composition + cycle), "
            "NOT domain-specific pipelines. You are the Тимлид: classify "
            "the delegated goal into a team type (dev/research/creative/"
            "ops), then pick the matching template by `description` and "
            "run it yourself via `workflow_run` — the team self-decomposes "
            "domain work inside the cycle. See the `You are the Тимлид` "
            "section for the full decision flow. Available templates:\n"
            + "\n".join(entries) + "\n"
        )
    except Exception as exc:
        logger.debug("workflow templates inventory failed: %s", exc)
        return None
