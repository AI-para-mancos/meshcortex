# 0002. Routing complexity taxonomy and evaluation set

## Status
Proposed

## Context
The orchestrator forwards every request that names no model to one hardcoded
backend, so adding a second node changes nothing about where work lands. Routing
by capability needs a vocabulary first: a finite set of classes a prompt can be
assigned to, and a rule saying which models may serve each one.

Everything else in the routing work depends on that vocabulary. The classifier
has to emit one of these labels, the deterministic fallback has to emit the same
ones so the two are comparable, and the selection policy has to turn a label into
a node. This is filed as `Proposed` so that work can start before the team has
met: `Proposed` means written down and safe to build against.

Correcting these classes later is the expected outcome. A taxonomy is only shown
to be ambiguous by applying it, which is why the seed evaluation set ships with
the definition rather than after it.

This covers the classes, how a model is matched to one, and the structure of the
evaluation set. It does not cover how a label is produced, nor how a label plus
live node state resolves to one chosen node.

## Decision

### The classification axis
Prompts are classified by the capability an answer needs, not by task type or
domain. A translation request and a debugging request belong to the same class
whenever they need the same model.

This is the one part fixed in advance, because it decides whether the work
survives a change of product: every candidate application has both easy and hard
requests, so a complexity axis holds whichever application gets picked.

### The classes
Three, ordered from least to most capable, defined in
`configs/routing/taxonomy.yaml`:

- `trivial` — mechanical, single-step work on text the prompt already contains,
  or a fact the model either knows or does not. No reasoning chain.
- `general` — composed prose or code needing ordinary fluency and common world
  knowledge, with at most one reasoning step. Being slightly off is cheap.
- `complex` — multi-step reasoning, or a conclusion that has to be derived and
  defended rather than recalled. Also anything where a confident wrong answer
  costs more than no answer.

Three rather than more because each boundary has to correspond to a routing
decision that can actually be made. A distinction that sends work to the same
model is one labellers can disagree about while nothing downstream changes.

The list order in the file is the capability ranking, and the policy depends on
it. Reordering the classes is a behaviour change, not a cosmetic edit.

### A class describes prompts; a model declares what it reaches
A class carries no size, threshold or hardware hint. What a model can handle is
recorded on the model, in `configs/models.yaml`, as a `tier` naming the hardest
class it answers acceptably:

```yaml
  - name: qwen3-1.7b-q4
    size_b: 1.7
    tier: general
```

Routing then reads: a model may serve class `C` when its `tier` is `C` or
higher. Ranking for "most capable available" is by `tier`, with `size_b`
descending as the tie-break, so the comparison is always total.

A model with no `tier` is treated as `trivial`. That keeps an unmeasured model
rankable and reachable while never letting it silently receive work above what it
has been shown to handle.

The alternative was to put a `min_size_b` floor on each class and compare it
against `size_b`. Rejected because it extrapolates: measuring one 1.7B model and
writing `min_size_b: 1.7` asserts something about every model of that size, when
quantization and instruction tuning are exactly what move that line. A `tier` is
the same measurement recorded without the extrapolation — the experiment behind
both is identical.

This also keeps the constraint that a node declares only the models it serves,
never the classes it accepts: the tier sits on the model, not on the node.

The registry already carries a hand-measured field in `approx_vram_gb`, so a
measured `tier` needs no new home.

### Measuring a tier
Per model, walk up the ladder rather than crossing every model with every prompt.
Serve the model, run it against the prompts of the lowest class, and keep going up
until it fails. Its tier is the highest class it passed.

A model passes a class when at least **80%** of that class's prompts get an
acceptable answer. The prompts are the `typical` and `adversarial` entries for
that class; the `few_shot` pool is excluded. A percentage rather than a count of
failures, because the set is expected to grow.

"Acceptable" is a human read today — there is no automated judge in the repo — so
the tiers only compare to each other if one person applies one standard across a
whole pass. Record the rate seen per class, not just the resulting tier.

A tier belongs to one registry entry, and an entry names one quantization of one
artifact, so different weights are a different entry that starts untiered.

No tier has been measured yet. The registry declares none, and every model is
therefore `trivial` by default until someone runs this.

### The evaluation set
`configs/routing/seed_prompts.yaml` holds three lists as separate top-level keys
— `few_shot`, `typical`, `adversarial` — so disjointness is structural: a prompt
cannot be in two splits without being physically duplicated.

`few_shot` is the only pool few-shot examples may be drawn from. An example a
classifier has already been shown is one it can copy, so scoring it on that same
prompt would measure recall rather than classification.

`adversarial` holds prompts whose surface features point at the wrong class:
short but hard, long but trivial, politeness padding, paraphrases, and
mixed-language prompts. It exists because comparable accuracy on typical prompts
is the expected result and therefore carries almost no information.

Each entry carries `id`, `prompt`, `label` and `lang` (`es`, `en` or `mixed`);
adversarial entries also carry a `note` recording which signal misleads.
Authorship is deliberately not a field: git already records who wrote each
prompt, so a labelling round that has to hand each person a slice nobody wrote
themselves can read it from the history rather than from a column that would
have to be kept honest by hand.

Prompts are written in Spanish, English and a mix across every split, because
that is how the team writes and a keyword heuristic built in one language is
exactly what mixed prompts defeat.

The seed is 30 prompts — 6 few-shot, 15 typical, 9 adversarial — balanced across
the three classes, sized to expose ambiguous boundaries rather than to be the
final set.

## Consequences
- Routing work blocked on a vocabulary can start: the classifier, the fallback
  and the policy all have a fixed label set before the team has ratified it.
- Adding `tier` to the registry schema is a change to `ModelEntry` and its
  loader, and the selection policy joins on `tier` rather than on a size
  threshold.
- A model is not usable above `trivial` until someone measures it. That is
  deliberate — the failure mode of an undersized model is a confident wrong
  answer, which nobody notices.
- Renaming or removing a class is a breaking change once the classifier prompt,
  the fallback rules and every model's `tier` encode the vocabulary. Retiering a
  model is cheap by comparison and is the intended way to adjust routing.
- Every label in the seed set is one person's judgement, so accuracy measured
  against it today measures agreement with that person. Removing that limitation
  is what the blind labelling round is for, and why this stays `Proposed`.
