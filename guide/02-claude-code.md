# 02. Claude Code: 14 habits and settings

Source for most of this page: the official cost guide, <https://code.claude.com/docs/en/costs>, checked Nov 25, 2026. Command names and version notes change. Run `/help` to see what your version has.

## The big four (do these first)

### 1. `/clear` between unrelated tasks
Finished the login bug and now starting a docs task? Type `/clear`. It costs nothing, and the next message no longer carries the old story. If you may need the old thread later, name it first with `/rename` and bring it back with `/resume`.

### 2. Use the cheaper model for everyday work
Type `/model`. The docs say Sonnet handles most coding tasks well and costs less than Opus; keep Opus for complex design decisions and multi-step reasoning. You can set a default in `/config`. Heads up: switching to Opus also applies to helper agents that inherit your session's model.

### 3. Lower the thinking level for simple tasks
Type `/effort` (or pick it in `/model`) and choose a lower level for small jobs. The docs explain thinking is on by default and billed as output. Two honest notes from the docs: some models cannot have thinking turned off, and `MAX_THINKING_TOKENS=8000` (an environment variable) only works on models with a fixed thinking budget. Models with adaptive reasoning ignore it, so use effort levels there.

### 4. Check `/usage` once a week
It shows your plan limits and a Session block. The docs say the breakdown recommends a change for behaviors behind 10% or more of your recent usage, such as long context and cache misses. Type the key it shows to apply a recommendation. Those recommendations come from your own data, so they beat any generic list, including this one.

## Keep context small

### 5. Compact with a focus, and write "Compact instructions"
`/compact keep the failing test and the files we changed` tells the summary what matters. You can also add a short "Compact instructions" section to CLAUDE.md. See `templates/CLAUDE.lean.md`. Remember: compacting a big context is itself a big request. If you do not need the thread, `/clear` instead.

### 6. Keep CLAUDE.md short; move how-to steps into skills
CLAUDE.md loads at the start of every session. Skills load only when used. The docs say to aim for under 200 lines and keep only essentials. Run `python3 scripts/cost_audit.py .` to see yours. Details in [guide 05](05-instruction-file-diet.md).

### 7. Cut tool-server (MCP) overhead
The docs say tool definitions are deferred by default, so mostly names enter context until a tool is used. Still: run `/context` to see what takes space, run `/mcp` and switch off servers you are not using today, and prefer plain command-line tools (`gh`, `aws`, `gcloud`) when they exist, because they add no per-tool listing.

### 8. Trim noisy command output with a hook
A failing test run can print thousands of lines. A PreToolUse hook can rewrite the command so Claude sees only the last lines. The docs show the idea using `jq`. We ship a version in Python (`scripts/filter_test_output.py`) that also keeps the real exit code, so a failing test still looks like a failure. Setup:

1. Copy the script to `.claude/hooks/filter_test_output.py` in your project.
2. Merge the `hooks` block from `templates/claude-settings.cost.example.json` into `.claude/settings.json`.
3. Type `/hooks` to confirm it is listed under PreToolUse.
4. Ask Claude to run your tests. To see the rewrite, start with `claude --debug-file ./claude-debug.txt` and look for the line about modified tool input.

It only rewrites plain commands like `npm test`, `pytest`, `go test ./...`. Anything with a pipe, quotes or `&&` is left alone. Change the line count with `TBT_TAIL_LINES=60`.

### 9. Send noisy jobs to a helper agent
Running tests, reading docs or going through logs can fill the chat. The docs suggest handing such work to a subagent so only a summary comes back. The helper's own requests still use your allowance, so give simple helpers a smaller model: put `model: haiku` in the subagent's settings.

### 10. Hide folders Claude should never read
A `.claudeignore` file does nothing in Claude Code (the docs say so). Use deny rules in `.claude/settings.json` instead, like `Read(node_modules/**)`. `python3 scripts/make_ignore.py .` prints the lines for your project. Honest limit: these rules cover Claude's file tools, not every shell command.

## Ask in ways that cost less

### 11. Be specific, and use plan mode for big changes
"Improve this codebase" makes the agent scan everything. "Add input validation to the login function in auth.ts" does not. For larger work press Shift+Tab to reach plan mode so the approach is agreed before the expensive part. Press Escape the moment it heads the wrong way, and use `/rewind` (or double-tap Escape) to go back to a checkpoint.

### 12. Give it a way to check itself
Include the test to run, the expected output, or a screenshot. When the agent can verify its own work, fewer "that's wrong, try again" rounds happen. Our free Verify Before Done skill does this for you: https://tidybyte.gumroad.com/l/verify-before-done-free

## Quiet spending

### 13. Know what spends while you are away
The docs list these: a long session that stays open (every request carries the whole chat), the first message after a long break (cache miss), session-scoped scheduled tasks and loops that fire on a timer, messages from other sessions, goal check-ins while background work runs, helper agents, and agent teammates that stay active until they exit. Session recap, idle compaction and prompt suggestions can also use tokens in the background, and the docs say how to switch each off. To stop idle goal check-ins, set `CLAUDE_CODE_GOAL_CHECKIN_MINUTES` to `0`.

Agent teams are off by default. The docs say they use roughly 7 times more tokens than a normal session when teammates run in plan mode. Keep teams small and use Sonnet for teammates.

### 14. Start fresh after lunch
A session left open all day plus a cold cache means a big first request after you return. Write a handoff note (`templates/handoff-note.md`), `/clear`, and paste it. `python3 scripts/session_report.py --days 7` shows which of your sessions had many requests, huge context, or "cold restarts" after idle time.

---

Sources: <https://code.claude.com/docs/en/costs>, <https://code.claude.com/docs/en/permissions>, <https://code.claude.com/docs/en/model-config>.

Next: [03 Cursor](03-cursor.md)

Want your agent to run tests, scan for secrets and write the PR text the same way every time? The Ship-Ready Skills Pack has 10 tested skills: https://tidybyte.gumroad.com/l/ship-ready-skills-pack
