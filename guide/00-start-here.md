# 00. Start here: the 10-minute plan

Goal: spend fewer tokens without making your agent worse. Three steps. Measure, fix three things, measure again.

## Step 1. Measure (2 minutes)

Write down where you are now. Without a "before" number you cannot tell if a change helped.

- **Claude Code:** type `/usage`. It shows your plan limits and a Session block with token totals. On plans that show it, the breakdown also lists what drove your recent usage and recommends changes. (Claude Code docs: <https://code.claude.com/docs/en/costs>)
- **Cursor:** open your usage page in the dashboard for your plan.
- **Codex:** type `/status` in a session to see the current model, settings and usage. Your weekly or daily limit view is in the Codex usage page for your plan.
- **Your files:** run `python3 scripts/cost_audit.py .` in your project. It prints what is sent on every request, and a fix list.
- **Claude Code history:** run `python3 scripts/session_report.py --days 7` for token totals per session from your own logs.

## Step 2. Fix three things (6 minutes)

Pick these first. They are the biggest levers for most people, and they cost nothing.

1. **One task, one session.** Start a new chat (or `/clear` in Claude Code, `/new` in Codex) when the task changes. Old history is re-sent with every new message. Guide 01 explains why.
2. **Match the model and thinking level to the job.** Use the cheaper model and a lower effort level for everyday edits. Move up only when the task is hard. Guides 02, 03 and 04 show the exact commands.
3. **Shrink what loads every time.** Your instruction files, always-on rules and unused tool servers ride along on every request. The audit script finds them. Guide 05 shows how to cut them.

## Step 3. Measure again (2 minutes, one week later)

Look at the same screens and the same script. Did the numbers move? Keep what helped. Skip what did not. If your work is different from ours, your best list will be different too.

## Extra guard rails (do when you have time)

- Hide noise folders (`node_modules`, `dist`, build output) from file tools: `python3 scripts/make_ignore.py .`
- Keep test output short with the hook in `scripts/filter_test_output.py` (Claude Code).
- Turn off tool servers (MCP) you are not using today.
- Use plan mode for big changes so a wrong direction is caught before the expensive part.
- Write a handoff note (`templates/handoff-note.md`) before you clear a long chat, so a fresh one starts fast.

## A promise about numbers

You will not find a big "percent saved" headline in this pack. Nobody can promise that without seeing your work. Where we give a number (a line limit, a file size), it comes from the official docs, and we link them. Where it is a rule of thumb, we say so.

Next: [01 Why costs grow](01-why-costs-grow.md)

---
Want ready-made skills that make the agent check its own work, so you pay for fewer "try again" rounds? See the Ship-Ready Skills Pack: https://tidybyte.gumroad.com/l/ship-ready-skills-pack
