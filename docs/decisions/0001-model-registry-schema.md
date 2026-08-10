# 0001. Model registry schema (configs/models.yaml)

## Status
Proposed

## Context
The orchestrator and backend nodes need a single source of truth for which
models exist, what quantization/format they use, which node types can serve
them, and where to download them from. Without this, model metadata would
end up hardcoded across the orchestrator and each backend, duplicating and
drifting over time.

This covers the on-disk YAML schema and the Python types used to load and
validate it — not routing logic (how a node is chosen for a given request),
which is deferred to a later phase.

## Decision

### File layout
`configs/models.yaml` holds a single top-level `models:` list. Each item is
one model entry.

### Fields

Required:
- `name` (str) — unique identifier, also used as the model id in API requests.
- `quantization` (str | null) — e.g. `"Q4_K_M"`; null for full precision.
- `size_b` (float) — parameter count in billions. Numeric rather than a
  string like `"1.5B"` so future code (e.g. a capability-aware router) can
  compare sizes without parsing strings.
- `format` (enum: gguf | safetensors | awq | gptq) — the artifact format.
  Needed because `node_types` alone is ambiguous: different team members run
  different inference engines on the same node type (e.g. vLLM vs. llama.cpp
  on a GPU node), and each engine expects a different format.
- `node_types` (list of: gpu | edge | router) — which backend types can serve
  this model. A list, since a small model may run on more than one.
- `source_url` (URL) — download source. Should point at the exact artifact
  file, not just a repository root.

Optional:
- `family` (str) — human-readable grouping (e.g. `"qwen3"`). No effect on
  validation or behavior.
- `approx_vram_gb` (float | null) — a rough, non-authoritative estimate.
  Real usage depends on context length and engine overhead, so this is a
  hint, not a guarantee.

### Python types
Two classes, not one:
- `ModelEntry` — validates a single entry (types, enum membership, URL
  shape). Lives in `packages/common`.
- `ModelRegistry` — wraps `models: list[ModelEntry]` and adds
  collection-level validation, specifically rejecting duplicate `name`
  values across the file. This check cannot live on `ModelEntry`, since a
  single entry has no visibility into its siblings.

`load_registry(path)` reads the YAML, surfaces clear errors for a missing
file or malformed YAML, and returns a validated `ModelRegistry`.

## Alternatives considered
- `size_b` as a string (e.g. `"1.5B"`) — more familiar to read, but requires
  parsing before any numeric comparison. Rejected in favor of a plain float.
- Omitting `format` and relying on `node_types` alone — rejected once it
  became clear the same node type can run different engines expecting
  different artifact formats.
- Duplicate-checking done ad hoc wherever the registry gets loaded, instead
  of as a class invariant — rejected in favor of putting that check on
  `ModelRegistry`, so it can't be forgotten by a future caller.

## Open questions for the team
- Is `router` a legitimate `node_types` value now, or should it wait until
  the routing phase actually needs it?
- The seed file's `source_url` values currently point at repository roots,
  not specific artifact files — need the literal filenames confirmed.
- Only `gguf` has been validated against a real download so far; other
  formats are unverified.

## Consequences
- Adding a new model going forward means editing YAML only — no code changes
  in the orchestrator or backends.
- Any future change to a required field is a breaking change for everyone
  already relying on the schema — new fields should default to optional
  where possible.