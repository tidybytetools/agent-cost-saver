# 05. The instruction-file diet

Your instruction files are the one thing you control that is sent on **every** request. A bloated one is a tax on every message you ever send.

## What loads where

| File | Read by | Loads |
|---|---|---|
| `CLAUDE.md` | Claude Code | Start of every session |
| `AGENTS.md` | Codex, Cursor, and other tools | Every task (Codex: root down to your folder, at most one file per folder, up to 32 KiB combined by default) |
| `.cursor/rules/*.mdc` | Cursor | By rule type: always, by file pattern, when the agent decides, or when you @-mention it |
| Skills (`.claude/skills/`) | Claude Code | Only when used (name and description are listed; the body loads on use) |

If you use both Claude Code and another tool, keep the real rules in `AGENTS.md` and make `CLAUDE.md` one line that imports it: `@AGENTS.md`. The audit script flags the case where both files repeat the same text.

## The rule of thumb

Ask of every line: **"Would the agent get this wrong without it, on most tasks?"** If not, delete it, or move it to the place that loads only when needed.

Keep:
- Commands: how to install, run one test, run all tests, type check, lint.
- Hard rules that were broken before ("never touch `generated/`").
- Where things live, in 3 to 6 lines.
- What "done" means (see our free Verify Before Done skill: https://tidybyte.gumroad.com/l/verify-before-done-free).
- A short "Compact instructions" note (Claude Code).

Move out:
- Long how-to workflows (release steps, migrations, PR review): make a skill. Skills load on demand.
- Rules for one folder: a nested `AGENTS.md` in that folder, or a Cursor rule with `globs`.
- History, meeting notes, old decisions: a `docs/` file the agent reads only when asked.
- Things the code already says: linters and formatters enforce style better than prose.
- Anything you copied from a blog post and never used.

## Size targets

These are our rules of thumb, except where marked as the docs' own number:

| Item | Target |
|---|---|
| `CLAUDE.md` | Under 200 lines (the Claude Code docs' own suggestion). Under 100 is better |
| Root `AGENTS.md` | Under 32 KiB (Codex's default cap, from its docs). Under 8 KiB is better |
| Always-on Cursor rules | A few lines in total. Everything else gets `globs` or a description |
| Tool servers (MCP) | Only the ones you use today |

## Try it on the demo

```
python3 scripts/cost_audit.py samples/demo-project
```

The demo has a 225-line CLAUDE.md with old meeting notes pasted in, an AGENTS.md that repeats it, an always-on Cursor rule, seven tool servers and a `.claudeignore` that does nothing. The audit flags all of it. Its saved output is in `samples/cost-audit-demo-output.txt`.

Now look at the lean versions in `templates/CLAUDE.lean.md` and `templates/AGENTS.lean.md`. They are under 40 lines each and still say the things that matter: commands, hard rules, what "done" means, where things live. The tests in this pack check that the lean templates pass the audit with no high or medium findings.

## A 15-minute diet

1. Run the audit on your project. Note the token guess.
2. Copy `CLAUDE.md` to a backup.
3. Delete everything the agent would get right without it.
4. Move each long workflow into its own skill or `docs/` file.
5. Put one-folder rules in that folder.
6. Run the audit again. Use your agent for a day. If it keeps missing something you cut, add back that one line.

Next: [06 Prompts that cost less](06-prompts-that-cost-less.md)

If you want skills ready to take over the long workflows (code review, release notes, PR text, secret scan): Ship-Ready Skills Pack, https://tidybyte.gumroad.com/l/ship-ready-skills-pack. For copy-paste AGENTS.md files: https://tidybyte.gumroad.com/l/agents-md-starter-pack
