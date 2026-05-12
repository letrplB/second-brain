# Pedagogy reference — Socratic prompt templates and session heuristics

Reference for `/teach`. Templates and rules for building 3–5 prompt teaching plans that stay question-first and under the 30% revelation budget.

---

## The seven prompt types

Each prompt in a teaching plan plays one of these roles. A good plan uses 2–4 of these types in sequence — not all seven, not the same one repeated.

| Type | What it does | When to use it | Counts against revelation budget? |
|---|---|---|---|
| **anchor** | Connects the claim to something the user demonstrably already knows. The opening of most sessions. | Always available as the opening prompt. Especially valuable when current engagement is 0 (no prior probe). | No (referencing user's prior knowledge, not revealing claim content) |
| **tension** | Surfaces an apparent contradiction or puzzle the claim resolves. Pulls the user into wanting the answer. | When the claim contradicts a common intuition or resolves a tension. | No |
| **application** | Asks the user to deploy the claim on a hypothetical, near-case, or analogous situation. | Mid-session, after some grip is established. | No |
| **bound** | Asks the user to find an edge case where the claim breaks. | When targeting the `bounds` axis. Late in the plan. | No |
| **falsifier** | Asks what evidence would refute the claim. | When targeting the `falsifiability` axis. | No |
| **consequence** | Asks what follows from the claim — what it forbids or enables. | When targeting the `implications` axis. | No |
| **mechanism-build** | Walks the user step-by-step through assembling the causal chain. May include a mini-explanation if the chain has a non-obvious link. | When targeting the `mechanism` axis AND the user has shown they cannot reconstruct it from prompts alone. | **Yes** — typically the single budget-eligible prompt. |

---

## Prompt templates per axis

### Targeting `mechanism`

The user needs to explain *why* the claim holds — the causal/structural reason.

**Anchor prompts:**
- "Before we touch the claim itself: what do you already know about `<adjacent concept>` and why it works that way?"
- "What's a related situation where the same kind of reasoning applies? Walk me through that one."

**Tension prompts:**
- "Naive intuition says X. The claim says Y. What's the asymmetry that makes Y correct?"
- "If `<simple model>` were the whole story, we'd expect `<wrong consequence>`. Why doesn't that happen?"

**Application prompts:**
- "Suppose `<hypothetical with the same shape>`. Would the claim's mechanism predict the same outcome? Walk it through."

**Mechanism-build prompt** (the one budget-eligible slot, used carefully):
- Walks the user from step 1 to step 3 of a 4-step chain, asking the user to fill in step 4
- "We've established that A leads to B, and B has property P. What does P imply about how A interacts with C?"

### Targeting `implications`

The user needs to deploy the claim — what does it forbid, enable, predict?

**Anchor prompts:**
- "Set the claim aside for a moment. What other beliefs do you hold about `<surrounding domain>`?"

**Consequence prompts (load-bearing for this axis):**
- "If the claim holds, what *can't* be true? Name something that would be inconsistent with it."
- "What design move does this rule out, that you might otherwise be tempted to make?"
- "What previously-defensible position does this now make untenable?"

**Application prompts:**
- "You're designing `<concrete future thing>`. What does the claim tell you to avoid? What does it open up?"

### Targeting `falsifiability`

The user needs to articulate the counterfactual world the claim rules out.

**Anchor prompts:**
- "What would it look like if the claim were *wrong*? Don't argue for it being wrong — just describe a world where it doesn't hold."

**Falsifier prompts (load-bearing):**
- "What evidence would shift your confidence in this claim downward?"
- "If you wanted to falsify the claim — design the experiment. What would you measure?"
- "What's the strongest counterexample someone could bring, and why would it (or wouldn't it) matter?"

**Tension prompts:**
- "If the claim survives `<easy counter>`, why? What's the asymmetry?"

### Targeting `bounds`

The user needs to locate where the claim stops applying.

**Anchor prompts:**
- "Think about scale. At what scale does this claim live? What happens at scales much larger or smaller?"

**Bound prompts (load-bearing):**
- "Name a regime where you'd hesitate to apply this claim."
- "If a colleague tried to apply this to `<obviously inappropriate domain>`, what would you tell them to look out for?"
- "Where's the boundary between 'this clearly applies' and 'this clearly doesn't'? Describe both sides."

**Application prompts:**
- "Take an edge case — `<borderline regime>`. Walk through whether the claim applies there."

---

## Constructing the plan: a heuristic

For a 4-prompt session targeting **`falsifiability` on a synthesis claim**, a reasonable plan shape:

1. **Anchor** — connect to a related claim the user has engaged with
2. **Tension** — surface the puzzle the synthesis resolves
3. **Falsifier** — the load-bearing axis prompt: what would refute this?
4. **Application** — deploy on a hypothetical

For a 3-prompt session targeting **`mechanism` on a fresh claim** (no prior engagement):

1. **Anchor** — establish what the user knows about the subject
2. **Mechanism-build** — walk the chain with one mini-explanation slot used
3. **Application** — does the mechanism reproduce on a near-case?

For a 5-prompt session targeting **`bounds` on a heavily-cited claim** (prior engagement on other axes already high):

1. **Anchor** — recall the claim's mechanism (already known)
2. **Bound** — find one edge case
3. **Bound** — find another in a different regime
4. **Tension** — surface where the user's edges conflict
5. **Application** — given the edges, predict behaviour in a new case

The plan shape is not rigid. **Aim for variety** — 2+ different prompt types per plan. Five anchors in a row is not Socratic, it's a quiz.

---

## Hints — the rule

A hint is **constraint, not supply**.

| Good hint (constraint) | Bad hint (supply) |
|---|---|
| "Think about what doesn't change when you change the scale." | "It's because gravity is universal." |
| "What kind of feedback loop would have to exist for this to be stable?" | "It's a negative feedback loop — the system corrects itself." |
| "What does the claim assume about the observer's position?" | "It assumes the observer is inside the system, not outside." |

A hint that constrains is free (does not count against the 30% revelation budget). A hint that supplies the answer counts as revelation.

If you find yourself drafting a hint and you can't tell which category it falls into, ask: *would the user still need to derive the answer from this hint, or have I handed it to them?*

---

## Acknowledging the user — specifically

When the user partially answers, the acknowledgement must reference **the specific element** they got right. Not the body of their answer — the load-bearing element.

| Generic (bad) | Specific (good) |
|---|---|
| "Great answer!" | "The part about feedback timing is exactly load-bearing — and you named it without prompting." |
| "Yes, you're on the right track." | "You spotted the asymmetry between capture and verification. That's the move. The piece you haven't named yet is why one direction must be effortless." |
| "Correct." | "You captured the mechanism. Now the question is whether the mechanism survives scale-up." |

The specificity is the value. Generic praise is sycophancy; the system exists to prevent that failure mode.

---

## Surfacing gaps — as follow-up, not correction

When the user's answer misses a load-bearing detail, frame the gap as a **next question**, not a correction.

| Correction (bad) | Follow-up (good) |
|---|---|
| "You missed the part about runtime enforcement failing." | "What you said about asymmetry is right. What about *why* the user can't enforce it themselves at runtime?" |
| "That's not quite right — the mechanism is different." | "You named one mechanism. The claim points at a different one — what could it be, given the same setup?" |
| "Actually, the claim is about X, not Y." | "Y is a related claim, and it would also fit your description. What makes you think it's Y and not X?" |

The follow-up keeps the user *in the work*. The correction kicks them out of it.

---

## When to move on within a prompt

After **two follow-ups** within the same prompt, if the user isn't converging:

- Acknowledge progress honestly: "We've spotted the asymmetry but the underlying reason is still soft. Let's come back to it after the next prompt — context might help."
- Move to the next prompt.
- In the session summary at the end, list this prompt as **"moved on without full resolution"** — honest signal for the user's `/no-surrender` decision.

Two follow-ups = ~90 seconds of grinding on one question. Past that, the friction kills the session.

---

## Self-reporting revelation percentage

At session end, estimate the revelation percentage and report it honestly.

Reference points:

- **0%** — every prompt was question-first; no agent-led explanations; hints were all constraint-form
- **~15%** — one short mini-explanation slot used; the rest question-first
- **~30%** — one full mini-explanation (the budget-eligible slot used to its limit)
- **>30%** — multiple prompts drifted toward explanation; honest signal that the session erred on the side of teaching-as-telling. Note it; suggest the user re-test via `/no-surrender` more strictly than they otherwise would, since the engagement coming out of a high-revelation session is less robust.

Reporting >30% is **not a failure mode to hide**. It's the most useful signal the system produces — the user knows the engagement is shakier than a 0%-revelation session would have left it.

---

## Worked example — teaching `mechanism` on the asymmetric-friction synthesis

The synthesis: *capture must be effortless, verification must be architecturally friction-rich, because unreliable-agent properties must be relocated from runtime enforcement to design-time architecture.*

A 4-prompt plan targeting `mechanism`:

**Prompt 1 (anchor):**
"Before the synthesis itself: think about Goodhart's law in general. What happens when an observable becomes a target? Walk me through the mechanism in one example you know — code coverage, GDP, anything."

(User describes how the observable diverges from the load-bearing variable under optimization pressure. Acknowledge specifically what they got right.)

**Prompt 2 (tension):**
"OK — so observables get gamed. That suggests we should hide our metrics, or rotate them often. But the synthesis says something different: it says the structural countermeasure is architectural, not metric-design. What's the asymmetry that makes 'design-time architecture' a different kind of move than 'better metric'?"

(User has to surface that runtime metrics — even good ones — can be optimized against; design-time architecture is the load-bearing variable made structural.)

**Prompt 3 (mechanism-build, budget-eligible):**
"Let's build the chain. Step 1: model can't reliably self-calibrate. Step 2: user can't reliably calibrate against an unreliable model. Step 3: these two failures are independent of each other — neither side can fix it from their end. Given that — fill in step 4: what's the only remaining option for ensuring honesty in the system?"

(This prompt walks the user from three established premises to one inference. The mini-explanation is the three premises; the user fills step 4. This is the one revelation-eligible prompt in the plan.)

**Prompt 4 (application):**
"You're designing a feature where an agent generates content for the user. The agent's calibration is poor. The user's verification rate is empirically ~27%. Based on the synthesis: what's the *wrong* design move, and what's the right one?"

(User deploys the synthesis on a concrete case. Tests transfer — does the user own the principle enough to use it.)

Estimated revelation: ~20% (Prompt 3 used its slot; others were question-first). Self-report at end.

---

## What pedagogy.md does NOT cover

- **Grading.** That's `probes.md` for `/no-surrender`. `/teach` does not grade.
- **Engagement scoring formulas.** Same — those are in `no-surrender/SKILL.md` and `surrender-tracking-design.md`.
- **Adversarial probing.** That's v2 `/no-surrender` mode, not `/teach`. Adversarial is calibration-test; `/teach` is constructive.
