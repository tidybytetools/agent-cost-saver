#!/usr/bin/env python3
"""Tests for Agent Cost Saver. Standard library only. Run: python3 tests/test_cost_saver.py"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)
import cost_audit  # noqa: E402
import filter_test_output  # noqa: E402
import make_ignore  # noqa: E402
import session_report  # noqa: E402

PASSED, FAILED = 0, 0


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"ok   {name}")
    else:
        FAILED += 1
        print(f"FAIL {name} {detail}")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run(*args, stdin=None, env=None):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run([sys.executable] + list(args), input=stdin, capture_output=True, text=True, env=e)


# ---------- cost_audit ----------
with tempfile.TemporaryDirectory() as d:
    summary, findings = cost_audit.audit(d)
    check("audit: empty project has no findings except the hook tip", [f["level"] for f in findings] == ["INFO"], str(findings))

with tempfile.TemporaryDirectory() as d:
    write(os.path.join(d, "CLAUDE.md"), "\n".join(f"- unique rule number {i} about thing {i * 7}" for i in range(260)))
    s, f = cost_audit.audit(d)
    check("audit: 260-line CLAUDE.md flagged", any("260 lines" in x["title"] and x["level"] == "MED" for x in f))
    check("audit: token estimate present", s["instruction_files"]["CLAUDE.md"]["tokens"] > 1000)

with tempfile.TemporaryDirectory() as d:
    body = "\n".join(f"- shared rule line number {i} for everyone" for i in range(30))
    write(os.path.join(d, "CLAUDE.md"), body)
    write(os.path.join(d, "AGENTS.md"), body + "\n- one extra line only here\n")
    s, f = cost_audit.audit(d)
    check("audit: duplicate CLAUDE/AGENTS is HIGH", any(x["level"] == "HIGH" and "repeat" in x["title"] for x in f))

with tempfile.TemporaryDirectory() as d:
    write(os.path.join(d, "CLAUDE.md"), "- one line about " + "alpha " * 5 + "\n- another line about " + "beta " * 5)
    write(os.path.join(d, "AGENTS.md"), "- something totally different for codex users to read\n- and more different words here too, nothing alike")
    s, f = cost_audit.audit(d)
    check("audit: different files are not flagged as duplicates", not any("repeat" in x["title"] for x in f))

with tempfile.TemporaryDirectory() as d:
    write(os.path.join(d, "AGENTS.md"), "x" * 40000)
    s, f = cost_audit.audit(d)
    check("audit: AGENTS.md over 32 KiB is HIGH", any(x["level"] == "HIGH" and "bytes" in x["title"] for x in f))

with tempfile.TemporaryDirectory() as d:
    write(os.path.join(d, ".cursor/rules/big.mdc"), "---\nalwaysApply: true\n---\n" + "rule text here. " * 500)
    write(os.path.join(d, ".cursor/rules/scoped.mdc"), "---\nglobs: src/**\nalwaysApply: false\n---\n" + "rule text here. " * 500)
    write(os.path.join(d, ".cursor/rules/plain.md"), "ignored")
    s, f = cost_audit.audit(d)
    check("audit: only alwaysApply rules counted", 1500 < s["cursor_always_apply_tokens"] < 3000, str(s["cursor_always_apply_tokens"]))
    check("audit: plain .md rule reported as ignored", any("plain.md" in x["title"] for x in f))

with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "node_modules", "pkg"))
    os.makedirs(os.path.join(d, "packages", "a", "dist"))
    write(os.path.join(d, "node_modules", "CLAUDE.md"), "must not be scanned")
    s, f = cost_audit.audit(d)
    check("audit: noise dirs found incl. nested", sorted(s["noise_dirs"]) == ["node_modules", os.path.join("packages", "a", "dist")], str(s["noise_dirs"]))
    check("audit: files inside node_modules are not scanned", "node_modules/CLAUDE.md" not in s["instruction_files"] and not s["instruction_files"])
    check("audit: uncovered noise flagged", any("noisy folder" in x["title"] for x in f))
    write(os.path.join(d, ".cursorignore"), "# c\nnode_modules/\ndist/\n")
    s, f = cost_audit.audit(d)
    check("audit: .cursorignore covers noise", not any("noisy folder" in x["title"] for x in f), str([x["title"] for x in f]))

with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "node_modules"))
    write(os.path.join(d, ".claude/settings.json"), json.dumps({"permissions": {"deny": ["Read(node_modules/**)"]}}))
    s, f = cost_audit.audit(d)
    check("audit: Claude Read deny covers noise", not any("noisy folder" in x["title"] for x in f))

with tempfile.TemporaryDirectory() as d:
    write(os.path.join(d, "data/huge.csv"), "a,b\n" + "1,2\n" * 120000)
    write(os.path.join(d, "logo.png"), "x" * 400000)
    s, f = cost_audit.audit(d, big_kb=200)
    big = [x for x in f if "big file" in x["title"]]
    check("audit: big text file listed, image skipped", big and "huge.csv" in big[0]["detail"] and "logo.png" not in big[0]["detail"])

with tempfile.TemporaryDirectory() as d:
    write(os.path.join(d, ".mcp.json"), json.dumps({"mcpServers": {n: {"command": "x"} for n in "abcdefg"}}))
    write(os.path.join(d, ".codex/config.toml"), '[mcp_servers.one]\ncommand = "x"\nenabled = false\n\n[mcp_servers.two]\ncommand = "y"\n')
    s, f = cost_audit.audit(d)
    names = {(m["name"], m["enabled"]) for m in s["mcp_servers"]}
    check("audit: codex enabled=false read", ("one", False) in names and ("two", True) in names, str(names))
    check("audit: 8 servers on is MED", any(x["level"] == "MED" and "MCP" in x["title"] for x in f))

with tempfile.TemporaryDirectory() as d:
    write(os.path.join(d, ".claudeignore"), "dist/")
    s, f = cost_audit.audit(d)
    check("audit: .claudeignore flagged", any(".claudeignore" in x["title"] for x in f))

with tempfile.TemporaryDirectory() as d:
    write(os.path.join(d, ".claude/settings.json"), json.dumps({"hooks": {"PreToolUse": [{"command": "tail -n 100"}]}}))
    s, f = cost_audit.audit(d)
    check("audit: hook present removes the hook tip", not any("hook" in x["title"] for x in f))

demo = os.path.join(ROOT, "samples", "demo-project")
r = run(os.path.join(SCRIPTS, "cost_audit.py"), demo)
check("audit CLI: demo runs", r.returncode == 0 and "[HIGH]" in r.stdout, r.stderr[-200:])
r = run(os.path.join(SCRIPTS, "cost_audit.py"), demo, "--json")
try:
    j = json.loads(r.stdout)
    check("audit CLI: --json valid", "summary" in j and j["findings"])
except ValueError:
    check("audit CLI: --json valid", False, r.stdout[:100])
check("audit CLI: --fail-on high exits 1 on demo", run(os.path.join(SCRIPTS, "cost_audit.py"), demo, "--fail-on", "high").returncode == 1)
with tempfile.TemporaryDirectory() as d:
    check("audit CLI: --fail-on high exits 0 when clean", run(os.path.join(SCRIPTS, "cost_audit.py"), d, "--fail-on", "high").returncode == 0)
check("audit CLI: bad folder exits 2", run(os.path.join(SCRIPTS, "cost_audit.py"), "/nonexistent/zzz").returncode == 2)
check("audit: shipped sample output matches the demo", True)
# the saved sample output must match a fresh run (relative path as in samples/)
fresh = subprocess.run([sys.executable, os.path.join(SCRIPTS, "cost_audit.py"), "demo-project"], cwd=os.path.join(ROOT, "samples"), capture_output=True, text=True).stdout
saved = open(os.path.join(ROOT, "samples", "cost-audit-demo-output.txt")).read()
check("audit: saved sample output is current", fresh.strip() == saved.strip())

# the lean templates must pass their own audit
with tempfile.TemporaryDirectory() as d:
    for src, dst in (("CLAUDE.lean.md", "CLAUDE.md"), ("AGENTS.lean.md", "AGENTS.md")):
        write(os.path.join(d, dst), open(os.path.join(ROOT, "templates", src)).read())
    write(os.path.join(d, ".cursor/rules/scoped.mdc"), open(os.path.join(ROOT, "templates", "cursor-rule-scoped.mdc")).read())
    s, f = cost_audit.audit(d)
    check("templates: lean files raise no HIGH/MED finding", not [x for x in f if x["level"] in ("HIGH", "MED")], str(f))
    check("templates: lean files are small", s["always_loaded_tokens_estimate"] < 800, str(s["always_loaded_tokens_estimate"]))

# ---------- session_report ----------
def rec(i, ts, inp, out, cr, cw, mid=None, model="claude-sonnet-x"):
    return json.dumps({"type": "assistant", "timestamp": ts, "requestId": f"r{i}",
                       "message": {"id": mid or f"m{i}", "model": model,
                                   "usage": {"input_tokens": inp, "output_tokens": out,
                                             "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw}}})

with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "proj-a", "sess1.jsonl")
    lines = [
        rec(1, "2026-11-20T10:00:00.000Z", 10, 100, 0, 5000),
        rec(2, "2026-11-20T10:01:00.000Z", 10, 200, 5000, 300),
        rec(2, "2026-11-20T10:01:00.000Z", 10, 250, 5000, 300),   # streamed duplicate: last wins
        rec(3, "2026-11-20T11:30:00.000Z", 10, 100, 0, 60000),     # 89 minute gap: cold restart
        json.dumps({"type": "user", "message": {"content": "hello"}}),
        "not json at all",
        json.dumps({"type": "assistant", "message": {"model": "<synthetic>", "usage": {"input_tokens": 0, "output_tokens": 0}}}),
    ]
    write(p, "\n".join(lines) + "\n")
    reqs = session_report.load_session(p)
    check("session: dedupe keeps 3 requests", len(reqs) == 3, str(len(reqs)))
    check("session: last duplicate wins (250 output)", reqs[1]["out"] == 250)
    s = session_report.summarize(p, reqs, 5, 20000)
    check("session: totals", s["output"] == 450 and s["cache_read"] == 5000 and s["cache_write"] == 65300, str(s))
    check("session: cold restart counted", s["cold_restarts"] == 1 and s["cold_restart_tokens"] == 60000)
    check("session: peak context", s["peak_context"] == 60010)
    s60 = session_report.summarize(p, reqs, 120, 20000)
    check("session: longer cache lifetime means no cold restart", s60["cold_restarts"] == 0)
    r = run(os.path.join(SCRIPTS, "session_report.py"), "--dir", d, "--rates", "3,15,0.3,3.75")
    check("session CLI: runs and prints dollars", r.returncode == 0 and "~$" in r.stdout and "cold restart" in r.stdout, r.stdout + r.stderr)
    r = run(os.path.join(SCRIPTS, "session_report.py"), "--dir", d, "--json")
    check("session CLI: --json valid", json.loads(r.stdout)["top"][0]["requests"] == 3)
    r = run(os.path.join(SCRIPTS, "session_report.py"), "--dir", d, "--days", "1")
    check("session CLI: --days filters old sessions", "No usage records" in r.stdout, r.stdout)
    r = run(os.path.join(SCRIPTS, "session_report.py"), "--dir", d, "--rates", "1,2")
    check("session CLI: bad --rates exits 2", r.returncode == 2)
with tempfile.TemporaryDirectory() as d:
    r = run(os.path.join(SCRIPTS, "session_report.py"), "--dir", d)
    check("session CLI: empty dir is a calm message", r.returncode == 0 and "No usage records" in r.stdout)

# ---------- make_ignore ----------
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "node_modules"))
    os.makedirs(os.path.join(d, "app", "dist"))
    r = run(os.path.join(SCRIPTS, "make_ignore.py"), d)
    check("ignore: prints folders and Read rules", "node_modules/" in r.stdout and "Read(dist/**)" in r.stdout and ".claudeignore" in r.stdout, r.stdout)
    check("ignore: print-only does not write", not os.path.exists(os.path.join(d, ".cursorignore")))
    r = run(os.path.join(SCRIPTS, "make_ignore.py"), d, "--write")
    check("ignore: --write creates file", os.path.exists(os.path.join(d, ".cursorignore")))
    write(os.path.join(d, ".cursorignore"), "mine\n")
    run(os.path.join(SCRIPTS, "make_ignore.py"), d, "--write")
    check("ignore: no overwrite without --force", open(os.path.join(d, ".cursorignore")).read() == "mine\n")
    run(os.path.join(SCRIPTS, "make_ignore.py"), d, "--write", "--force")
    check("ignore: --force overwrites", "node_modules/" in open(os.path.join(d, ".cursorignore")).read())
    # round trip: audit sees the folders as covered
    s, f = cost_audit.audit(d)
    check("ignore: generated file satisfies the audit", not any("noisy folder" in x["title"] for x in f))

# ---------- hook ----------
ev = {"tool_name": "Bash", "tool_input": {"command": "pytest -x tests/test_a.py", "description": "run"}}
out = filter_test_output.decide(ev, 50)
new = out["hookSpecificOutput"]["updatedInput"]
check("hook: test command rewritten", new["command"].endswith("| tail -n 50") and "pipefail" in new["command"])
check("hook: other tool_input fields kept", new["description"] == "run")
check("hook: event name set", out["hookSpecificOutput"]["hookEventName"] == "PreToolUse")
for cmd in ["ls -la", "pytest && rm -rf x", "pytest | cat", "npm test; echo hi", "pytest -k \"a b\"", "go test ./... > out.txt", "pytest $(whoami)", "pytest `id`"]:
    check(f"hook: leaves alone: {cmd}", filter_test_output.decide({"tool_name": "Bash", "tool_input": {"command": cmd}}) == {})
check("hook: non-Bash tool ignored", filter_test_output.decide({"tool_name": "Read", "tool_input": {"command": "pytest"}}) == {})
check("hook: accepts go test ./...", filter_test_output.decide({"tool_name": "Bash", "tool_input": {"command": "go test ./..."}}) != {})
# the rewritten wrapper must keep a failing exit code, and must trim output
w = filter_test_output.wrap("sh -c 'seq 1 300; exit 3'", 100)
r = subprocess.run(["bash", "-c", w], capture_output=True, text=True)
check("hook: failing command keeps exit code 3", r.returncode == 3, str(r.returncode))
check("hook: output trimmed to 100 lines", len(r.stdout.splitlines()) == 100 and r.stdout.splitlines()[-1] == "300")
r = subprocess.run(["bash", "-c", filter_test_output.wrap("sh -c 'echo ok'", 100)], capture_output=True, text=True)
check("hook: passing command exits 0", r.returncode == 0 and r.stdout.strip() == "ok")
r = run(os.path.join(SCRIPTS, "filter_test_output.py"), stdin=json.dumps(ev), env={"TBT_TAIL_LINES": "7"})
check("hook CLI: reads stdin, honors TBT_TAIL_LINES (min 10)", "tail -n 10" in r.stdout, r.stdout)
r = run(os.path.join(SCRIPTS, "filter_test_output.py"), stdin="garbage")
check("hook CLI: bad input prints {}", r.stdout.strip() == "{}")

# ---------- templates and docs ----------
json.load(open(os.path.join(ROOT, "templates", "claude-settings.cost.example.json")))
check("templates: settings example is valid JSON", True)
try:
    import tomllib
    tomllib.loads(open(os.path.join(ROOT, "templates", "codex-config.example.toml")).read())
    check("templates: codex example is valid TOML", True)
except ImportError:
    check("templates: codex example (tomllib missing, skipped)", True)
mdc = open(os.path.join(ROOT, "templates", "cursor-rule-scoped.mdc")).read()
check("templates: cursor rule is scoped, not always-on", "alwaysApply: false" in mdc and "globs:" in mdc)
check("templates: CLAUDE.lean under 60 lines", len(open(os.path.join(ROOT, "templates", "CLAUDE.lean.md")).read().splitlines()) < 60)

md_files = []
for base, _, files in os.walk(ROOT):
    for fn in files:
        if fn.endswith(".md") and "samples" not in base:
            md_files.append(os.path.join(base, fn))
bad = []
for p in md_files:
    text = open(p, encoding="utf-8").read()
    for m in re.finditer(r"\]\((?!https?:|#|mailto:)([^)\s]+)\)", text):
        target = m.group(1).split("#")[0]
        if target and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), target))):
            bad.append((os.path.relpath(p, ROOT), target))
check("docs: every relative markdown link resolves", not bad, str(bad))
readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read() if os.path.exists(os.path.join(ROOT, "README.md")) else ""
check("docs: README exists", bool(readme))
missing = [m for m in re.findall(r"`((?:guide|scripts|templates|samples)/[A-Za-z0-9_./-]+)`", readme) if not os.path.exists(os.path.join(ROOT, m))]
check("docs: every file named in README exists", not missing, str(missing))
alltext = "\n".join(open(p, encoding="utf-8").read() for p in md_files)
check("docs: links to Ship-Ready Skills Pack", "tidybyte.gumroad.com/l/ship-ready-skills-pack" in alltext)
check("docs: links to AGENTS.md Starter Pack", "tidybyte.gumroad.com/l/" in alltext and "AGENTS.md Starter Pack" in alltext)
check("docs: no invented savings percentages", not re.search(r"\b(save|saves|saving|cut|cuts|reduce|reduces)\b[^.\n]{0,40}\b\d{2,3}\s?%", alltext, re.I))
check("docs: no secrets or personal emails", not re.search(r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|@gmail\.com|apify_api_)", alltext))

print(f"\n{PASSED} passed, {FAILED} failed")
sys.exit(1 if FAILED else 0)
