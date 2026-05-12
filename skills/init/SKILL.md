---
name: init
description: Scaffold a new second-brain vault. Two modes — guided (no args, conversational onboarding) and quick (preset name + optional domain + optional --at path).
version: "0.1"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob
argument-hint: "[preset] [domain] [--at <path>] — leave empty for guided setup. Or specify preset (research|personal), an optional domain string, and an optional vault path."
---

# /init

**Intent.** Lay down a new vault. Either by talking with the user (guided mode) or by accepting preset + domain on the command line (quick mode). Same scaffolding step at the end; the modes only differ in *how the placeholders get filled* and *how the location is chosen*.

**Refuses to overwrite.** If the resolved target directory already exists and is non-empty, abort with a clear error.

## Modes

### Guided (default — no arguments)

A focused conversation: ~7 questions, a review-and-confirm step, then scaffold. **Use this when starting a new vault from scratch and you want it to fit your work.**

### Quick (preset specified)

`/init research [domain] [--at <path>]` or `/init personal [--at <path>]`. Scaffolds immediately with sensible defaults; you edit afterwards. **Use this when you know what you want, or when you're scripting setup.**

A future `hybrid` preset is reserved but not yet shipped.

---

## Resolving where the vault lives

This is the same logic in both modes — the difference is *whether the user is asked* or *whether a default is taken silently*.

The model has access to the user's current working directory (the directory Claude Code was invoked from). Call this `$CWD`.

**Default proposal:** `$CWD/vault/`.

**Path resolution rules:**
- Absolute paths used as-is (e.g. `/Users/bastian/notes/research-vault/`).
- `~/...` expanded to home.
- Anything else treated as relative to `$CWD`.

**Refusal cases (both modes — abort and explain):**
- The resolved path equals the plugin directory itself (the directory containing this `init/SKILL.md`'s grandparent). Vaults must not nest inside the plugin source.
- The resolved path exists and is non-empty.
- The resolved path is a parent of `$CWD` (likely a slip; ask user to confirm explicitly).

---

## Guided mode behaviour

The model conducts a focused interview. Each question shapes a specific part of the generated vault. After the answers are in, the model presents a *file plan* and asks for confirmation before any disk write.

### The questions

**Q1 — where should the vault live?**

> "I'll create a vault directory. Suggested location: `$CWD/vault/`. Type a different path if you want it elsewhere (absolute, relative to where you launched the session, or `~/...`). Press enter to accept."

The model echoes the resolved absolute path back so the user sees exactly what's about to be created. If the proposal collides with the plugin directory or an existing non-empty path, refuse and ask again.

**Q2 — what's this vault for?**

> "Describe in one or two sentences what this vault is for and what kind of content lives in it."

The model parses the answer to infer:
- **Preset:** research (paper- and claim-oriented, evidence-typed) | personal (memory- and identity-oriented, looser linking) | mixed (the user describes both — propose research with `self_space: true`, or hold for the future `hybrid` preset)
- **Domain string:** a short kebab-case slug derived from the user's description, used in `vault.yaml`, `index.md`, and CLAUDE.md substitutions. Show the proposed slug; let them override.

**Q3 — what topics do you already know you want to track?**

> "Any specific topics you already know will live here? List them as you'd describe them to a colleague."

The answers seed `notes/_<topic>.md` MOC scaffolds. Each topic becomes a real starter MOC — frontmatter filled, `## Core claims` empty (ready to fill), parent set to `[[index]]`. **Generate at most 5 starter MOCs**; if the user lists more, prompt them to pick the 5 most central or accept that the rest will be created on demand.

**Q4 — identity-anchored or impersonal?**

> "Do you want a `self/` directory for identity, goals, and values — i.e. is this vault personal-shaped, even if research-shaped on the surface?"

- Default for research preset: no.
- Default for personal preset: yes.
- The user can override either way.

**Q5 — vocabulary tweaks?**

> "Default vocabulary: claims (atoms), papers (sources), topic-maps (MOCs). Want any of those renamed for your domain?"

Read the preset's `vocabulary.yaml` as the starting point. Show it. Accept overrides. Write the resolved map into `vault.yaml`.

**Q6 — active threads right now?**

> "What's actively on your mind right now that this vault should help with? List up to ~5 active threads."

The answers populate the `active_threads:` list in `goals.md` (real content, not a `-` stub). Empty answer is fine — the file is still scaffolded with the YAML head.

**Q7 — assistant preferences?**

> "Anything you want the assistant to consistently flag, skip, or treat differently in this vault? Some examples to start from (pick any, override, or write your own):
> - 'Surface connections I haven't seen — especially across domains.'
> - 'Challenge my assumptions before agreeing.'
> - 'Answer from the vault first, fall back to general knowledge only when explicit.'
> - 'Flag when I contradict myself across claims.'
> - 'Mark inferences as inferences; don't assert profile-extrapolation as fact.'
> - 'Be direct. Skip closing pleasantries.'"

The example list is from the *Vault That Adds To You* framing — the highest-leverage preferences are the ones that make the vault talk back, not just nod along. Free-text answer becomes a `## Preferences` section appended to the generated `vault.md` (via the `{PREFERENCES_BLOCK}` placeholder). The model reads it on every session start.

### The review-and-confirm step

After Q7, the model summarises:

```
ready to scaffold. here's the plan:

  vault root:           /Users/bastian/SURA_workspace/vault/
  preset:               research
  domain slug:          ml-interpretability
  self/ directory:      no
  vocabulary:           claim, paper, topic-map (default)

  starter MOCs (3):
    - notes/_circuit-discovery.md
    - notes/_alignment.md
    - notes/_evals.md

  goals.md active threads (2):
    - "writing the survey"
    - "rerun nanda 2024 with claude-3"

  CLAUDE.md preferences:
    - flag claims that don't have replication info
    - don't auto-suggest links between journal/ and notes/

ok to proceed? (yes / edit / abort)
```

If the user says **edit**, the model offers to revise specific lines (Q-by-Q) without redoing the whole conversation.

If the user says **yes**, scaffold (see "Shared scaffold" below).

If **abort**, exit cleanly with no disk writes.

---

## Quick mode behaviour

`/init research` or `/init research <domain>` or `/init personal [--at <path>]` etc.

1. Resolve preset; if invalid, list available presets and abort.
2. Resolve domain: use the provided string, or default to `general`.
3. Resolve location: use `--at <path>` if provided, else default `$CWD/vault/`. Apply the resolution rules and refusal cases above.
4. Scaffold immediately with default values for everything else (no starter topic-MOCs beyond the index, default vocabulary, default `self_space` from the preset, empty `goals.md` stub, no preferences section in CLAUDE.md).
5. Print: "Vault scaffolded with defaults at `<resolved-path>`. Edit `vault.yaml`, `notes/index.md`, and `CLAUDE.md` to customise. Or re-run `/init` (no args) for guided setup against a fresh directory."

Quick mode is silent — no prompts, no questions. Suitable for scripting, testing, or users who'd rather edit YAML than answer questions.

---

## Shared scaffold (both modes converge here)

1. **Locate plugin root.** Grandparent of this `init/SKILL.md` (`<plugin>/skills/init/SKILL.md` → plugin = grandparent).
2. **Resolve target** per the rules above. Print the resolved absolute path so the user sees what's about to happen.
3. **Create directory skeleton:**
   ```
   <vault-root>/
   ├── notes/
   │   ├── claims/                 (research) or memories/ (personal)
   │   ├── papers/                 (research only)
   │   ├── methods/                (research only)
   │   └── index.md
   ├── inbox/
   ├── archive/
   ├── sessions/
   ├── self/                       (only if preset/answer says yes)
   ├── CLAUDE.md                   (thin — session-start instructions only)
   ├── vault.md                    (the vault contract: atom shape, verbs, conventions)
   ├── vault.yaml                  (runtime config)
   └── goals.md                    (research) or self/goals.md (personal)
   ```
4. **Write `vault.yaml`** with the resolved values (preset, domain, vocabulary, qmd config, git config, surrender config, created date). The `surrender:` block is copied from the preset's `preset.yaml` and always lands with `enabled: false` — surrender activation is a deliberate user choice, never auto-on at init.
5. **Generate `CLAUDE.md`** (thin) and **`vault.md`** (full contract) from the preset's templates. Both substitute the same placeholders:
   - `{VAULT_NAME}` → vault root basename
   - `{DOMAIN}` → resolved domain slug
   - `{PLUGIN_ROOT}` → absolute plugin path
   - `{DATE}` → today
   - `{VOCAB:key}` → from the resolved vocabulary
   - `{PREFERENCES_BLOCK}` (in vault.md only) → in guided mode replaced with a `## Preferences` section from Q7; in quick mode replaced with empty string

   **Parent-CLAUDE.md detection.** Before writing `CLAUDE.md`, check whether a `CLAUDE.md` exists at the vault root's parent directory. If yes, surface this fact to the user with options:
   - **standalone** (default): write `<vault>/CLAUDE.md` as usual; both load via Claude Code's hierarchical CLAUDE.md reading
   - **additive**: append a clearly-bounded `## second-brain vault: <vault-name>` section to the parent's CLAUDE.md, skip writing `<vault>/CLAUDE.md`
   - In quick mode, default to standalone with no prompt.
6. **Copy starter files.** From `<plugin>/presets/<preset>/starter/` into the vault root, applying the same substitutions.
7. **Create starter MOCs** (guided mode only). For each topic from Q3: write `notes/_<kebab-case-slug>.md` from `reference/templates/topic-map.md`, with `description` and `scope` sketched from the topic name (a single sensible sentence; user edits later).
8. **Populate `goals.md`** (guided mode only). YAML head's `active_threads:` filled from Q6; body left as scaffold prose.
9. **Initialise git** (if `git` is available): `git init`, `git add -A`, `git commit -m "init: vault scaffolded from <preset> preset"`.
10. **Print next steps:**
   ```
   ✓ vault initialised: <vault-root>

   start with:
     - drop a source in inbox/ and run /learn <path>
     - or write a first claim directly in notes/claims/
   read CLAUDE.md to understand the verbs and the contract.
   ```

---

## When to spawn a subagent

Never. `/init` is mechanical scaffolding wrapped (in guided mode) by a conversation — both run in the lead context.

## Failure modes to resist

- **Overwriting a non-empty target.** Refuse and abort. Surface the path to the user; don't silently merge.
- **Creating the vault inside the plugin.** Detect when target = plugin root or descendant; refuse.
- **Wrong preset name.** List available presets in the error.
- **Half-init on git failure.** If `git init` fails, the vault is still usable; print a warning, don't roll back.
- **Over-asking in guided mode.** Seven questions, then review. Don't drift into "tell me about your research goals for the next year". The vault adapts as the user works; setup just provides scaffold.
- **Generating fake topic content.** Starter MOCs from Q3 should have empty `## Core claims` sections. The user fills them; the assistant doesn't fabricate placeholder claims.
- **Defaulting `self_space` blindly in mixed cases.** If Q2 returns "research with a journal layer", the right move is to ask Q4 explicitly rather than infer.
- **Silently picking a path the user didn't expect.** Always echo the resolved absolute path before writing.

## Output

- New directory tree on disk at the resolved path
- Initial git commit (if git available)
- Summary printed
- (Guided mode) the conversation log itself remains visible in the session — useful as a record of intent

## Cross-references

- Templates: `<plugin>/presets/<preset>/CLAUDE.md.template`, `<plugin>/reference/templates/topic-map.md`
- Editorial: this skill is the only verb that *creates* a vault; every other verb assumes one exists
- Charter principles: P1 (the conversation IS the customisation engine), P5 (one-shot recipe — fine), P7 (visible state — every path is echoed before writing), P8 (domain-aware via the user's answer, not domain-prescriptive in the code)
