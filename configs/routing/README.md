# Routing taxonomy and evaluation set

- `taxonomy.yaml` — the complexity classes the router distinguishes.
- `seed_prompts.yaml` — labelled prompts used to evaluate anything that assigns those labels.

Why the classes are what they are: `docs/decisions/0002-routing-complexity-taxonomy.md`.

Prompts are classified by the **capability** an answer needs, never by task type or domain. Two
requests from the same application routinely land in different classes.

## Classes and model tiers

A class describes prompts only. What a model can handle is recorded on the model, in
`configs/models.yaml`, as a `tier` naming the hardest class it answers acceptably:

```yaml
  - name: qwen3-1.7b-q4
    size_b: 1.7
    tier: general
```

A model may serve class `C` when its `tier` is `C` or higher. "Most capable available" ranks by
`tier`, tie-broken by `size_b` descending. A model with no `tier` counts as `trivial`, so it stays
reachable but never silently gets work above what it has been shown to handle.

The class order in `taxonomy.yaml` is that ranking. Reordering it changes routing behaviour.

### Measuring a tier

No tier has been measured yet, so every model currently counts as `trivial`.

You do not cross every model with every prompt. Per model, walk up the ladder:

1. Serve the model and run it against the lowest class's prompts — the `typical` and `adversarial`
   entries for that class, never the `few_shot` pool. `configs/README.md` covers downloading and
   running a registry entry.
2. It passes the class if **80% or more** of those answers are acceptable. A percentage, not a
   failure count, because the set keeps growing.
3. If it passed, repeat with the next class up. Stop at the first failure; its tier is the highest
   class it passed.

Record the rate per class, not just the resulting tier. "Acceptable" is a human read today, so
tiers only compare to each other if one person applies one standard across a whole pass.

## The splits

No prompt may appear in more than one:

| split | what it is for |
|---|---|
| `few_shot` | The only pool few-shot examples may be drawn from. |
| `typical` | Everyday requests. Easy for anything that classifies at all. |
| `adversarial` | Prompts whose surface features point at the wrong class. |

`few_shot` stays disjoint because an example a classifier has already been shown is one it can
copy: scoring it on that prompt later would measure recall, not classification. `typical` carries
little information on its own — the number worth reading is `adversarial`, where a cheap heuristic
and a real classifier diverge.

## Adding prompts

```yaml
  - id: adv-010
    prompt: |-
      Your prompt text here.
    label: complex
    lang: en
    note: >-
      Which signal points at the wrong class. Required for adversarial entries.
```

- `id` — keep the split prefix and never reuse a number, including a deleted prompt's. Ids are how
  a blind-labelling round refers to a prompt without quoting it.
- `lang` — `es`, `en` or `mixed`. Mixed prompts are wanted: a keyword list in one language is
  exactly what they defeat.
- `note` — an adversarial prompt whose trap is not written down is indistinguishable from a
  typical one.

Write prompts as `|-` block scalars, so quotes and colons need no escaping.

`packages/common/tests/test_routing_seed_set.py` checks the structural rules. After editing:

```bash
uv run pytest packages/common -v
```
