#!/usr/bin/env python3
"""cost_audit.py - what does your AI coding agent load before you type a word?

Scans a project for the things that get sent with EVERY request:
instruction files (CLAUDE.md, AGENTS.md), Cursor rules that always apply,
MCP servers, and big noisy folders and files that are not ignored.
Prints a short list of fixes. Python 3.8+, standard library only.
It only reads files. It never changes anything.

Token numbers are rough guesses (characters divided by 4). Real counts differ.

Usage:
  python3 cost_audit.py [PROJECT_DIR] [--json] [--fail-on high]
"""
import argparse
import fnmatch
import json
import os
import re
import sys

NOISE_DIRS = ["node_modules", "dist", "build", ".next", ".nuxt", "out", "coverage", ".venv", "venv",
              "__pycache__", "target", "vendor", ".gradle", ".terraform", ".turbo", ".cache", "bower_components"]
SKIP_WALK = set(NOISE_DIRS) | {".git", ".hg", ".svn", ".idea", ".vscode"}
INSTR_NAMES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md")
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".svg", ".woff", ".woff2", ".ttf", ".pdf", ".zip",
            ".gz", ".tar", ".mp4", ".mov", ".mp3", ".wav", ".so", ".dll", ".exe", ".bin", ".pyc", ".class", ".jar"}
MAX_DEPTH_NOISE = 3
MAX_FILES = 200000


def est_tokens(text):
    return (len(text) + 3) // 4


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def walk(root, big_kb):
    """Return instruction files, mdc rules, noise dirs (not entered), big files."""
    instr, rules, noise, big = [], [], [], []
    count = 0
    for dirpath, dirs, files in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        keep = []
        for d in dirs:
            if d in NOISE_DIRS:
                if depth < MAX_DEPTH_NOISE:
                    noise.append(os.path.normpath(os.path.join(rel_dir, d)))
                continue
            if d in SKIP_WALK:
                continue
            keep.append(d)
        dirs[:] = keep
        for fn in files:
            count += 1
            if count > MAX_FILES:
                return instr, rules, noise, big
            full = os.path.join(dirpath, fn)
            rel = os.path.normpath(os.path.join(rel_dir, fn))
            if fn in INSTR_NAMES:
                instr.append(rel)
            if rel.replace(os.sep, "/").find(".cursor/rules/") >= 0 and fn.endswith((".mdc", ".md")):
                rules.append(rel)
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_EXT:
                continue
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            if size >= big_kb * 1024:
                big.append((rel, size))
    big.sort(key=lambda x: -x[1])
    return instr, rules, sorted(set(noise)), big


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^\s*([A-Za-z_]+)\s*:\s*(.*?)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip("\"'")
    return out


def norm_lines(text):
    return {re.sub(r"\s+", " ", l.strip().lower()) for l in text.splitlines() if len(l.strip()) > 12}


def load_cursorignore(root):
    pats = []
    for line in read_text(os.path.join(root, ".cursorignore")).splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            pats.append(line)
    return pats


def load_claude_denies(root):
    pats = []
    for name in ("settings.json", "settings.local.json"):
        raw = read_text(os.path.join(root, ".claude", name))
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        for rule in ((data.get("permissions") or {}).get("deny") or []):
            m = re.match(r"^Read\((.*)\)$", str(rule))
            if m:
                pats.append(m.group(1))
    return pats


def covered(path, patterns):
    """Rough check: does any ignore pattern name this folder or file?"""
    p = path.replace(os.sep, "/").strip("/")
    base = p.rsplit("/", 1)[-1]
    for pat in patterns:
        q = pat.strip().lstrip("./").lstrip("/")
        q = re.sub(r"(/\*\*|/\*|/)$", "", q)
        q = q.lstrip("*/") if q.startswith("**/") else q
        if q in (p, base):
            return True
        if fnmatch.fnmatch(p, q) or fnmatch.fnmatch(base, q):
            return True
    return False


def mcp_servers(root):
    found = []  # (file, name, enabled)
    for rel in (".mcp.json", os.path.join(".cursor", "mcp.json")):
        raw = read_text(os.path.join(root, rel))
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        for name, cfg in (data.get("mcpServers") or {}).items():
            disabled = isinstance(cfg, dict) and cfg.get("disabled") is True
            found.append((rel, name, not disabled))
    toml_path = os.path.join(".codex", "config.toml")
    section, cur_enabled = None, True
    lines = read_text(os.path.join(root, toml_path)).splitlines()
    for line in lines + ["[end]"]:
        m = re.match(r"^\s*\[mcp_servers\.([^\].]+)\]\s*$", line)
        if m or re.match(r"^\s*\[", line):
            if section:
                found.append((toml_path, section, cur_enabled))
            section = m.group(1).strip('"') if m else None
            cur_enabled = True
            continue
        if section and re.match(r"^\s*enabled\s*=\s*false\b", line):
            cur_enabled = False
    return found


def audit(root, big_kb=200):
    shown = root
    root = os.path.abspath(root)
    instr, rules, noise, big = walk(root, big_kb)
    findings = []
    sizes = {}

    def add(level, title, detail, fix):
        findings.append({"level": level, "title": title, "detail": detail, "fix": fix})

    root_texts = {}
    for rel in sorted(instr):
        text = read_text(os.path.join(root, rel))
        lines = len(text.splitlines())
        sizes[rel] = {"lines": lines, "bytes": len(text.encode("utf-8", "replace")), "tokens": est_tokens(text)}
        if os.path.dirname(rel) == "":
            root_texts[rel] = text
        if os.path.basename(rel) in ("CLAUDE.md", "CLAUDE.local.md") and lines > 200:
            add("MED", f"{rel} is {lines} lines (about {est_tokens(text):,} tokens)",
                "Claude Code loads it at the start of every session. Its docs suggest keeping CLAUDE.md under 200 lines.",
                "Keep commands and hard rules. Move workflow steps into skills or sub-folder files. See guide/05.")
        elif sizes[rel]["tokens"] > 4000:
            add("MED", f"{rel} is big: about {sizes[rel]['tokens']:,} tokens",
                "Every line is sent with every request, whether or not the task needs it.",
                "Cut it to commands, rules, and the 'before you say done' list. See guide/05.")
        if os.path.basename(rel) == "AGENTS.md" and sizes[rel]["bytes"] > 32768:
            add("HIGH", f"{rel} is {sizes[rel]['bytes']:,} bytes",
                "Codex stops adding AGENTS.md files once the combined size reaches project_doc_max_bytes (32 KiB by default). The rest is left out.",
                "Shrink it, or put folder rules in AGENTS.md files inside those folders.")

    if "CLAUDE.md" in root_texts and "AGENTS.md" in root_texts:
        a, b = norm_lines(root_texts["CLAUDE.md"]), norm_lines(root_texts["AGENTS.md"])
        small = min(len(a), len(b))
        same = len(a & b)
        if small and same / small >= 0.6:
            add("HIGH", "CLAUDE.md and AGENTS.md repeat the same text",
                f"{same} of {small} lines match. A tool that reads both pays for the text twice.",
                "Keep the rules in AGENTS.md and make CLAUDE.md one line: @AGENTS.md")

    if os.path.exists(os.path.join(root, ".claudeignore")):
        add("MED", ".claudeignore does nothing in Claude Code",
            "Claude Code's docs say a .claudeignore file has no effect.",
            "Move its lines into permissions.deny as Read(...) rules. Run scripts/make_ignore.py to get the snippet.")

    always_tokens, always_files = 0, []
    for rel in sorted(rules):
        text = read_text(os.path.join(root, rel))
        if rel.endswith(".md"):
            add("INFO", f"{rel} is ignored by Cursor", "Project rules must end in .mdc. A plain .md file in .cursor/rules is ignored.",
                "Rename it to .mdc, or move the text into AGENTS.md.")
            continue
        fm = frontmatter(text)
        t = est_tokens(text)
        sizes[rel] = {"lines": len(text.splitlines()), "bytes": len(text.encode("utf-8", "replace")), "tokens": t,
                      "alwaysApply": fm.get("alwaysApply", "false").lower() == "true"}
        if sizes[rel]["alwaysApply"]:
            always_tokens += t
            always_files.append((rel, t))
    if always_tokens > 1500:
        names = ", ".join(f"{r} (~{t:,})" for r, t in always_files[:5])
        add("MED", f"Cursor rules that always apply: about {always_tokens:,} tokens",
            f"Rules with alwaysApply: true go into every chat. {names}",
            "Give each rule globs (apply to matching files) or a description (Agent decides), and keep only a few lines always on.")
    if os.path.exists(os.path.join(root, ".cursorrules")):
        add("INFO", ".cursorrules is the old rules format", "It still loads in some versions and costs tokens every chat.",
            "Move the content into AGENTS.md or .cursor/rules/*.mdc with globs.")

    ign = load_cursorignore(root) + load_claude_denies(root)
    missing = [n for n in noise if not covered(n, ign)]
    if missing:
        add("MED", f"{len(missing)} noisy folder(s) not named in .cursorignore or a Claude Read-deny rule",
            ", ".join(missing[:8]) + (" ..." if len(missing) > 8 else "") +
            ". If they are already in .gitignore, many tools skip them. Check your tool.",
            "Run scripts/make_ignore.py. It prints a .cursorignore and a Claude settings snippet.")
    big_missing = [(p, s) for p, s in big if not covered(p, ign)][:5]
    if big_missing:
        add("INFO", f"{len(big_missing)} big file(s) an agent could read by accident",
            ", ".join(f"{p} ({s // 1024} KB)" for p, s in big_missing),
            "Ignore generated, log, minified and data files you never want read. Ask for 'the first 50 lines' instead of the whole file.")

    servers = mcp_servers(root)
    on = [s for s in servers if s[2]]
    if len(on) >= 6:
        add("MED", f"{len(on)} MCP servers are switched on in this project",
            ", ".join(f"{n}" for _, n, _ in on[:8]),
            "Every server adds tool names to context. Turn off the ones you are not using right now (/mcp in Claude Code, enabled = false in Codex).")
    elif servers:
        add("INFO", f"{len(on)} MCP server(s) on, {len(servers) - len(on)} off", ", ".join(n for _, n, _ in servers[:8]),
            "Prefer a plain CLI tool (gh, aws, ...) when one exists. Turn off servers you do not need today.")

    hook_ok = False
    for name in ("settings.json", "settings.local.json"):
        raw = read_text(os.path.join(root, ".claude", name))
        if "PreToolUse" in raw and ("tail" in raw or "filter" in raw):
            hook_ok = True
    if not hook_ok:
        add("INFO", "No test-output filter hook found for Claude Code",
            "Without one, a failing test run can dump thousands of lines into context.",
            "Optional: copy scripts/filter_test_output.py and templates/claude-settings.cost.example.json.")

    root_always = sum(sizes[r]["tokens"] for r in sizes if os.path.dirname(r) == "" and os.path.basename(r) in INSTR_NAMES)
    summary = {
        "root": shown,
        "always_loaded_tokens_estimate": root_always + always_tokens,
        "instruction_files": {k: v for k, v in sizes.items() if os.path.basename(k) in INSTR_NAMES},
        "cursor_always_apply_tokens": always_tokens,
        "noise_dirs": noise,
        "mcp_servers": [{"file": f, "name": n, "enabled": e} for f, n, e in servers],
    }
    order = {"HIGH": 0, "MED": 1, "INFO": 2}
    findings.sort(key=lambda f: order[f["level"]])
    return summary, findings


def render(summary, findings):
    out = []
    out.append(f"Agent Cost Saver - audit of {summary['root']}")
    out.append("")
    out.append(f"Sent with every request if your tools read all of these (rough guess): up to about {summary['always_loaded_tokens_estimate']:,} tokens")
    for k, v in sorted(summary["instruction_files"].items()):
        out.append(f"  {k}: {v['lines']} lines, about {v['tokens']:,} tokens")
    if summary["cursor_always_apply_tokens"]:
        out.append(f"  Cursor always-apply rules: about {summary['cursor_always_apply_tokens']:,} tokens")
    out.append("")
    if not findings:
        out.append("Nothing to fix. Your always-loaded files and ignore lists look fine.")
    for f in findings:
        out.append(f"[{f['level']}] {f['title']}")
        out.append(f"   Why: {f['detail']}")
        out.append(f"   Fix: {f['fix']}")
        out.append("")
    high = sum(1 for f in findings if f["level"] == "HIGH")
    med = sum(1 for f in findings if f["level"] == "MED")
    out.append(f"{high} high, {med} medium, {len(findings) - high - med} info. Token numbers are rough (characters / 4).")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit what your AI coding agent loads on every request.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    ap.add_argument("--big-kb", type=int, default=200, help="list files at least this big (default 200)")
    ap.add_argument("--fail-on", choices=["high", "med"], help="exit 1 if a finding of this level or worse exists")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.path):
        print(f"Not a folder: {a.path}", file=sys.stderr)
        return 2
    summary, findings = audit(a.path, a.big_kb)
    if a.json:
        print(json.dumps({"summary": summary, "findings": findings}, indent=2))
    else:
        print(render(summary, findings))
    if a.fail_on:
        bad = {"HIGH"} if a.fail_on == "high" else {"HIGH", "MED"}
        if any(f["level"] in bad for f in findings):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
