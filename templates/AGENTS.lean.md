# AGENTS.md (lean version)

Short on purpose. Codex, Cursor and other tools read this file on every task.

## Commands
- Install: `pnpm install`
- Test one file: `pnpm vitest run path/to/file.test.ts`
- Test all / types / lint: `pnpm test`, `pnpm tsc --noEmit`, `pnpm lint`

## Rules
- TypeScript strict. No `any`.
- Use the shared logger, not `console.log`.
- Add a test for every bug you fix.
- Never commit `.env` files.

## Done means
Tests, types and lint pass, and you show the command output before you say "done".

## Folder rules
Rules for one folder live in an AGENTS.md inside that folder (for example `src/ui/AGENTS.md`), so they load only when work happens there.
