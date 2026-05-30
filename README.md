# hermes-plugin-assistant-prompt-overlay

External Hermes plugin (loaded at gateway/agent startup) — applies our
Гермес-role system-prompt customizations on top of upstream
`agent.prompt_builder` and `agent.system_prompt`.

## About

The default system prompt assembled by upstream Hermes is generic. Our
operator-assistant profile (the "Гермес" personal assistant role) needs
several behavioural overlays:

- a 6-question pre-step that forces clarification before delegation
- expanded native-tool preference (claude/sonnet/opus added to the
  enforcement model-family list)
- KANBAN_GUIDANCE that maps explicit verbs to `kanban_*` / `chief_*` /
  `mc_*` tools (no more `execute_code` + raw `sqlite3` shortcuts)
- live infrastructure injections — current model/provider, Google creds
  state, workflow-template inventory — read fresh on every prompt build
- ASSISTANT_DELEGATION_GUIDANCE (the big "you are Гермес, delegate to
  Тимлид, control don't execute" block)

Previously these lived inline in our fork of `agent/prompt_builder.py`
and `agent/system_prompt.py` (≈1280 lines of customizations). This
plugin externalises them so the fork stays clean against upstream.

## Use

Add to the gateway/agent plugin search path. Activate via
`plugins.enabled` in `config.yaml`:

```yaml
plugins:
  enabled:
    - assistant-prompt-overlay
```

The plugin's `register()` runs at startup. It:

1. Replaces module-level constants in `agent.prompt_builder`
   (`KANBAN_GUIDANCE`, `TOOL_USE_ENFORCEMENT_GUIDANCE`,
   `TOOL_USE_ENFORCEMENT_MODELS`, `ASSISTANT_DELEGATION_GUIDANCE`)
   and blanks `TASK_COMPLETION_GUIDANCE` (the new enforcement block
   covers the same ground).
2. Wraps `agent.system_prompt.build_system_prompt_parts` to append
   four extra sections **only when the profile is the
   operator-assistant** (`chief_spawn` or `mc_project_create` present
   AND `terminal` absent):
   - ACTIVE RUNTIME identity (authoritative model/provider line)
   - ASSISTANT_DELEGATION_GUIDANCE (the Гермес-role block)
   - GOOGLE CREDS live state (read from
     `/opt/data/.google-creds-state.json`)
   - WORKFLOW TEMPLATES live inventory (scanned from
     `/opt/hermes-workflows/`)

Worker profiles (which have `terminal`) get only the upstream prompt +
the replaced constants — no overlay injection.

## Mounting

```yaml
# docker-compose.hermes-core.yml
volumes:
  - ./sources/hermes-external-plugins/assistant-prompt-overlay:/opt/data/plugins/assistant-prompt-overlay:ro
```

## Why

- `agent/prompt_builder.py` in our fork carried ~1059 lines of additions
  over upstream — every upstream merge needed careful per-hunk review.
  After this extraction the fork file is upstream-pristine.
- The wrapper pattern makes the overlay swappable per profile / per
  deployment without recompiling Hermes.
- Live config injections (Google creds, workflow templates) are now
  testable in isolation against the plugin without spinning up the
  gateway.

## Plugin layout

```
hermes-plugin-assistant-prompt-overlay/
├── __init__.py                          # register() — applies all patches
├── plugin.yaml                          # name, kind, version, repo
├── LICENSE                              # MIT
├── README.md                            # this file
├── constants/
│   ├── __init__.py
│   ├── assistant_delegation.py          # ASSISTANT_DELEGATION_GUIDANCE
│   ├── kanban_guidance.py               # replacement KANBAN_GUIDANCE
│   └── tool_use_enforcement.py          # replacement enforcement constants
└── overlays/
    ├── __init__.py
    ├── runtime_identity.py              # build_runtime_identity_line(agent)
    ├── google_creds.py                  # build_google_creds_block()
    └── workflow_templates.py            # build_workflow_templates_block()
```
