# Agent definitions (the real copy)

One Markdown file per agent: `<agent-name>.md`. `uv run .agents/sync_agents.py` turns each file into `.claude/agents/<name>.md`, whose body is the Claude Code subagent's system prompt. There are no project agents yet; reviewer agents come from Skill Central.

## Format

```markdown
---
name: docs-checker               # required; lowercase kebab-case; must match the file name
description: >-                  # required; when to delegate to this agent
  Checks that the docs match the code. Use when ...

# Optional Claude Code block. Keys are copied verbatim into the generated file.
claude:
  tools: Read, Grep, Glob
  model: inherit
---

Instructions for the agent, in Markdown: its role, inputs, and the output it must produce.
```

Check field names against the current Claude Code subagent docs; the generator does not validate harness-specific keys. `copilot` and `codex` blocks are accepted but ignored until those harnesses are added to `ENABLED_HARNESSES` in `sync_agents.py`.

Never edit the generated files. They carry a "generated" header and are overwritten or deleted by the sync.
