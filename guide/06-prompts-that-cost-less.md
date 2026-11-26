# 06. Prompts that cost less

A good prompt is not about magic words. It is about telling the agent **where to look, what to change, and how to check**, so it does not wander.

## 8 patterns

**1. Name the place.**
Instead of: "Fix the login bug."
Try: "Login fails when the email has a plus sign. Look at `src/auth/login.ts` and its test."

**2. Name the finish line.**
Instead of: "Make it faster."
Try: "Make `parseRows` handle 100,000 rows in under 2 seconds. Show me the timing before and after."

**3. Give the check.**
"When you finish, run `pnpm test src/auth` and show the last 20 lines." The agent can then fix its own mistakes before you see them.

**4. Plan first, then build.**
"Do not edit anything yet. Tell me your plan in 5 bullets and which files you will touch." Approve or correct it. Then: "Go."

**5. Ask for small answers.**
"Show only the changed function, not the whole file." "Give me a diff." "Answer in 3 sentences."

**6. Set a stop rule.**
"If the test still fails after 3 attempts, stop and tell me what you tried." This avoids long loops that dig deeper into a wrong idea.

**7. Do not paste what a tool can read.**
Pasting a 2,000-line log puts it in the chat twice (once from you, once if the agent reads it). Tell the agent the path and the part you care about: "Read the last 100 lines of `logs/app.log`."

**8. One task per chat.**
When the task changes, start fresh. Carry the facts across with a handoff note.

## The handoff note

Before you `/clear`, `/new` or open a new chat, ask: "Write a handoff note under 15 lines using this template. Facts only." Then paste `templates/handoff-note.md`'s fields. The new chat starts small and still knows what matters.

## When a long chat is worth keeping

Keep one when the agent is holding a lot of hard-won understanding (a tangled bug, a design you just argued out). Then use the focused compact: in Claude Code, `/compact keep the root cause, the files changed and the failing test`. If you only need the result, take the handoff note and start fresh.

## What to avoid

- "Look through the whole repo and tell me what you think." Broad scans read many files. Ask about one area.
- Retrying the same prompt unchanged. If the answer was wrong, say what was wrong, or go back to a checkpoint (`/rewind` in Claude Code).
- Asking for the whole file back after a one-line change.

Next: [07 Cheat sheet](07-cheat-sheet.md)

Our free Verify Before Done skill makes the agent run your real checks before it says "done": https://tidybyte.gumroad.com/l/verify-before-done-free
