#!/usr/bin/env python3
"""make_ignore.py - suggest ignore rules for noisy folders in your project.

Prints:
  1. a .cursorignore (gitignore style) for Cursor
  2. a snippet for .claude/settings.json (permissions.deny with Read rules) for Claude Code

Use --write to save .cursorignore (it will not overwrite an existing file unless you pass --force).
It never edits .claude/settings.json for you: merge the snippet yourself.

Honest limits: ignore files and Read deny rules cover the agent's file tools. They do not stop
a shell command like `cat`. Do not rely on them alone to protect secrets.
Python 3.8+, standard library only.
"""
import argparse
import json
import os
import sys

NOISE = ["node_modules", "dist", "build", ".next", ".nuxt", "out", "coverage", ".venv", "venv", "__pycache__",
         "target", "vendor", ".gradle", ".terraform", ".turbo", ".cache", "bower_components"]
SKIP = set(NOISE) | {".git", ".hg", ".svn"}
OPTIONAL = ["*.min.js", "*.min.css", "*.map", "*.log", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "*.csv"]
SECRETS = [".env", ".env.*", "*.pem", "*.key"]


def find_noise(root, max_depth=3):
    found = set()
    for dirpath, dirs, _ in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        keep = []
        for d in dirs:
            if d in NOISE and depth < max_depth:
                found.add(d)
            elif d not in SKIP:
                keep.append(d)
        dirs[:] = keep
    return sorted(found)


def build(root):
    noise = find_noise(root)
    lines = ["# Suggested by Agent Cost Saver. Edit before you use it.",
             "# Folders found in this project that an agent should not read:"]
    lines += [f"{n}/" for n in noise] or ["# (none found)"]
    lines += ["", "# Optional: generated and data files. Remove any line your agent needs to read."]
    lines += [f"# {p}" for p in OPTIONAL]
    lines += ["", "# Optional: keep secrets away from the agent's file tools."]
    lines += [f"# {p}" for p in SECRETS]
    deny = [f"Read({n}/**)" for n in noise]
    snippet = {"permissions": {"deny": deny}}
    return noise, "\n".join(lines) + "\n", snippet


def main(argv=None):
    ap = argparse.ArgumentParser(description="Suggest .cursorignore and Claude Read-deny rules.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--write", action="store_true", help="save .cursorignore in the project folder")
    ap.add_argument("--force", action="store_true", help="overwrite an existing .cursorignore")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.path):
        print(f"Not a folder: {a.path}", file=sys.stderr)
        return 2
    noise, cursor_text, snippet = build(a.path)
    print("=== .cursorignore ===")
    print(cursor_text)
    print("=== .claude/settings.json (merge this into your file) ===")
    print(json.dumps(snippet, indent=2))
    print("\nNote: a .claudeignore file has no effect in Claude Code. Use the deny rules above.")
    if a.write:
        dest = os.path.join(a.path, ".cursorignore")
        if os.path.exists(dest) and not a.force:
            print(f"\nSkipped: {dest} already exists (use --force to replace it).")
            return 0
        with open(dest, "w", encoding="utf-8") as f:
            f.write(cursor_text)
        print(f"\nWrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
