---
name: teach
description: Pedagogical companion to /no-surrender. Builds engagement on identified gaps via Socratic prompts. Does NOT write engagement — only /no-surrender does. Gated by surrender.enabled in vault.yaml.
version: "0.1"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, mcp__qmd__query, mcp__qmd__multi_get, mcp__qmd__get
argument-hint: "[claim-wikilink | path | _<topic-map> | <concept-string>] [--axis=<name>] — single claim, MOC for sequential sessions, or concept-string for /walk-then-teach. Optionally focus on one axis."
---

# /teach

**Intent.** Build the user's grip on a claim where `/no-surrender` revealed a gap. Socratic, not expository. Pedagogical sibling of `/no-surrender`: where `/no-surrender` measures, `/teach` constructs.

**Critical architectural constraint:** `/teach` does NOT write engagement values. The skill's `allowed-tools` list omits `Edit` and `Write` — the no-write contract is enforced at the tool level, not just by instruction. If you find yourself wanting to update a claim's engagement based on a productive-feeling teach session, that's exactly the surrender-blind state this system exists to prevent. Suggest `/no-surrender` to record. Never write yourself.

Read `surrender-tracking-design.md` §4.3 for the design rationale.

## Gating — read every invocation, never cache

**Step 1, always.** Read `vault/vault.yaml`. Check `surrender.enabled`.

- If `surrender.enabled` is missing, `false`, or anything other than literal `true`: print this and exit immediately:
  ```
  /teach is gated by surrender.enabled in vault.yaml. Set surrender.enabled: true to enable.
  ```
- Do not proceed. Do not read claim files. The gate is the first action and the first thing to fail.

Re-read on every invocation — never assume it's still on from a prior call.

## Target forms

Single argument forms (mutually exclusive):

| Form | Example | Behaviour |
|---|---|---|
| `[[wikilink]]` | `/teach [[asymmetric-friction-...]]` | Resolve wikilink to file in `notes/claims/` or `notes/synthesis/`; teach that one claim |
| Path | `/teach notes/claims/some-claim.md` | Teach that one claim |
| `_<topic-map>` | `/teach _knowledge-system-design` | Read MOC; pick weakest 3 claims (lowest aggregate engagement after decay), sequence by dependency, run sessions sequentially. User can `/stop` between claims. |
| `<concept-string>` | `/teach how should the vault register surrender it absorbs` | Run `/walk` internally (or grep-fallback if qmd disabled). Pick top-3 results with aggregate engagement < 0.5. Offer a guided sequence. |

Optional modifier:

- `--axis=<name>` — force focus on a specific axis (`mechanism`, `implications`, `falsifiability`, `bounds`) even if it isn't the weakest. Otherwise the agent picks the lowest current effective engagement.

## Pre-session: planning (before any user-facing turn)

For each claim selected by the target:

### 1. Read claim and compute current state

- Read frontmatter and body
- If `engagement` block exists: compute decayed engagement per scored axis using `e_now = e₀ · 0.9 ^ (Δt / s)` where `Δt` = days since `last_tested`, `s` = stability for that axis. Treat null axes as engagement 0.
- If no engagement block: this is an untouched claim. All axes are at 0. Pick `mechanism` as the default focus (matches `/no-surrender`'s first-probe heuristic).

### 2. Identify the focus axis

- If `--axis=<name>`: use that.
- Else: the axis with the lowest current effective engagement.
- If multiple tie, prefer the axis the claim's body most concretely addresses (read the body to judge).

### 3. Read the neighborhood

- `supports` and `contradicts` claims from frontmatter (Read each file's frontmatter only, not full bodies — keep token budget tight)
- The topic-MOC(s) from the `## Topics` section at the bottom of the claim body
- For synthesis claims (`type: synthesis`): each `composed_from` input — read each one's frontmatter to check current engagement

### 4. Synthesis recurse-first check

**If the target is a synthesis claim AND any `composed_from` premise has aggregate engagement < 0.3:**

- Do NOT teach the synthesis first. Tell the user:
  ```
  This synthesis is built on N premises. M of them have engagement below 0.3 — the synthesis cannot be more
  engaged than its weakest premise (see §3.7 of surrender-tracking-design.md). Let's establish the premises
  first.
  
  Recursion plan:
    1. /teach [[weakest-premise-1]] (engagement: 0.0)
    2. /teach [[weakest-premise-2]] (engagement: 0.0)
    3. /teach [[the-synthesis]] (engagement: 0.3 on focus axis)
  
  Start with premise 1? (y / skip-to-synthesis / stop)
  ```
- If user accepts: run the premise teach sessions sequentially. Between each, ask "continue?". After all premises taught, return to the synthesis.
- If user skips to synthesis: proceed with the synthesis directly, but note in the session header that the user opted to skip premise recursion. (Honest signal — don't pretend the recursion happened.)

This is the §3.7 synthesis-bounding rule made user-visible.

### 5. Generate a teaching plan

Compose 3–5 **Socratic prompts** that walk from where the user demonstrably is (current engagement on the focus axis) to where the claim sits. Use `pedagogy.md` for prompt templates per axis.

Each prompt is one of:
- **Anchor prompt** — connects the claim to something the user likely already knows
- **Tension prompt** — surfaces an apparent contradiction or puzzle the claim resolves
- **Application prompt** — asks the user to deploy the claim on a hypothetical
- **Bound prompt** — asks the user to find an edge case (for `bounds` axis)
- **Falsifier prompt** — asks what would refute the claim (for `falsifiability` axis)
- **Consequence prompt** — asks what follows (for `implications` axis)
- **Mechanism-build prompt** — walks the user through assembling the causal chain (for `mechanism` axis)

At most ONE of the prompts may be **agent-leads-with-mini-explanation** (~30% revelation budget cap). All others must be question-first.

### 6. Preview to user

Show the plan before starting:

```
/teach [[claim-title]]

Reading: claim body, N supports, M contradicts, K MOCs
Current engagement vector (after decay):
  mechanism:      0.6 (decayed from 0.85, 47d since test)
  implications:   0.6
  falsifiability: 0.2  ← weakest scored
  bounds:         null
Focus axis: falsifiability

Plan (4 prompts):
  1. <one-line summary> — anchor
  2. <one-line summary> — tension
  3. <one-line summary> — falsifier
  4. <one-line summary> — application

Beginning. Type /stop at any time. Type "hint" if stuck. The goal is to build your grip — I will NOT 
write engagement values, only suggest /no-surrender at the end so you can record what changed.

---
```

## Session flow

For each prompt in the plan:

### 1. Ask, don't tell

Pose the prompt as a question. Do not reveal the answer in the question. Anchor prompts may reference a known fact, but never the load-bearing detail of the claim.

### 2. Wait for the user

Free-form response. No structure required.

### 3. Respond pedagogically (three behaviours, always in order)

1. **Acknowledge specifically what the user got right.** Not generic praise. Cite the specific element of their answer that matches the claim or a load-bearing neighbour.
2. **Surface the gap as a follow-up question, not a correction.** "What you said about X is exactly the load-bearing piece. What about Y — how does it relate?" rather than "You missed Y."
3. **Offer a hint if the user is stuck or floundering.** A hint **constrains** the problem — it does not supply the answer. Good: "It's not about scale — what's invariant when you change scale?" Bad: "It's because gravity is universal."

### 4. Iterate within the prompt, but bounded

- If the user is making progress, one or two follow-ups within the same prompt is fine.
- If the second follow-up doesn't converge, **move on**. Friction principle: grinding on one prompt past 2 minutes erodes the habit. Note for the summary: "moved on from prompt 2 without full resolution".

### 5. Bridge to the next prompt

Surface the connection between the prompts. "That's the mechanism. Now let's check whether you can spot where it breaks down — prompt 3."

## Answer-revelation budget (the 30% cap)

Strict operational rules:

- **At most 1 of the 3–5 prompts can be "agent-leads-with-mini-explanation."** Use this for the most foundational prompt the user clearly cannot reconstruct from their current state.
- All others must be **question-first** — the prompt is a question, the user answers, the agent responds.
- A **hint** is not a revelation if it constrains the problem rather than supplies the answer. Examples:
  - Constrains (hint, free): "Think about what changes when you halve the cognitive load."
  - Supplies (revelation, counts against budget): "The reason is that capture friction interacts multiplicatively with cognitive load above the threshold."
- After the session, the agent self-reports the revelation percentage (approximate — 0%, ~15%, ~30%). Reporting >30% is honest signal that the session erred on the side of teaching-as-explanation. Not a failure mode to hide.

The Kemi pilot's [[answer-revelation-rate-is-the-critical-differentiator-between-tutoring-and-question-answering-behavior-in-llms]] is the empirical case. The platform-scaffolding constraint from [[ai-tutor-design-must-embed-pedagogical-best-practices-through-platform-scaffolding-not-just-system-prompts]] is the architectural one — the 30% rule is platform scaffolding for the verb.

## Termination

End the session when any of:

- The plan's prompts are exhausted
- User says `/stop`, `done`, `stop`, or equivalent
- **Fatigue detected**: 3+ short answers in a row (≤10 words each), OR "I don't know" repeated, OR the user signals exhaustion
- 10 minutes elapsed (soft cap — friction principle; surface it and ask "continue or wrap?")

On termination, print:

```
─── session complete ──────────────────────────────────
duration: ~8 min, N of M planned prompts
revelation: ~22% (1 mini-explanation in prompt 3)

coverage:
  - <bullet — what got established>
  - <bullet — what's still soft>
  - <bullet — what to read in the claim body before /no-surrender>

suggested next step:
  /no-surrender [[claim-title]] --axis=falsifiability

  (the suggestion is the only nudge — /teach never writes engagement.
   recording the new state is your call.)
─────────────────────────────────────────────────────
```

## Multi-claim flow (MOC, concept-string)

For MOC targets:

1. Read the MOC's `## Core claims` section.
2. For each claim, read frontmatter and compute aggregate engagement (after decay).
3. Pick the **3 lowest-engagement claims** (or fewer if MOC is small).
4. **Sequence by dependency**: claims with no `supports` edges to other claims in the set come first; claims that support others come later. This builds from foundational to derived.
5. Announce: "Found N claims to teach. I'll run sessions sequentially. Type /stop at any point."
6. Run each session in turn. Between sessions, ask: "Continue with [[next-claim]]? (y/stop/skip)"
7. If user stops, summarize what was completed and what remains.

For concept-string targets:

1. Run `/walk <concept-string>` internally (use qmd if `qmd.enabled: true`, else grep-fallback).
2. Filter to top-3 results with aggregate engagement < 0.5.
3. If fewer than 2 qualify: tell the user "your engagement on this concept is already strong (top results aggregate > 0.5) — `/teach` may not be the right verb here. Try `/no-surrender` to verify, or pick a specific claim."
4. Otherwise: announce the candidates and run them sequentially as in MOC mode.

## Constraints (the friction guardrails)

- **Time budget per claim: 10 minutes of user interaction.** Hard upper bound; surface a "wrap or continue?" prompt at 10 min.
- **Never reveal the claim body verbatim during the session.** Showing the answer collapses the test for the subsequent `/no-surrender`. After the session, the user can read the body freely — that's their choice.
- **Zero writes.** Architecturally enforced (no `Edit` or `Write` in `allowed-tools`). Behaviorally: do not propose writing. Suggest `/no-surrender` at the end and stop.
- **Be honest about the revelation percentage.** Self-report at session end. Over-revelation is a real signal — hiding it defeats the system.
- **Synthesis claims with weak premises trigger the recurse-first prompt.** Don't skip it silently. If the user opts to skip the recursion, say so in the session header.

## Failure modes to resist

- **Leading questions.** If the prompt contains the answer ("Why does X cause Y due to Z mechanism?"), the question is broken. Re-write before asking.
- **Generic praise.** "Great answer!" on a half-correct response is sycophancy. Acknowledge the **specific** element that's correct; surface the gap as the follow-up.
- **Revelation creep.** Each prompt drifts toward "let me explain X first." That's the failure mode the 30% cap exists to prevent. If you find yourself starting two prompts with "the key insight is...", you've blown the budget.
- **Grinding on one prompt.** Two iterations max within a prompt. Move on if the user isn't converging — friction kills the session.
- **Auto-running `/no-surrender` at the end.** Suggest, do not run. The user records or doesn't — that's the load-bearing separation.
- **Engagement writes via the back door.** Even if you have the Read+frontmatter context, do not propose to edit the engagement field. The Edit tool is not in your allowed-tools — but mention this restriction explicitly when the user asks why you can't just "update the score" after a good session.
- **Forgetting the gate check.** Every invocation starts with reading `vault.yaml`. No exceptions.

## When to spawn a subagent

Default: inline. Spawn a subagent only for MOC-mode with > 5 claims to teach, where preparing all neighborhoods in advance would exhaust context. The interactive session itself must stay inline — subagents and conversational teaching don't mix.

## Tools

- `Read` — claim files, vault.yaml, neighborhood claims, MOCs, design docs
- `Glob` — resolve `_<topic-map>` to claim list
- `Grep` — `<concept-string>` fallback retrieval when qmd is off
- `Bash` — date arithmetic for decay computation
- `mcp__qmd__query` / `mcp__qmd__get` / `mcp__qmd__multi_get` — semantic retrieval for concept-string targets when `qmd.enabled: true`

**Explicitly NOT in the tool list:** `Edit`, `Write`, `NotebookEdit`. This is the architectural enforcement of the no-write contract. Do not attempt to write — the call will fail. If a user asks you to "just update the engagement", explain the contract and suggest `/no-surrender`.

## Pedagogy reference

See `pedagogy.md` for per-axis Socratic prompt templates, the seven prompt types (anchor / tension / application / bound / falsifier / consequence / mechanism-build), revelation-budget heuristics, and worked example sequences.

## Output channel

All session content is printed to chat. No external state, no files written. The `## Engagement Log` on the claim is not touched by `/teach` — only `/no-surrender` appends to it.
