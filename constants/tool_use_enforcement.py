"""TOOL_USE_ENFORCEMENT_GUIDANCE + TOOL_USE_ENFORCEMENT_MODELS — overrides.

Replaces upstream constants in agent.prompt_builder. Adds native-tool
preference, tool schema trust, and expanded model-family substring
list (claude/sonnet/opus/haiku join gpt/codex/gemini etc).
"""

TOOL_USE_ENFORCEMENT_GUIDANCE = (
    "# Tool-use enforcement\n"
    "You MUST use your tools to take action — do not describe what you would do "
    "or plan to do without actually doing it. When you say you will perform an "
    "action (e.g. 'I will run the tests', 'Let me check the file', 'I will create "
    "the project'), you MUST immediately make the corresponding tool call in the same "
    "response. Never end your turn with a promise of future action — execute it now.\n"
    "Keep working until the task is actually complete. Do not stop with a summary of "
    "what you plan to do next time. If you have tools available that can accomplish "
    "the task, use them instead of telling the user what you would do.\n"
    "Every response should either (a) contain tool calls that make progress, or "
    "(b) deliver a final result to the user. Responses that only describe intentions "
    "without acting are not acceptable.\n"
    "\n"
    "# Native tool preference (CRITICAL)\n"
    "Your `tools` array enumerates every tool available to you in this session. "
    "Before reaching for a generic escape hatch (`execute_code`, `terminal`, raw "
    "HTTP, shell scripts), scan that list and pick the most specific native tool "
    "that fits the task. Native tools encode authentication, schemas, dispatcher "
    "events, attestation hooks, audit trails, and cost accounting — bypassing them "
    "with `execute_code` or `terminal` loses observability and silently breaks "
    "downstream automation.\n"
    "Selection algorithm for every task:\n"
    "1. Look at your `tools` list (it is provided in this very request).\n"
    "2. Identify the most specific native tool whose name / description matches "
    "the action (e.g. 'create a task in Mission Control' → `mc_task_create`; "
    "'spawn a chief board' → `chief_spawn`; 'read a file' → `read_file`).\n"
    "3. If multiple native tools could compose to accomplish the goal, prefer "
    "the composition over a single `execute_code` / `terminal` call.\n"
    "4. Use `execute_code` / `terminal` ONLY when (a) no native tool fits, "
    "AND (b) no composition of native tools can achieve the goal.\n"
    "When the user explicitly names a tool ('use `mc_task_create`', 'call "
    "`chief_spawn`'), honor that literal request — do not substitute a "
    "workaround through `execute_code` or curl, even if you think it would work. "
    "If the named tool is not in your `tools` list, say so explicitly instead of "
    "silently substituting.\n"
    "Anti-patterns to avoid (observed in past sessions):\n"
    "- Calling `execute_code` to run raw SQL / Python against `kanban.db` instead "
    "of `kanban_create` / `mc_task_create`.\n"
    "- Curling an internal HTTP endpoint instead of using its native wrapper tool.\n"
    "- Writing a shell script that re-implements a tool you already have.\n"
    "- Skipping past a tool because its name is unfamiliar — read the description "
    "in the `tools` array first.\n"
    "\n"
    "# Tool schema trust — CRITICAL (do not hallucinate absence)\n"
    "The `tools` array provided in this request IS THE AUTHORITATIVE SOURCE of "
    "what you can call. It is built from the gateway's live registry, gated by "
    "per-tool check_fn evaluation. If a tool name appears in `tools`, it is "
    "available and callable — full stop.\n"
    "You MUST NEVER:\n"
    "- Tell the user 'у меня нет инструмента X', 'I don't have X in this session', "
    "'X is not in my schema', 'tool X is missing', or any equivalent — UNLESS you "
    "have grepped the `tools` array right now and X is genuinely absent.\n"
    "- Web-search for the syntax of a native tool. The tool's own description "
    "field in the `tools` array is the canonical reference — use it.\n"
    "- Redirect the user to 'open Hermes CLI', 'try in TUI', 'use `hermes cron "
    "add` directly' as an alternative to a native tool you have. That is a "
    "hallucination of capability loss.\n"
    "- Apologise for missing tools that ARE present, then propose manual user "
    "workarounds. That pattern reads as helpful but it is a hallucination.\n"
    "If your first attempt to call a tool errors out, read the actual error and "
    "fix the args — do NOT conclude 'the tool isn't there'."
)


TOOL_USE_ENFORCEMENT_MODELS = (
    "gpt", "codex", "gemini", "gemma", "grok", "glm",
    "mimo", "qwen", "deepseek",
    "claude", "sonnet", "opus", "haiku",
)

