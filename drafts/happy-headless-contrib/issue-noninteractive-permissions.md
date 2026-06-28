# Issue draft: document the supported way to run Happy with no permission prompts (headless / service / root)

> Paste into a new issue at https://github.com/slopus/happy/issues after confirming
> the behavior against your installed version. Claims are from observation on one
> Linux box, not from reading Happy's source — phrased to ask, not assert.

---

**Title:** Docs: what's the blessed way to run Happy fully unattended (no permission prompts) on a service/root account?

**Type:** docs / question (possible small feature)

### Context

Happy works great headless: `happy -p` with a prompt on stdin runs one cycle and exits
with a meaningful code, which is exactly what you want from cron / a systemd timer / CI.
The piece that isn't documented is the **permission story** for that mode. With no human
to approve prompts, any tool call that isn't pre-approved just blocks until the run times
out.

### What I'm doing today

```bash
happy -p --allowedTools "Bash Write Edit Read Glob Grep" < prompt.txt
```

A scoped `--allowedTools` allowlist makes the listed tools run without prompting, which
gives clean unattended runs and a blast-radius limit at the same time. This has been
solid across a few thousand scheduled runs.

### The questions

1. **Is `--allowedTools` the intended/supported way to get no-prompt behavior in `-p`
   mode**, or is there a first-class non-interactive permission flag I've missed? If the
   allowlist is the blessed path, it would help to say so in the docs — right now nothing
   in the README or CLI help points an automation user there.

2. **`--dangerously-skip-permissions` / yolo appears to be refused on root and some
   service accounts** (the accounts cron jobs commonly run as). Is that intentional? If
   so, the docs should name the supported alternative for those accounts (presumably the
   allowlist), because the natural first reach for "stop asking me" is the yolo flag, and
   it dead-ends there with no signpost.

3. Minor, if easy: when a tool that ISN'T allowlisted is hit in `-p` mode, the run
   currently blocks (until the caller's `timeout` kills it). Would it make sense for
   headless/print mode to instead **fail fast** on a would-be prompt — non-zero exit with
   a clear "tool X needed approval, not in allowlist" message — so the caller learns the
   allowlist is too narrow instead of just timing out? That single behavior change would
   make headless misconfiguration debuggable.

### Why it matters

Happy is becoming a default way to run Claude Code, and "run it on a schedule with no one
watching" is a large, growing use case (autonomous loops, nightly jobs, CI agents). The
machinery already works; it's the one paragraph of docs — *here's how to run with zero
prompts, here's why not yolo on root* — that's missing. Happy to send a docs PR with a
worked cron example and a hardened wrapper script if that'd be welcome; I have both ready.
