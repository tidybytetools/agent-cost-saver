#!/usr/bin/env python3
"""session_report.py - which Claude Code sessions used the most tokens, and why?

Reads the session logs Claude Code keeps on your computer
(default: ~/.claude/projects/**/*.jsonl) and adds up the token counts that
each reply reports. Standard library only. It only reads files.

IMPORTANT: those logs are not an official, promised format. If a future version
changes them, this script will say "no usage records found" instead of guessing.
Your own /usage screen in Claude Code is always the source of truth.

Usage:
  python3 session_report.py [--dir PATH] [--days 7] [--top 10]
                            [--cache-minutes 5] [--rates IN,OUT,CACHE_READ,CACHE_WRITE] [--json]

--rates are YOUR dollar prices per million tokens. We do not guess prices.
"""
import argparse
import datetime
import glob
import json
import os
import sys


def parse_ts(s):
    try:
        return datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def load_session(path):
    """Return a list of requests (dicts) from one .jsonl file, de-duplicated."""
    seen = {}
    order = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if not isinstance(obj, dict):
                continue
            msg = obj.get("message")
            if obj.get("type") != "assistant" or not isinstance(msg, dict):
                continue
            usage = msg.get("usage")
            if not isinstance(usage, dict):
                continue
            if msg.get("model") == "<synthetic>":
                continue
            rec = {
                "ts": parse_ts(obj.get("timestamp")),
                "model": msg.get("model") or "unknown",
                "in": int(usage.get("input_tokens") or 0),
                "out": int(usage.get("output_tokens") or 0),
                "cr": int(usage.get("cache_read_input_tokens") or 0),
                "cw": int(usage.get("cache_creation_input_tokens") or 0),
            }
            key = (msg.get("id"), obj.get("requestId")) if msg.get("id") else ("line", n)
            if key not in seen:
                order.append(key)
            seen[key] = rec  # keep the last copy: streamed copies end with the final counts
    return [seen[k] for k in order]


def summarize(path, reqs, cache_minutes, restart_min):
    ts = [r["ts"] for r in reqs if r["ts"]]
    s = {
        "session": os.path.splitext(os.path.basename(path))[0],
        "project": os.path.basename(os.path.dirname(path)),
        "requests": len(reqs),
        "input": sum(r["in"] for r in reqs),
        "output": sum(r["out"] for r in reqs),
        "cache_read": sum(r["cr"] for r in reqs),
        "cache_write": sum(r["cw"] for r in reqs),
        "peak_context": max((r["in"] + r["cr"] + r["cw"] for r in reqs), default=0),
        "models": sorted({r["model"] for r in reqs}),
        "first": min(ts).isoformat() if ts else None,
        "last": max(ts).isoformat() if ts else None,
        "hours": round((max(ts) - min(ts)).total_seconds() / 3600, 2) if len(ts) > 1 else 0,
        "cold_restarts": 0,
        "cold_restart_tokens": 0,
    }
    prev = None
    for r in reqs:
        if prev and prev["ts"] and r["ts"]:
            gap = (r["ts"] - prev["ts"]).total_seconds()
            if gap > cache_minutes * 60 and r["cw"] >= restart_min:
                s["cold_restarts"] += 1
                s["cold_restart_tokens"] += r["cw"]
        prev = r
    total_in = s["input"] + s["cache_read"] + s["cache_write"]
    s["cache_hit_pct"] = round(100.0 * s["cache_read"] / total_in, 1) if total_in else 0.0
    s["total_tokens"] = total_in + s["output"]
    flags = []
    if s["requests"] >= 150:
        flags.append("many requests: clear between tasks")
    if s["peak_context"] >= 200000:
        flags.append("huge context: clear or compact sooner")
    if s["cold_restarts"] >= 2:
        flags.append(f"{s['cold_restarts']} cold restarts after idle: start fresh after long breaks")
    if s["hours"] >= 6:
        flags.append("open for many hours: one task per session")
    s["flags"] = flags
    return s


def dollars(s, rates):
    i, o, cr, cw = rates
    return (s["input"] * i + s["output"] * o + s["cache_read"] * cr + s["cache_write"] * cw) / 1e6


def main(argv=None):
    ap = argparse.ArgumentParser(description="Token totals per Claude Code session, from local logs.")
    ap.add_argument("--dir", default=os.path.join(os.path.expanduser("~"), ".claude", "projects"))
    ap.add_argument("--days", type=int, default=0, help="only sessions that ended in the last N days")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--cache-minutes", type=float, default=5.0,
                    help="how long your prompt cache lives (default 5; see /usage for your setup)")
    ap.add_argument("--restart-min-tokens", type=int, default=20000)
    ap.add_argument("--rates", help="your $/million tokens: input,output,cache_read,cache_write")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rates = None
    if a.rates:
        try:
            rates = [float(x) for x in a.rates.split(",")]
            assert len(rates) == 4
        except (ValueError, AssertionError):
            print("--rates needs 4 numbers: input,output,cache_read,cache_write", file=sys.stderr)
            return 2
    files = sorted(glob.glob(os.path.join(a.dir, "**", "*.jsonl"), recursive=True))
    sessions = []
    cutoff = None
    if a.days:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=a.days)
    for p in files:
        try:
            reqs = load_session(p)
        except OSError:
            continue
        if not reqs:
            continue
        s = summarize(p, reqs, a.cache_minutes, a.restart_min_tokens)
        if cutoff and s["last"]:
            last = parse_ts(s["last"])
            if last and last.tzinfo and last < cutoff:
                continue
        if rates:
            s["estimated_dollars"] = round(dollars(s, rates), 2)
        sessions.append(s)
    if not sessions:
        print(f"No usage records found under {a.dir}.")
        print("Either there are no sessions yet, or this Claude Code version logs in a different format.")
        print("Use /usage inside Claude Code instead.")
        return 0
    sessions.sort(key=lambda s: -s["total_tokens"])
    top = sessions[: a.top]
    if a.json:
        print(json.dumps({"sessions": len(sessions), "top": top}, indent=2))
        return 0
    tot = {k: sum(s[k] for s in sessions) for k in ("requests", "input", "output", "cache_read", "cache_write")}
    print(f"{len(sessions)} session(s) in {a.dir}")
    print(f"All sessions: {tot['requests']:,} requests | input {tot['input']:,} | output {tot['output']:,} | "
          f"cache read {tot['cache_read']:,} | cache write {tot['cache_write']:,}")
    print("")
    print(f"Top {len(top)} by total tokens:")
    for s in top:
        extra = f" | ~${s['estimated_dollars']}" if "estimated_dollars" in s else ""
        print(f"- {s['session'][:12]}  {s['project'][:40]}")
        print(f"    {s['requests']} requests | peak context {s['peak_context']:,} | output {s['output']:,} | "
              f"cache hit {s['cache_hit_pct']}% | {s['hours']} h{extra}")
        if s["cold_restarts"]:
            print(f"    cold restarts after idle: {s['cold_restarts']} ({s['cold_restart_tokens']:,} tokens written to cache again)")
        for fl in s["flags"]:
            print(f"    ! {fl}")
    if rates:
        print("")
        print("Dollar numbers use the rates you gave. They are estimates, not a bill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
