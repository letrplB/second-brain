---
name: no-surrender
description: Probe the user's grip on a vault claim across mechanism / implications / falsifiability / bounds axes. Updates the claim's engagement vector. The only verb that writes engagement. Gated by surrender.enabled in vault.yaml.
version: "0.1"
user-invocable: true
allowed-tools: Read, Edit, Glob, Grep, Bash
argument-hint: "[claim-wikilink | path | _<topic-map> | --weakest=N | --recent-since=Nd] [--axis=<name>] — single claim by [[wikilink]] or path; or a topic-MOC for sequential testing; or scope flags."
---

# /no-surrender

**Intent.** Test the user's mental grip on a claim. Write the result to the claim's `engagement` vector so the vault knows what the user has actually engaged with vs. what they've absorbed without verification. Read `surrender-tracking-design.md` at the repo root for the design rationale.

This verb is the **architectural circuit-break** for the calibration loop (model emits high confidence without reasoning; user accepts without verification). It is the only verb in the vault that writes `engagement`.

## Gating — read every invocation, never cache

**Step 1, always.** Read `vault/vault.yaml`. Check `surrender.enabled`.

- If `surrender.enabled` is missing, `false`, or anything other than literal `true`: print this and exit immediately:
  ```
  /no-surrender is gated by surrender.enabled in vault.yaml. Set surrender.enabled: true to enable.
  ```
- Do not proceed. Do not write any file. Do not read any claim. The gate is the first action and the first thing to fail.

This is a behavioural gate (skill-instruction layer), not a runtime gate. The flag exists to make activation deliberate. Re-read on every invocation — never assume it's still on from a prior call.

## Target forms

Single argument forms (mutually exclusive):

| Form | Example | Behaviour |
|---|---|---|
| `[[wikilink]]` | `/no-surrender [[ai-tutor-design-must-embed...]]` | Resolve wikilink to file in `notes/claims/` or `notes/synthesis/`; test that one claim |
| Path | `/no-surrender notes/claims/some-claim.md` | Test that one claim |
| `_<topic-map>` | `/no-surrender _ai-in-education` | Read MOC; sequentially test each claim under `## Core claims`. User can `/stop` between claims. |
| `--weakest=N` | `/no-surrender --weakest=5` | Find N claims with lowest current effective engagement (after decay); test in order |
| `--recent-since=Nd` | `/no-surrender --recent-since=14d` | Test claims with `created` date within last N days |

Optional modifier:

- `--axis=<name>` — force a specific axis (`mechanism`, `implications`, `falsifiability`, `bounds`). Overrides default axis selection.

## Workflow per claim

For each claim selected by the target:

### 1. Read and compute current state

- Read the claim's frontmatter and body.
- If `engagement` is absent or null: this is a **first probe**. Set `γ = 1.0` (full replacement of engagement on grading).
- If `engagement` exists: this is a **re-probe**. Set `γ = 0.5` (EMA smoothing).
- For re-probes, compute the **decayed** engagement for each existing axis using the read-time decay formula:
  ```
  e_now(axis) = e₀ · 0.9 ^ (Δt / s)
  ```
  where `e₀` = `engagement.axes[axis]`, `Δt` = days since `engagement.last_tested`, `s` = `engagement.stability[axis]`.

### 2. Select axes to probe (1–3)

- If `--axis=<name>` was provided: use only that axis.
- Else if **first probe** on this claim: pick the default axes (see `probes.md` heuristics — typically `mechanism` + one secondary by `evidence_type` or tags).
- Else (re-probe): target the axis with the lowest current decayed engagement. Add a second axis if it has decayed below 0.5.

**Limit: 1 axis for tight-budget claims (re-probe with one weak axis), 2–3 axes for full first probe. Never 4 in one session — friction principle.**

### 3. Generate and ask probes

For each selected axis, generate a probe using the templates in `probes.md`. The probe must:

- Reference the claim's title or subject in plain language
- **Not reveal the claim body** (no copy-paste from the claim into the probe)
- Be answerable in 1–3 sentences
- Be open-ended; not a yes/no

Print:
```
/no-surrender [[claim-title]]
Reading claim, computing decay...

Tested axes: <axis-1>, <axis-2>

Probe 1 (<axis-1>): <question>
```

Wait for user response.

### 4. Grade against claim body

Compare the user's answer against the claim body. Apply this rubric:

| Score | Meaning |
|---|---|
| 0.0 | Contradicts the claim, or fundamental misunderstanding of subject |
| 0.3 | Surface-level match, missing the core (e.g., names the right entity but wrong mechanism) |
| 0.6 | Substantial match with notable omission |
| 0.85 | Full match, correct paraphrase, captures the load-bearing detail |
| 1.0 | Match plus connections to neighbours or correct generalisation beyond the claim's stated scope |

Print the grade with a one-sentence rationale:
```
Grade (<axis>): 0.6
Rationale: <user> captured the X mechanism correctly but missed the Y dependence that's load-bearing in the claim body.
```

### 5. Accept dispute

After showing the grade, watch for dispute in the user's next message.

- **Substantive dispute** (user provides reasoning, points to specific text in the claim, names a missed nuance): bump grade by `+0.1`, capped at the rubric band ceiling for the actual response quality (i.e., never bump above what the user's full response, including dispute, deserves).
- **Trivial dispute** ("I disagree" without elaboration): no bump. Acknowledge: "Noted — the grade stands without elaboration." Move on.
- The dispute itself counts as engagement: if the user successfully argues the grade up, the *higher* value is what gets persisted.

### 6. Compute new engagement and stability

For each tested axis:

**Engagement (EMA):**
```
e_new = e_old + γ · (grade − e_old)
```
where `e_old` is the decayed value from step 1 (or 0 if first probe), `grade` is the final grade after any dispute resolution.

**Stability (FSRS-inspired):**
- If `grade ≥ 0.5` (success):
  ```
  s_new = s_old · (1 + 0.6 · (1 − e_decayed_before_probe))
  ```
- If `grade < 0.5` (failure):
  ```
  s_new = max(7, s_old · 0.5)
  ```
- For first probe, `s_old` is the default for the claim's `evidence_type`:
  - `theoretical`, `meta-analysis`, or no evidence_type: 180 days
  - `experimental`, `observational`: 90 days
  - `computational`: 60 days
  - Synthesis claims (`type: synthesis`): 90 days default (inheritance from composed_from is a v2 read-time concern; the stored value can be the default)

### 7. Write the frontmatter

Use the Edit tool to update the claim's `engagement` block. Patterns:

- If the block doesn't exist yet, insert it as the last frontmatter key before the closing `---`.
- If the block exists, update `engagement.axes[axis]` and `engagement.stability[axis]` for each tested axis, and update `engagement.last_tested` to today's ISO date.
- Untested axes are **not touched** — leave them as null or their existing value.

Be precise with YAML formatting. The block must remain parseable:

```yaml
engagement:
  axes:
    mechanism: 0.6
    implications: null
    falsifiability: 0.85
    bounds: null
  stability:
    mechanism: 95
    falsifiability: 90
  last_tested: 2026-05-12
```

### 8. Append history line

The claim file should have an `## Engagement Log` section at the very bottom (after `Research Areas:`). If it doesn't exist, create it. Append one line per `/no-surrender` invocation:

```markdown
## Engagement Log

- 2026-05-12 cooperative — mechanism:0.55 falsifiability:0.85 — first probe
```

Format: `- <date> <mode> — <axis>:<value> <axis>:<value> — <note>`

Notes:
- `<mode>`: `cooperative` (v1 default) or `adversarial` (v2+)
- `<note>`: `first probe`, `re-probe`, `dispute-bumped`, etc. — terse
- One line per invocation; do not regenerate the whole log

### 9. Print summary

End each claim's session with:

```
Updated engagement for [[claim-title]]:
  mechanism:        0.0  → 0.55   (s: 180 → 226 d)
  falsifiability:   null → 0.85   (s: -   → 90 d, default)

Aggregate engagement (mean over all 4 axes): 0.35
Aggregate before this probe: 0.0

next /no-surrender suggested in ~<half-life-estimate> days
```

`<half-life-estimate>` ≈ `min(stability) · ln(0.5) / ln(0.9)` ≈ `min(s) · 6.58` days, but cap suggestion text at "~90 days" if the value is larger — long-horizon precision isn't useful.

## Multi-claim flow (topic MOC, --weakest, --recent-since)

For multi-claim targets, run claims **sequentially** (not parallel — the user is in the loop):

1. Announce: "Found N claims to test. I'll go one at a time. Type /stop to end the session at any point."
2. For each claim, run the full per-claim workflow.
3. Between claims, ask: "Continue? (y/stop)". This is the friction valve — the user can bail without losing prior writes.
4. If the user stops, summarize what was completed and what remains.

## Constraints (the friction guardrails)

- **Time budget per claim: 90 seconds of user interaction.** If you find yourself asking the user to revise a probe answer 3+ times or the user is generating long answers, *move on*. Friction kills usage.
- **Never reveal the claim body verbatim before grading.** Showing the answer before testing collapses the test. After grading is fine.
- **One write per claim per invocation.** Do not edit the frontmatter multiple times during the session — collect all axis updates, then write once at step 7.
- **Be honest in the rationale.** "You missed X" is the value of the verb. Sycophancy ("great answer!") on a 0.3 grade is the failure mode this whole system exists to prevent.

## Failure modes to resist

- **Leading probes.** If the probe contains the answer ("Why does X cause Y due to Z mechanism?"), the test is broken. Re-write before asking.
- **Generous grading.** A "kind of" answer is not 0.85. The rubric is the rubric. Bias toward lower scores; users can dispute up if they actually engaged.
- **Probing all 4 axes on first contact.** Tempting for completeness; fatal for friction. Two axes per session, max.
- **Forgetting the gate check.** Every invocation starts with reading `vault.yaml`. No exceptions, even if the gate just got flipped in the previous call.
- **Writing to untested axes.** If the user is tested only on `mechanism`, only `mechanism` updates. Leave the others as they were.
- **Auto-running `/teach` on failure.** Out of scope for v1. If the user fails badly, suggest they read the claim body or related claims; do not start teaching.

## When to spawn a subagent

Default: inline. Spawn a subagent only for `--weakest=N` with N > 20 where finding the candidates requires scanning many files. The interactive probing itself must stay inline — subagents and conversational testing don't mix.

## Tools

- `Read` — claim files, vault.yaml
- `Edit` — frontmatter and Engagement Log updates
- `Glob` — resolve `_<topic-map>` to claim list, find claims by pattern
- `Grep` — `--weakest=N` and `--recent-since=Nd` modes
- `Bash` — date arithmetic (computing `Δt` from `last_tested`)

## Probes reference

See `probes.md` for axis-to-probe templates, first-probe vs re-probe axis selection heuristics, and the grading rubric expanded with examples.

## Output channel

All probe Q&A and summaries are printed to chat. No external state, no separate output files. The claim file's frontmatter and `## Engagement Log` section are the only persistent writes.
