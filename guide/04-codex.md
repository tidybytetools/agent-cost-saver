# 04. Codex: 9 habits and settings

Sources: OpenAI's Codex docs, <https://developers.openai.com/codex/> (config, commands, AGENTS.md pages), checked Nov 25, 2026. Setting names and defaults change between versions. Run `codex --help` and check the docs for your version before you rely on a line here.

### 1. Check where you stand
Type `/status` in a session for the active model, settings, token usage and remaining context. `/usage` shows your account's token use (daily, weekly or total).

### 2. Lower the reasoning effort for everyday work
In `~/.codex/config.toml` (or `.codex/config.toml` inside one project) set `model_reasoning_effort`. A lower level is faster and uses less. Raise it with `/model` for hard problems. The levels you can pick depend on the model. See `templates/codex-config.example.toml`.

### 3. New task, new session
Use `/new` when the task changes. Use `/compact` when you must keep the thread but it got long. As with every tool, compacting reads the whole conversation, so a fresh start is cheaper when you do not need the history. You can also set `model_auto_compact_token_limit` to compact earlier (a commented example is in the template; pick your own number).

### 4. Keep AGENTS.md short
Codex reads AGENTS.md files before it starts work. The docs say it stops adding files once the combined size reaches `project_doc_max_bytes` (32 KiB by default), and suggest splitting instructions across nested folders when you hit the cap. Short files are cheaper and more likely to be read in full. The audit script flags a root AGENTS.md over 32,768 bytes. Details in [guide 05](05-instruction-file-diet.md).

### 5. Put folder rules in folder files
Per the docs, Codex starts at the project root and walks down to your current folder, using at most one file per folder (an `AGENTS.override.md` wins over `AGENTS.md` in the same folder). Put rules for `src/ui/` in `src/ui/AGENTS.md`, so they only load when the work happens there.

### 6. Turn off tool servers you are not using
For each MCP server in your config you can add `enabled = false` to keep the definition but stop loading it. Turn servers on only for the days you need them. The audit script lists what is on.

### 7. Cap huge tool output
A setting `tool_output_token_limit` limits how many tokens of each tool's output are kept. A commented example is in the template. Set a number that fits your work, and test that it does not cut things you need.

### 8. Use fast mode on purpose
`/fast` turns on a faster service tier, when the model offers one (type `/fast` again to turn it off). Faster tiers can be counted or priced differently on your plan, so check your usage page before you leave it on. Use it when time matters, not by default.

### 9. Use two profiles: cheap and deep
Codex supports profiles (`codex --profile name`). Keep a `cheap` profile with medium or low effort for daily work, and a `deep` one for hard problems. You choose per task, and nothing stays on by accident.

---

Next: [05 The instruction-file diet](05-instruction-file-diet.md)

If your team uses several agents, a shared AGENTS.md is the simplest start. See the AGENTS.md Starter Pack: https://tidybyte.gumroad.com/l/agents-md-starter-pack
