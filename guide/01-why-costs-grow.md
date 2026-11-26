# 01. Why costs grow (plain words)

You do not need to be an expert to save tokens. You only need a picture of where they go.

## The picture

A chat with a coding agent is not a phone call. It is more like a letter that gets longer each time.

Each time you press enter, the tool sends the whole story so far: your instruction files, the tool list, every old message, every file it read, every command output. Then the model writes the next part. The Claude Code docs say it directly: it sends your full conversation with every request, and each time Claude uses tools it sends another request carrying that batch of tool results.

So these five things add up:

1. **Long chats.** A one-line question at the end of a long chat still carries the whole chat.
2. **Big always-on files.** Instruction files and always-on rules ride along on every request.
3. **Big tool output.** A test run that prints 5,000 lines puts 5,000 lines in the chat. They stay there.
4. **Thinking.** Extra reasoning is billed like output. Claude Code's docs say thinking tokens are billed as output tokens, and the default budget can be tens of thousands of tokens per request depending on the model.
5. **Helpers and background work.** Each helper agent has its own context and sends its own requests. Timers, loops and check-ins can start new turns even when you are away.

## Caching helps, but it times out

Tools use "prompt caching": repeated content (like the start of your chat) is read back at a cheaper rate. That is why long chats are not as bad as they could be. But the cache does not last forever.

- Claude Code's docs say that the first message after a break longer than the cache lifetime misses the cache and reprocesses the full context. They also list which lifetime your requests get; at the time we checked, a subscription sign-in and an API key were different, and background agents were shorter. Read the current table at <https://code.claude.com/docs/en/costs> because it can change.
- Cursor does not publish a cache time that we could find. So we do not give one. Treat a long break like a cold start.

Plain-words rule: **if you are coming back after a long break, a fresh session with a short handoff note is often cheaper than waking up a huge old one.** (Use `templates/handoff-note.md`.)

## Compacting is not free

`/compact` makes the agent summarize the chat so it gets smaller. But summarizing means reading the whole chat. The Claude Code docs say it plainly: compacting a large context is itself a large request. `/clear` costs nothing. Use `/clear` when the old chat is not needed. Use compact when you must keep the thread, and tell it what to keep (guide 02).

## What does not matter much

- Saying "please" and "thank you". Tiny.
- Short, clear questions. Cheap.
- Worrying about a single prompt. The cost is the pile, not the one line.

## How to see the pile

- Claude Code: `/context` shows what is using space. `/usage` shows token totals and what drove your usage.
- Anywhere: `python3 scripts/cost_audit.py .` shows the always-on files in your project.

Next: [02 Claude Code](02-claude-code.md)

---
Pair this with the AGENTS.md Starter Pack for short, tidy instruction files you can copy: https://tidybyte.gumroad.com/l/agents-md-starter-pack
