# Project rules (lean version)

<!-- Keep this file short. It is sent with every session. Aim for under 100 lines. -->

## Commands
- Install: `pnpm install`
- Test one file: `pnpm vitest run path/to/file.test.ts`
- Test all: `pnpm test`
- Type check: `pnpm tsc --noEmit`
- Lint: `pnpm lint`

## Rules that matter
- TypeScript strict. No `any`.
- Use the shared logger, not `console.log`.
- Add a test for every bug you fix.
- Never commit `.env` files.

## Done means
Before you say a task is done: tests pass, types pass, lint passes, and you have shown me the output.

## Where things live
- `src/api/` HTTP handlers. `src/db/` queries. `src/ui/` components.
- Big workflows (releases, migrations) are skills in `.claude/skills/`. Do not paste them here.

## Compact instructions
When you compact, keep: the goal, the files we changed, failing tests and their errors, and the decisions we made. Drop: old file dumps and long command output.
