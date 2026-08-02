# Contributing to meshcortex

> Minimal guide covering local code-style tooling. It will be expanded with the
> full contribution workflow (branching, PRs, reviews) later.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) installed.
- Sync the workspace once: `uv sync --all-packages`

## Code style: ruff + pre-commit

Style and linting are enforced by [ruff](https://docs.astral.sh/ruff/), wired
into [pre-commit](https://pre-commit.com/) so violations are caught **before** a
commit is created. The same ruff version and configuration run locally and in CI.

### One-time setup

```bash
uv tool install pre-commit
pre-commit install
```

`pre-commit install` registers a git hook, so `ruff` (lint) and `ruff-format`
run automatically on the files you stage every time you `git commit`.

### How it works

- On `git commit`, the hooks lint and format the staged files.
- If ruff auto-fixes something (or a file isn't formatted), the commit is
  **blocked** and the changes are left in your working tree — review, re-stage
  (`git add`), and commit again.
- Unfixable lint errors block the commit until you resolve them.

### Useful commands

```bash
pre-commit run --all-files   # run the hooks over the whole repo
uv run ruff check .          # lint only (same as CI)
uv run ruff format .         # format in place
uv run ruff format --check . # verify formatting without changing files (CI does this)
```

### Version alignment

The ruff version is pinned in **two** places that must stay in sync:

- `.pre-commit-config.yaml` → `rev: v0.16.1`
- `pyproject.toml` → `[dependency-groups] dev` → `ruff==0.16.1`

When upgrading ruff, bump **both** together so local hooks and CI keep using an
identical version. Ruff reads its configuration from `[tool.ruff]` in
`pyproject.toml`, so lint/format rules are defined once and shared.
