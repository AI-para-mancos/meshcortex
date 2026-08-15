---
name: issue
description: This skill should be used when the user asks to "open an issue", "create an issue",
  "file a bug", "report a bug", or whenever Claude is about to run `gh issue create` in this
  repository. Enforces this project's issue templates, labels, and confirmation workflow.
version: 0.1.0
---

# Issues for meshcortex

Open GitHub issues in this repository with a consistent body and metadata, using the existing
templates under `.github/ISSUE_TEMPLATE/` so the structure holds regardless of which teammate's
Claude Code session created it.

## Before creating

1. Pick the closest matching template (`bug_report.md`, `feature_request.md`, `epic.md`, or
   `roadmap_task.md`) rather than writing free-form. `gh issue create` doesn't apply a template's
   frontmatter automatically — pass the matching `--title`, `--label`, and `--type` explicitly.
2. Read existing labels with `gh label list` rather than guessing a name. If nothing in the
   templates fits, say so instead of forcing the closest match.
3. Search for an existing issue covering the same problem before opening a new one
   (`gh issue list --search "..."`) to avoid duplicates.

## Body

Follow the matching template's sections. Write as natural sentences/paragraphs — no manual
line-wrapping, even in a temp `.md` file staged for `--body-file`: this overrides the global
100-character prose-wrap preference, since GitHub renders a paragraph's internal line breaks as
nothing (soft-wrapped) and hard-wrapping only makes the raw source look broken up for no visual
benefit.

Roadmap task and Epic issues must be self-contained: never reference a phase by name (that's
already the Milestone, not prose), the parent Epic (that's the sub-issue relationship, not
prose), or an external document (meeting notes, a planning doc section, a chat thread) — inline
the actual rationale/constraint instead of pointing at where it was once written down. The only
exception is referencing a sibling or dependency issue that genuinely relates to this one and
isn't its parent.

When referencing another issue, always use the real `#<number>` link — never a title-derived
scheme like `P0-01`, which doesn't link to anything and breaks the moment the issue is retitled.
An actual dependency is metadata, not body content: set it as a real Relationship instead
(see Metadata below). For an issue that's merely related (no dependency either way), prefer the
native "Relates to" relationship, web UI only for now (no `gh` CLI or GraphQL support yet), so
tell the user to add it by hand rather than scripting it. Use a bare `#<number>` inline only
when neither relationship type fits.

## Metadata

Only set metadata if `gh` is available and the user has confirmed it.

- Attach whatever labels fit, chosen from what `gh label list` actually returns — never a name
  that wasn't confirmed to exist. There are no `phase:`/`epic:` labels in this repo; phase and
  epic membership are expressed through Milestone and Issue Type + parent/sub-issue (below), not
  labels.
- Set the Milestone (`--milestone`) from `gh api repos/:owner/:repo/milestones` if this issue
  belongs to a specific phase — never a name that wasn't confirmed to exist.
- Set the Issue Type (`--type`) to match the chosen template's `type:` frontmatter — `gh issue
  create` doesn't apply it automatically, same as `--title`/`--label`.
- Ask whether the issue should be assigned to an epic (provided the issue is not an epic itself),
  then set the parent issue (`--parent`) from `gh issue list --type Epic`.
- If this issue is blocked by, or blocks, another one, set that with the native Relationships
  feature — `--blocked-by`/`--blocking` on `gh issue create`, or `--add-blocked-by`/
  `--add-blocking` on `gh issue edit`.
- If this issue is merely related to another (no dependency either way), flag that the user
  should add the native "Relates to" relationship from the issue's web UI.
- Assign to whoever should own it; leave unassigned if that's unclear rather than guessing.
- Don't add the issue to the "meshcortex roadmap" Project manually — the `Auto-add to project`
  workflow already does this for every open issue that matches its filter.

## Confirmation

Never run `gh issue create` without first showing the drafted title, body, and chosen metadata,
and waiting for confirmation — the same rule as committing or opening a PR. Creating an issue is
outward-facing and cannot be quietly undone.

## Additional resources

- `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`,
  `.github/ISSUE_TEMPLATE/epic.md`, `.github/ISSUE_TEMPLATE/roadmap_task.md` — the body templates
  this skill fills in.
- `.claude/skills/pull-request/SKILL.md` — companion skill for opening PRs that close these
  issues.
