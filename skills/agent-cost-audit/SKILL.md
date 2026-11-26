---
name: agent-cost-audit
description: Use when asked why Claude Code, Cursor or Codex is using too many tokens, to audit CLAUDE.md, AGENTS.md, Cursor rules or MCP servers for size, or to cut context cost. Runs a read-only audit script and lists the fixes in order.
license: MIT
---

# Agent cost audit

Find what your agent loads before you type a word, then fix the biggest items first.

## Steps

1. Run the audit on the project folder. It only reads files and never changes anything:

   ```bash
   python3 scripts/cost_audit.py .
   ```

   Run it from this skill's folder, or give the full path to `scripts/cost_audit.py`.
2. Show the user the findings in the order the script printed them (HIGH, then MED, then INFO). Say that token numbers are rough guesses (characters divided by 4).
3. For each HIGH and MED finding, give the one-line fix the script printed. Do not edit the user's files unless they ask.
4. If the script says `.claudeignore` does nothing or suggests ignore rules, offer to run `python3 scripts/make_ignore.py .` to print a suggested `.cursorignore` and Claude Code Read-deny rules. Only add `--write` if the user says yes. That saves a `.cursorignore` and never overwrites an existing one unless `--force` is given.
5. Tell the user to measure before and after. Do not promise a percent saved.

## Limits

- Counts are estimates, not billing numbers.
- Ignore rules cover the agent's file tools. They do not stop a shell command like `cat`, so do not rely on them to protect secrets.
- The full guide for Claude Code, Cursor and Codex is in the repository's `guide/` folder.
