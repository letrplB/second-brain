# Probe templates and axis-selection heuristics

Reference for `/no-surrender`. Templates and rules for generating axis-specific probes that test user engagement without revealing the claim body.

---

## The four axes

### `mechanism` — *Why* does the claim hold?

The causal or structural reason. Tests whether the user has internalized the *engine* of the claim, not just its statement.

**Template probes** (pick one, adapt to the claim subject):

- "Why is `<claim subject>` true? Walk me through the underlying process."
- "What's actually happening that makes `<X>` produce `<Y>`?"
- "If a smart skeptic asked you 'but *why* does this work?' — what would you tell them?"
- "What's the causal step you'd point to as the load-bearing one?"

**Don't ask:** "Is the mechanism X?" — leading. "What does the claim say about the mechanism?" — just asks for paraphrase.

### `implications` — What *follows* from the claim?

What the claim enables, forbids, or implies for the surrounding domain. Tests whether the user has *deployed* the claim mentally.

**Template probes:**

- "If `<claim>` holds, what else must be true?"
- "Name something that would be inconsistent with this claim."
- "What would change in your understanding of `<domain>` if you fully accepted this?"
- "What does this rule *out*?"

**Don't ask:** "What are the implications?" — too abstract; the user can stall on phrasing without engaging.

### `falsifiability` — What would *refute* the claim?

The counterfactual world the claim rules out. Tests whether the user could distinguish the claim from its negation.

**Template probes:**

- "What evidence would convince you this is wrong?"
- "Describe a world where this would *not* hold — what would be different?"
- "If you were trying to falsify this, what experiment or observation would you target?"
- "What's the strongest counter-case that would actually move your confidence down?"

**Don't ask:** "Is this falsifiable?" — yes/no, not engagement.

### `bounds` — Where does the claim *stop* applying?

Scope, edge cases, regime conditions. Tests whether the user has located the claim's domain of applicability.

**Template probes:**

- "When does this *not* hold? Name an edge case."
- "What conditions need to be true for this to apply?"
- "Can you think of a regime — different scale, different system, different domain — where you'd hesitate to apply this?"
- "If I gave you a borderline case, how would you decide whether the claim applies?"

**Don't ask:** "What are the bounds?" — too abstract.

---

## First-probe axis selection

When a claim has no prior `engagement` (first probe), pick **`mechanism` plus one secondary**. The secondary is chosen by the claim's `evidence_type` and `tags`:

| Claim shape | First-probe axes |
|---|---|
| `evidence_type: theoretical` or `meta-analysis` | mechanism + falsifiability |
| `evidence_type: experimental` or `observational` | mechanism + bounds |
| `evidence_type: computational` | mechanism + bounds |
| `methods` tag present, or method-focused claim | mechanism + bounds |
| `type: synthesis` | mechanism + implications (because synthesis claims live by what they enable) |
| Mixed or unclear | mechanism + falsifiability (safe default) |

**Why `mechanism` always**: it's the most universally applicable axis — every claim has a "why does this hold" question. Use it as the anchor.

**Why limit to 2 axes**: the friction principle. 3+ axes in one session pushes user time over 90 seconds and erodes habit. The other axes can be probed later.

---

## Re-probe axis selection

When a claim has prior `engagement`:

1. Compute decayed engagement for each scored axis.
2. Target the axis with the **lowest current effective engagement**.
3. If a second axis is below 0.5 after decay, add it (up to 2 axes total).
4. If the user invokes with `--axis=<name>`, force that axis (overrides 1–3).
5. If all axes are above 0.7 after decay: still test one — pick the one with the longest `Δt` since last test. The point is to refresh and verify, not to skip.

Untested axes (those still `null` after prior probes) are eligible for re-selection — treat them as engagement = 0 for the "lowest current" comparison.

---

## Grading rubric — expanded with examples

For each axis, after the user answers:

| Score | Pattern | Example (claim: *electrostatic interactions are the dominant driver of protein adsorption onto silica with maximum loading near the protein isoelectric point*) |
|---|---|---|
| 0.0 | Contradicts the claim, or wrong subject entirely | "Adsorption is driven by van der Waals forces; pI doesn't matter." |
| 0.3 | Surface match, missing the core | "It has to do with charges and pH." |
| 0.6 | Substantial match, notable omission | "Maximum loading is near pI because charges minimize; at low pH you get electrostatic attraction but protein-protein repulsion limits packing." (missing: salt screening effect, the silica pKa context) |
| 0.85 | Full match, correct paraphrase, captures load-bearing detail | Above answer plus: "and adding salt at low pH screens inter-protein repulsion, raising loading further." |
| 1.0 | Match plus correct connection / generalization | "...same charge-mediated mechanism applies at the cell-membrane scale where positively charged NPs prefer CME; both are electrostatic-driven binding." |

**Calibration notes:**

- Bias toward *lower* scores. Users can dispute up. Generosity defeats the test.
- A correct *partial* answer with a clear missing piece is 0.6, not 0.85. The dispute mechanism handles edge cases where the user can articulate the missing piece on a second pass.
- 1.0 requires going beyond the claim's stated content — connecting to neighbours, generalizing correctly, or naming an implication the claim doesn't explicitly state. Don't hand out 1.0s for excellent paraphrase; that's 0.85.

---

## Dispute mechanism

If the user disputes the grade in their next message:

- **Substantive** (cites claim body text, names a missed nuance, provides reasoning that *was implicit in the original answer*): bump grade by `+0.1`, capped at the rubric band for the user's actual demonstrated understanding (including dispute content).
- **Trivial** ("I disagree", "but I knew that"): no bump. Respond: "Noted — without elaboration the grade stands." Move on.
- **Hostile** (frustration, refusal to engage): de-escalate. "We can re-test later — moving on without an update for this axis." Skip the write for that axis.

Dispute itself is engagement. The user who can defend an answer post-grading has demonstrated more grip than the user who silently accepts. Reward the engagement; don't enable false-confidence inflation.

---

## Probe-writing checklist

Before sending a probe to the user, check:

- [ ] Does NOT contain the answer or load-bearing keywords from the claim body
- [ ] Phrased as an open question, not yes/no
- [ ] Answerable in 1–3 sentences (not "write an essay")
- [ ] Targets the specific axis, not generic comprehension
- [ ] Uses the claim's subject in plain language (so the user knows what's being asked about) without quoting the claim's exact phrasing

If any box fails, rewrite.

---

## Examples — first probes for representative claims

### Claim: *"capture friction above 10 seconds of manual effort causes knowledge capture habits to collapse"*

Evidence type: observational. First probe axes: mechanism + bounds.

- mechanism: "Why does a 10-second friction threshold collapse a capture habit? What's the mechanism — psychological, behavioural, structural?"
- bounds: "When would this *not* apply? Can you think of a capture context where 10+ seconds of friction is still sustainable?"

### Claim: *"in knowledge work every observable degrades as a target which makes evals themselves recursively corruptible"* (synthesis)

Type: synthesis. First probe axes: mechanism + implications.

- mechanism: "Why does every observable degrade as a target in this domain? What's the structural reason this is *systematic*, not coincidental?"
- implications: "If you accept this synthesis, what does it forbid you from doing when designing future vault tooling?"

### Claim: *"GPT-4 reports confidence 4.0/5 on incorrect safety answers; most models show no meaningful correlation between stated confidence and correctness"*

Evidence type: experimental. First probe axes: mechanism + bounds.

- mechanism: "Why would a model emit high stated confidence on wrong answers — what's the underlying reason calibration breaks for chemistry safety specifically?"
- bounds: "Where does this calibration failure stop? Are there domains or question types where stated confidence *would* correlate with correctness?"
