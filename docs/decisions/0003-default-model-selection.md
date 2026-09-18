# 0003. Default model selection semantics

## Status
Proposed

## Context
`ChatCompletionRequest.model` is required and any value is accepted, so a caller cannot say "you
pick" — and that is indistinguishable from a typo. Routing is meant to be the default behaviour of
the API, so the contract has to express the default before any routing code can act on it.

Two spellings are needed: the official OpenAI SDK requires the `model` argument, so a client using
the real library cannot omit it and needs a legal value to send.

Not covered here: how a model is actually chosen, and the shape of the error body that carries the
codes. Both are picked up elsewhere and neither blocks building against this.

## Decision

### `model` is optional, `auto` is reserved
`str | None`, default `None`. Omitting it and sending `auto` are the same request. The sentinel is
matched exactly on the wire, since model identifiers are case-sensitive everywhere else.

Nothing is normalized in either direction: the validated request is what gets forwarded to the
backend, so coercing `None` into `auto` would put a meaningless model name on the wire. The
equivalence lives in one predicate, `is_auto_selection`.

### Resolution order
Validate the body, resolve the sentinel to a concrete name, and only then look that name up in the
catalog. The order decides which of the two rejections below the caller gets.

### The catalog may not contain `auto`
Enforced on `ModelEntry.name`, case-insensitively — looser than the wire match on purpose: `AUTO`
in a YAML file cannot collide, but whoever wrote it expected the default behaviour.

### Substitution
Whoever chose the model owns the right to substitute it. A cluster-chosen model may fall back
freely; a caller-named one is served or refused, never swapped — answering a different model than
the one asked for is a wrong answer nobody notices.

### Two rejection codes
| Code | HTTP | What it asks the caller to do |
| --- | --- | --- |
| `model_not_found` | 404 | The request is wrong: use a catalogued name, or omit `model`. |
| `model_unavailable` | 503 | The request is fine, the cluster is not: change nothing and retry. |

404 rather than 400: the body is well-formed, a named resource does not exist. A cluster-chosen
selection that finds no candidate returns `model_unavailable` — the caller named nothing, so
nothing they wrote can be wrong.

The codes live in `common.errors`; the body that carries them is defined separately, which is what
lets this decision land first.

### The response names what served
`ChatCompletionResponse.model` is the model that produced the completion, never the sentinel,
enforced by a validator. `node_id` joins it, optional: the error body already says where a failure
happened, and without the same field on a success only failures report location.

## Alternatives considered
- Keep `model` required and mandate `auto` — rejected: clients omitting the field are common.
- Normalize `None` to `auto` during validation — rejected: it would reach the backend.
- A `default_model` key in the registry — rejected: makes "you pick" indistinguishable from a typo.
- The reserved-name check on `ModelRegistry` — rejected: 0001's rule is that collection-level checks
  are the ones needing siblings. On the entry it also fires for entries built in code.
- One code with the difference in the message — rejected: a machine cannot branch on prose.
- A `StrEnum` for the codes — rejected for consistency with `Role` and `NodeType`.

## Open questions for the team
- What mints a `node_id`? The registry's `backends` map is keyed by node *type*, which stops
  identifying anything once two machines share one. Answered by #54.
- Should `model_unavailable` carry a `Retry-After`? Answered by #64.

## Consequences
- `{"messages": [...]}` is now a legal request.
- `auto` is permanently unusable as a model name; renaming an entry to it fails at load time.
- A response's `model` is the model that served, which stops matching the requested one as soon as
  the cluster chooses.
- Adding a third code is additive; changing either value is breaking for clients branching on them.
- Until routing is wired, the orchestrator answers 503 to a cluster-chosen request.
