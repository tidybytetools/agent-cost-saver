# Agent Cost Saver

A free guide and four small scripts that help you spend fewer tokens with Claude Code, Cursor and Codex.

Most of the waste comes from a few habits and a few big files. This pack shows you which ones, then lets you measure before and after. It does not promise a percent saved. Nobody can, without seeing your work.

Facts in the guides were checked against the official docs on Nov 25, 2026. These tools change fast, so each guide links to its source. If a setting name here does not match your version, trust your version's docs and `/help`.

Also on Gumroad (same free pack): https://tidybyte.gumroad.com/l/agent-cost-saver

## Install

You need Python 3.8 or newer. Nothing else to install.

**As an agent skill** (asks your agent to run the audit for you):

```bash
npx skills add tidybytetools/agent-cost-saver
```

Or, in Claude Code:

```text
/plugin marketplace add tidybytetools/agent-cost-saver
/plugin install agent-cost-saver@tidybytetools-agent-cost-saver
```

Then ask: "Audit this project for token cost."

**As plain scripts and guides:**

```bash
git clone https://github.com/tidybytetools/agent-cost-saver.git
cd agent-cost-saver
python3 tests/test_cost_saver.py
```

That should print `73 passed, 0 failed`.

## Try it on the included demo

```bash
python3 scripts/cost_audit.py samples/demo-project
```

On the demo it reports about 9,186 tokens sent with every request if your tools read all of the instruction files, and flags a 225-line `CLAUDE.md` that repeats `AGENTS.md`. The saved output is in `samples/cost-audit-demo-output.txt`.

Then run the audit on your own project:

```bash
python3 scripts/cost_audit.py /path/to/your/project
```

Fix the top two findings. Read `guide/00-start-here.md` for the 10-minute plan, and keep `guide/07-cheat-sheet.md` as a one-page reminder.

## What is inside

| File | What it is |
|---|---|
| `guide/00-start-here.md` | The 10-minute plan: measure, fix three things, measure again |
| `guide/01-why-costs-grow.md` | Plain-words picture of where tokens go |
| `guide/02-claude-code.md` | 14 Claude Code habits and settings, with the exact commands |
| `guide/03-cursor.md` | 8 Cursor habits and settings |
| `guide/04-codex.md` | 9 Codex habits and settings |
| `guide/05-instruction-file-diet.md` | How to shrink CLAUDE.md, AGENTS.md and Cursor rules |
| `guide/06-prompts-that-cost-less.md` | Prompt patterns, plus a handoff note for fresh chats |
| `guide/07-cheat-sheet.md` | One page: "if this happens, do that" for all three tools |
| `scripts/cost_audit.py` | Scans a project for what is sent with every request. Prints fixes |
| `scripts/session_report.py` | Totals tokens per Claude Code session from your own local logs |
| `scripts/make_ignore.py` | Suggests a `.cursorignore` and Claude Code Read-deny rules |
| `scripts/filter_test_output.py` | A Claude Code hook that keeps test output short and keeps the exit code |
| `templates/` | Short CLAUDE.md and AGENTS.md files, a scoped Cursor rule, example settings, and a 15-line handoff note |
| `samples/` | A demo project and the audit output for it |
| `tests/test_cost_saver.py` | The tests |

## What this does not do

- It does not promise a saving. Measure before and after (guide 00).
- It does not know your prices. `session_report.py` only does dollars if you type your own rates.
- The scripts only read files, except `make_ignore.py --write`, which saves a `.cursorignore` and never overwrites one unless you say `--force`.
- Ignore rules cover the agent's file tools. They do not stop a shell command like `cat`. Do not use them as your only protection for secrets.

The hook also needs Claude Code and `bash`.

## Next step

If you want a set of agent skills, hooks and instruction files in one purchase, the [All Tidy Byte Agent Packs](https://tidybyte.gumroad.com/l/all-agent-packs) bundle is $19.

Website: https://tidybytetools.github.io/tools/agent-cost-saver/

MIT license. Made by Tidy Byte Tools.
