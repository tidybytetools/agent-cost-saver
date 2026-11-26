# 07. One-page cheat sheet

Facts checked Nov 25, 2026. Run `/help` (or `codex --help`) to see what your version has.

| If this happens... | Claude Code | Cursor | Codex |
|---|---|---|---|
| New, unrelated task | `/clear` | New chat | `/new` |
| Chat is long but you must keep it | `/compact <what to keep>` | Handoff note, then new chat | `/compact` |
| See what is using tokens | `/usage`, `/context` | Usage page in your dashboard | `/status`, `/usage` |
| Simple edit | `/model` to Sonnet, `/effort` lower | Auto (Cost mode) | Lower `model_reasoning_effort` |
| Hard problem | `/model` Opus, higher `/effort` | Pick a premium model for this task only | `/model`, higher effort |
| Big always-on instructions | Keep CLAUDE.md under 200 lines, use skills | `globs` or description on rules | Short AGENTS.md (cap 32 KiB), nested files |
| Noisy folders | `permissions.deny` with `Read(dir/**)` | `.cursorignore` | Keep them out of the project root instructions |
| Too many tool servers | `/mcp`, switch off unused | Turn off unused MCP tools | `enabled = false` |
| Huge test output | Hook: `filter_test_output.py` | "Show the last 20 lines" | `tool_output_token_limit` |
| Big change ahead | Plan mode (Shift+Tab) | Plan mode | `/plan` |
| Wrong direction | Escape, then `/rewind` | Stop the run | Interrupt, then `/new` if needed |
| Away from keyboard | Check timers and loops; cache goes cold | Fresh chat when you return | Fresh session when you return |

## The five-minute daily habit

1. New task, new chat.
2. Cheaper model by default.
3. Say where to look and how to check.
4. Plan before big edits.
5. Once a week: `/usage`, then `python3 scripts/cost_audit.py .`

## Scripts

```
python3 scripts/cost_audit.py .               # what loads on every request
python3 scripts/session_report.py --days 7    # Claude Code sessions: biggest first
python3 scripts/make_ignore.py .              # ignore rules for noisy folders
```

More from Tidy Byte Tools:
- Ship-Ready Skills Pack: https://tidybyte.gumroad.com/l/ship-ready-skills-pack
- AGENTS.md Starter Pack: https://tidybyte.gumroad.com/l/agents-md-starter-pack
- Free Verify Before Done skill: https://tidybyte.gumroad.com/l/verify-before-done-free
