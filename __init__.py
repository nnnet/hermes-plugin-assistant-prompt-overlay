"""assistant-prompt-overlay — Гермес-role system-prompt customizations.

Replaces upstream constants in ``agent.prompt_builder`` and wraps
``agent.system_prompt.build_system_prompt_parts`` to inject our
workflow-templates / Гермес-delegation blocks.

All patches applied at ``register()`` time. No upstream files are edited.

What it replaces (override module-level constants in agent.prompt_builder):
  - ``KANBAN_GUIDANCE``                — kanban/MC verb→tool routing rules
  - ``TOOL_USE_ENFORCEMENT_GUIDANCE``  — native-tool preference + trust
  - ``TOOL_USE_ENFORCEMENT_MODELS``    — expanded model-family substring list
  - ``TASK_COMPLETION_GUIDANCE``       — blanked (covered by TOOL_USE_*)
  - ``ASSISTANT_DELEGATION_GUIDANCE``  — new constant, used by our wrapper

What it adds (wrapped build_system_prompt_parts appends to ``stable_parts``):
  - ASSISTANT_DELEGATION_GUIDANCE     — gated on chief_spawn+!terminal
  - WORKFLOW TEMPLATES live inventory — gated on same as delegation
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register(ctx: Any) -> None:
    """Plugin entry point — installs all prompt overrides + injections."""
    try:
        from agent import prompt_builder as pb
    except Exception as exc:
        logger.error("assistant-prompt-overlay: cannot import agent.prompt_builder: %s", exc)
        return

    try:
        from agent import system_prompt as sp
    except Exception as exc:
        logger.error("assistant-prompt-overlay: cannot import agent.system_prompt: %s", exc)
        return

    # --- Replace module-level constants in agent.prompt_builder ---
    from .constants.assistant_delegation import ASSISTANT_DELEGATION_GUIDANCE
    from .constants.kanban_guidance import KANBAN_GUIDANCE
    from .constants.tool_use_enforcement import (
        TOOL_USE_ENFORCEMENT_GUIDANCE,
        TOOL_USE_ENFORCEMENT_MODELS,
    )

    pb.ASSISTANT_DELEGATION_GUIDANCE = ASSISTANT_DELEGATION_GUIDANCE
    pb.KANBAN_GUIDANCE = KANBAN_GUIDANCE
    pb.TOOL_USE_ENFORCEMENT_GUIDANCE = TOOL_USE_ENFORCEMENT_GUIDANCE
    pb.TOOL_USE_ENFORCEMENT_MODELS = TOOL_USE_ENFORCEMENT_MODELS
    # Upstream still injects TASK_COMPLETION_GUIDANCE for any tool-bearing
    # agent. We blank it because TOOL_USE_ENFORCEMENT_GUIDANCE (now applied
    # to all model families, see expanded TOOL_USE_ENFORCEMENT_MODELS) covers
    # the same "finish the job, don't fabricate" ground.
    pb.TASK_COMPLETION_GUIDANCE = ""

    # ``agent.system_prompt`` does ``from agent.prompt_builder import
    # KANBAN_GUIDANCE, TOOL_USE_ENFORCEMENT_*`` at module load, binding the
    # ORIGINAL string objects into its namespace. A later ``pb.X = NEW``
    # updates pb's binding but not sp's already-imported reference, so the
    # build function would still see upstream values. Re-bind those names in
    # sp's namespace too so the running prompt builder reads our versions.
    sp.KANBAN_GUIDANCE = KANBAN_GUIDANCE
    sp.TOOL_USE_ENFORCEMENT_GUIDANCE = TOOL_USE_ENFORCEMENT_GUIDANCE
    sp.TOOL_USE_ENFORCEMENT_MODELS = TOOL_USE_ENFORCEMENT_MODELS
    # TASK_COMPLETION_GUIDANCE is imported into sp too — blank it there.
    if hasattr(sp, "TASK_COMPLETION_GUIDANCE"):
        sp.TASK_COMPLETION_GUIDANCE = ""

    # --- Wrap build_system_prompt_parts ---
    from .overlays.workflow_templates import build_workflow_templates_block

    if getattr(sp.build_system_prompt_parts, "_overlay_wrapped", False):
        logger.debug("assistant-prompt-overlay: already wrapped, skipping")
        return

    _orig_build = sp.build_system_prompt_parts

    def _wrapped(agent: Any, system_message: Any = None):
        parts = _orig_build(agent, system_message)

        # Upstream changed return type from list to dict (3-tier:
        # stable / context / volatile) in 2026-05-30 release. Provide a
        # uniform ``_add(block)`` shim that appends to whichever
        # container we got — preserves backward compat if upstream
        # reverts.
        def _add(block: str) -> None:
            if not block:
                return
            if isinstance(parts, dict):
                # Append to volatile tier — least likely to invalidate
                # prompt cache; new dynamic blocks (identity, delegation
                # guidance) naturally belong with memory/profile.
                vol = parts.get("volatile")
                if isinstance(vol, list):
                    vol.append(block)
                elif isinstance(vol, str):
                    parts["volatile"] = vol + "\n\n" + block
                else:
                    parts["volatile"] = block
            else:
                parts.append(block)

        # Гермес-role gating: chief_spawn / mc_project_create present AND
        # terminal absent (operator-assistant, not a worker).
        valid_tools = getattr(agent, "valid_tool_names", None) or set()
        can_delegate = (
            "chief_spawn" in valid_tools
            or "mc_project_create" in valid_tools
        )
        is_operator_assistant = "terminal" not in valid_tools
        if can_delegate and is_operator_assistant:
            _add(ASSISTANT_DELEGATION_GUIDANCE)
            wf = build_workflow_templates_block()
            if wf:
                _add(wf)

        return parts

    _wrapped._overlay_wrapped = True  # type: ignore[attr-defined]
    sp.build_system_prompt_parts = _wrapped

    logger.info(
        "assistant-prompt-overlay: registered (prompt_builder constants "
        "replaced, build_system_prompt_parts wrapped)"
    )
