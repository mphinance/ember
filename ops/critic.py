#!/usr/bin/env python3
"""
ops/critic.py — the CRITIC brain. A cheap, single-shot reviewer that reads the WheelForge
code + the live picks + the recent journal, looks through ONE rotating LENS, and appends 1-3
concrete steering notes to INBOX.md. ember (the Opus builder) reads INBOX first every cycle,
so this closes the loop: one model ships, a DIFFERENT model keeps it honest and aimed.

Model diversity is the whole point. If OPENROUTER_API_KEY is set we rotate through a roster of
models (GPT, Gemini, DeepSeek, Grok, Claude, etc. — different eyes each run). If not, we fall
back to local Sonnet via `happy` so it still runs keyless. Lens AND model both rotate by clock.

It ONLY appends to INBOX.md. It never edits code or scan.json. The wrapper (ops/review.sh)
does the git commit/push of INBOX under the shared lock. Fail-open everywhere: any error and we
add nothing rather than break the loop.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rotating lenses — a different angle each run.
LENSES = [
    ("trader", "Michael himself: do the ACTUAL picks help sell rich premium AT support to hit "
               "~100%/yr on weeklies? Would he take these exact trades today? What would make him "
               "trust the list more? He loves assignment when the basis is right and does NOT want "
               "nannying about risk."),
    ("quant", "Is the math honest end to end? Hunt dead or constant factors, risk-neutral-vs-real "
              "sloppiness, IV/HV/VRP or annualization errors, anything that would mislead a vol "
              "seller. Name the file and the number."),
    ("product", "Judge the live page/product. Is the single BEST pick obvious in five seconds? "
                "What is confusing, buried, or ugly? Name the ONE change that makes it more "
                "glanceable."),
    ("risk", "Where could this quietly lose money or mislead? Earnings in the window, thin "
             "liquidity, assignment surprises, a label that overstates an edge. What guard is "
             "missing?"),
    ("growth", "What is the single highest-leverage MISSING capability for the income machine "
               "right now? Name the one thing that would matter most next, and why."),
]

# Preferred OpenRouter roster (cheap, capable, DIVERSE vendors). Validated against the live
# /models list at runtime so a stale slug is skipped, not fatal. Edit freely.
OPENROUTER_ROSTER = [
    "openai/gpt-4o",
    "google/gemini-2.5-flash",
    "deepseek/deepseek-chat",
    "x-ai/grok-2-1212",
    "anthropic/claude-3.7-sonnet",
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
    "mistralai/mistral-large",
]


def _read(path, cap=6000):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            t = f.read()
        return t if len(t) <= cap else t[:cap] + "\n...[truncated]"
    except Exception:
        return ""


def _scan_sample(n=6):
    """Top n live picks, compact, so the critic sees the real output."""
    try:
        with open(os.path.join(ROOT, "docs/data/scan.json"), encoding="utf-8") as f:
            data = json.load(f)
        rows = data.get("results") or data.get("picks") or data.get("rows") or data
        if isinstance(rows, dict):
            rows = rows.get("results") or list(rows.values())
        out = []
        for r in (rows or [])[:n]:
            p = r.get("pick", r) if isinstance(r, dict) else {}
            out.append({k: p.get(k) for k in
                        ("ticker", "strike", "exp", "dte", "annualized_roc", "prob_otm",
                         "iv", "rv", "vrp", "at_support", "support", "iv_gt_hv", "score", "grade")
                        if k in p or k in r})
        return json.dumps(out, separators=(",", ":"))[:3500]
    except Exception:
        return "(scan.json unavailable)"


def _context():
    files = {
        "INBOX.md (do NOT repeat anything here)": _read("INBOX.md", 4000),
        "GOAL.md (roadmap — do NOT repeat queued items)": _read("GOAL.md", 6000),
        "recent LOG.md": _read("LOG.md", 3500),
        "memory/michael.md (his thesis)": _read("memory/michael.md", 3500),
        "wheelforge/build_site_data.py (the engine)": _read("wheelforge/build_site_data.py", 9000),
    }
    # name the rest of the engine so the critic knows what exists to point at
    try:
        mods = sorted(f for f in os.listdir(os.path.join(ROOT, "wheelforge")) if f.endswith(".py"))
    except Exception:
        mods = []
    parts = ["wheelforge modules present: " + ", ".join(mods),
             "TOP LIVE PICKS (docs/data/scan.json): " + _scan_sample()]
    for name, body in files.items():
        if body:
            parts.append("=== " + name + " ===\n" + body)
    return "\n\n".join(parts)


def _pick(seq):
    now = datetime.now(timezone.utc)
    idx = (now.timetuple().tm_yday + now.hour) % len(seq)
    return idx, seq[idx]


SYS = ("You are an independent senior reviewer giving Michael's WheelForge (a cash-secured-put "
       "wheel income scanner) a hard, specific look through ONE lens. You are NOT the builder; "
       "another agent implements. Output ONLY 1 to 3 steering bullets, each CONCRETE and doable "
       "in a single build cycle, each naming the file/factor/number involved. Skip anything "
       "already in INBOX.md or GOAL.md. No preamble, no praise, no markdown headers — just the "
       "bullets, one per line, starting with '- '. If the product is genuinely solid through "
       "this lens, give ONE bullet with the single best next idea.")


def _via_openrouter(prompt, key):
    """Rotate through the validated roster; return (text, model) or (None, None)."""
    avail = set()
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/models",
                                     headers={"Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=20) as r:
            avail = {m.get("id") for m in json.load(r).get("data", [])}
    except Exception:
        pass
    roster = [m for m in OPENROUTER_ROSTER if (m in avail or not avail)]
    if not roster:
        roster = OPENROUTER_ROSTER
    _, model = _pick(roster)
    # try the rotated model, then fall back through the rest of the roster
    order = [model] + [m for m in roster if m != model]
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYS},
                     {"role": "user", "content": prompt}],
        "max_tokens": 700, "temperature": 0.7,
    })
    for m in order:
        try:
            payload = json.loads(body); payload["model"] = m
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": "Bearer " + key,
                         "Content-Type": "application/json",
                         "HTTP-Referer": "https://mphinance.github.io/ember",
                         "X-Title": "ember critic"})
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.load(r)
            txt = out["choices"][0]["message"]["content"].strip()
            if txt:
                return txt, m
        except Exception as e:
            sys.stderr.write(f"openrouter {m} failed: {e}\n")
    return None, None


def _via_gemini(prompt, key, model="gemini-2.5-flash"):
    """Direct Google Generative Language API (Michael has a GEMINI_API_KEY)."""
    try:
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               + model + ":generateContent?key=" + key)
        body = json.dumps({
            "system_instruction": {"parts": [{"text": SYS}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 700, "temperature": 0.7},
        }).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            out = json.load(r)
        txt = out["candidates"][0]["content"]["parts"][0]["text"].strip()
        return (txt, model) if txt else (None, None)
    except Exception as e:
        sys.stderr.write(f"gemini failed: {e}\n")
        return None, None


def _via_happy(prompt):
    """Keyless fallback: local Sonnet through happy print-mode."""
    try:
        p = subprocess.run(
            ["happy", "-p", "--claude-env", "ANTHROPIC_MODEL=claude-sonnet-4-6"],
            input=SYS + "\n\n" + prompt, capture_output=True, text=True, timeout=300)
        txt = (p.stdout or "").strip()
        return (txt, "claude-sonnet-4-6 (local)") if txt else (None, None)
    except Exception as e:
        sys.stderr.write(f"happy fallback failed: {e}\n")
        return None, None


def _clean_bullets(txt):
    out = []
    for ln in txt.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if ln[0] in "-*•":
            ln = "- " + ln.lstrip("-*• ").strip()
        elif ln[:2].rstrip(".").isdigit():
            ln = "- " + ln.split(".", 1)[-1].strip()
        else:
            continue
        if len(ln) > 5:
            out.append(ln)
    return out[:3]


def main():
    lens_idx, (lens_name, lens_desc) = _pick(LENSES)
    prompt = ("LENS for this review: " + lens_desc + "\n\n"
              "Here is the current state of WheelForge:\n\n" + _context())
    # Rotate across whatever models are available, for genuinely different eyes each run.
    ork = os.environ.get("OPENROUTER_API_KEY", "").strip()
    gk = os.environ.get("GEMINI_API_KEY", "").strip()
    providers = []
    if ork:
        providers.append("openrouter")   # rotates its own roster (GPT/Gemini/DeepSeek/...)
    if gk:
        providers.append("gemini")       # Gemini 2.5 Flash, direct
    providers.append("local")            # local Sonnet via happy — always available
    _, prov = _pick(providers)
    if prov == "openrouter":
        txt, model = _via_openrouter(prompt, ork)
    elif prov == "gemini":
        txt, model = _via_gemini(prompt, gk)
    else:
        txt, model = _via_happy(prompt)
    if not txt:                          # any provider error -> keyless fallback
        txt, model = _via_happy(prompt)
    if not txt:
        sys.stderr.write("critic: no model produced output; adding nothing\n")
        return 0
    bullets = _clean_bullets(txt)
    if not bullets:
        sys.stderr.write("critic: no usable bullets parsed; adding nothing\n")
        return 0
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    block = (f"\n## critic [{lens_name}] · {model} — {stamp}\n"
             + "\n".join(bullets) + "\n")
    with open(os.path.join(ROOT, "INBOX.md"), "a", encoding="utf-8") as f:
        f.write(block)
    print(f"critic: lens={lens_name} model={model} added {len(bullets)} note(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
