# 03. Cursor: 8 habits and settings

Sources: Cursor's official docs, checked Nov 25, 2026: rules <https://cursor.com/docs/context/rules>, ignore files <https://cursor.com/docs/context/ignore-files>, models and pricing <https://cursor.com/docs/models-and-pricing>. Cursor plans and usage rules change often. Look at your own plan's usage page before you trust any general advice, including ours.

### 1. New chat per task
Each message carries the chat so far. A fresh chat starts small. Open a new one when the task changes, and when you come back after a long break. Cursor does not publish how long its prompt cache lasts, so we do not claim a number. Use `templates/handoff-note.md` to carry the key facts across.

### 2. Pick the model on purpose
Cursor's pricing page says Auto has three modes: Cost, Balance and Intelligence. Cost mode bills as a Cursor-model request and draws from your weekly pool whatever model serves it, and individual plans have Cost mode only. Third-party models, on the plans that allow them, are billed at the model's API list price. So the cheap habit is simple: let Auto do routine edits, and pick a named premium model only for the hard task, then switch back. Your plan's page has the exact rules.

### 3. Do not reach for Max Mode by habit
Cursor's docs say Max Mode extends a model's context window beyond the default limit, is available only on legacy request-based plans, and is billed at the model's API rate plus 20%. A bigger window also means a bigger pile re-sent on each message. Use it only when one task truly needs that much in view.

### 4. Write a `.cursorignore`
Put noisy folders in `.cursorignore` (gitignore syntax) so they do not get indexed or pulled into context: `node_modules/`, `dist/`, build output, big data files. `python3 scripts/make_ignore.py .` prints a starting file for your project. Honest limit from Cursor's docs: the terminal and MCP server tools used by Agent cannot block access to code governed by `.cursorignore`, and Cursor says complete protection is not guaranteed. Do not treat it as a secret vault.

### 5. Make rules load only when needed
Cursor rules live in `.cursor/rules` and must end in `.mdc`. A plain `.md` file there is ignored. Each rule has a type:

| Type | Frontmatter | Loads |
|---|---|---|
| Always Apply | `alwaysApply: true` | In every chat |
| Apply to Specific Files | `globs: src/ui/**/*.tsx` | When a matching file is in context |
| Apply Intelligently | `description: ...` | When the agent decides it is relevant |
| Apply Manually | neither | Only when you @-mention it |

Keep "Always Apply" for a few lines that truly apply everywhere. Everything else gets globs or a description. See `templates/cursor-rule-scoped.mdc`. The audit script adds up your always-on rules.

### 6. Use nested AGENTS.md for folder rules
Cursor's docs say an `AGENTS.md` inside a subfolder applies when you work in that folder, and more specific files win. Put UI rules in `src/ui/AGENTS.md` and keep the root file short. Our AGENTS.md Starter Pack has tidy files to copy: https://tidybyte.gumroad.com/l/agents-md-starter-pack

### 7. Plan first for big changes
Use Plan mode (or ask for a plan and no code) so you approve the direction before the agent edits many files. Stop a run early if it is going the wrong way. A wrong 20-file edit costs more than a one-minute plan.

### 8. Point at files, ask for small answers
`@file` the exact file instead of "find the bug somewhere". Ask for "only the changed function" instead of the whole file back. Add the check to run ("then run `npm test` and show the last 20 lines").

---

Next: [04 Codex](04-codex.md)
