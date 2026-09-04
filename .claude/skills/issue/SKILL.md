---
name: issue
description: This skill should be used when the user asks to "open an issue", "create an issue",
  "file a bug", "report a bug", or whenever Claude is about to run `gh issue create` in this
  repository. Enforces this project's issue templates, granularity, title and metadata
  conventions, and confirmation workflow.
version: 0.2.0
---

# Issues for meshcortex

Open GitHub issues in this repository with a consistent body and metadata, using the existing
templates under `.github/ISSUE_TEMPLATE/` so the structure holds regardless of which teammate's
Claude Code session created it.

The sections below follow the order the work actually happens: decide how many issues there are,
pick the template, write the title, write the body, set the metadata, confirm.

## Splitting work into issues

Format isn't the hard part of writing an issue; granularity is. Before creating a set of issues
for a phase or an epic:

- **Tests are not their own issue.** An issue that produces code carries its own tests. Splitting
  them off makes one person wait on another for no technical reason, and the test issue is
  blocked from the moment it is created.
- **An issue that produces a definition** — a schema, a taxonomy, a contract — is verified by
  applying it to real data, not by tests. Keep the definition and its first application in the
  same issue: separated, the second one discovers the first is wrong and reopens it.
- **One unit of code is one issue.** Selection, failure handling and the edge cases of the same
  function belong together; three issues over one file means three PRs conflicting with each
  other.
- **When every member repeats the same work, open sibling issues, one per person**, following the
  existing `Validate gpu-node on <name>'s GPU` pattern. Everyone owns something, and milestone
  progress reflects real work.
- **Check what the phase depends on that isn't decided yet**, and prefer the approach that stays
  valid whichever way the open question resolves. Name that constraint in the issue instead of
  letting it surface halfway through.
- **A design decision ships as `Proposed`** (see Decision records in `CLAUDE.md`) so dependent
  issues can start immediately. Ratifying it is its own issue, never a blocker on the first.

## Choosing the template

1. Pick the closest matching template (`bug_report.md`, `feature_request.md`, `epic.md`, or
   `roadmap_task.md`) rather than writing free-form. `gh issue create` doesn't apply a template's
   frontmatter automatically — pass the matching `--title`, `--label`, and `--type` explicitly.
2. Search for an existing issue covering the same problem before opening a new one
   (`gh issue list --search "..."`) to avoid duplicates.

## Title

Task titles start with an imperative verb — `Scaffold packages/orchestrator`, `Wire orchestrator
to configs/models.yaml`. Epic titles are noun phrases — `Repo & tooling foundation` — because an
epic is a thing, not an action. That difference is what makes the two levels scannable in the
issue list.

No phase name, no plan ID (`P0-01`), and no epic name in the title. The Milestone, the Issue Type
and the parent relationship already encode all three; repeating one only means it has to be
maintained in two places, and it goes stale the moment a phase or epic is renamed.

If a task title needs "and", it is two issues — the same test the commit skill applies to a
subject line. A conjunction in an epic title is fine, since grouping is exactly what an epic does.

## Body

Follow the matching template's sections, and use them as they are: if one doesn't apply, drop it,
but don't invent new ones. If something is genuinely missing from every issue of a kind, change
the template rather than the individual issue. A `Depends on` heading in particular duplicates the
native relationship and goes stale silently.

Write as natural sentences/paragraphs — no manual line-wrapping, even in a temp `.md` file staged
for `--body-file`: this overrides the global 100-character prose-wrap preference, since GitHub
renders a paragraph's internal line breaks as nothing (soft-wrapped) and hard-wrapping only makes
the raw source look broken up for no visual benefit.

Roadmap task and Epic issues must be self-contained: never reference a phase by name (that's
already the Milestone, not prose), the parent Epic (that's the sub-issue relationship, not
prose), or an external document (meeting notes, a planning doc section, a chat thread) — inline
the actual rationale/constraint instead of pointing at where it was once written down. The only
exception is referencing a sibling or dependency issue that genuinely relates to this one and
isn't its parent.

When referencing another issue, always use the real `#<number>` link — never a title-derived
scheme like `P0-01`, which doesn't link to anything and breaks the moment the issue is retitled.
An actual dependency is metadata, not body content: set it as a real Relationship instead
(see Metadata below).

## Metadata

Only set metadata if `gh` is available and the user has confirmed it.

- Roadmap tasks and epics carry **no labels**: Issue Type, Milestone and the parent relationship
  already classify them, and none of this repo's labels describe roadmap work. Labels belong on
  `bug_report` and `feature_request` issues, where `bug` and `enhancement` genuinely apply — read
  them with `gh label list` and never pass a name that wasn't confirmed to exist. There are no
  `phase:`/`epic:` labels here, by design.
- Set the Milestone (`--milestone`) from `gh api repos/:owner/:repo/milestones` if this issue
  belongs to a specific phase — never a name that wasn't confirmed to exist.
- Set the Issue Type (`--type`) to match the chosen template's `type:` frontmatter — `gh issue
  create` doesn't apply it automatically, same as `--title`/`--label`.
- Ask whether the issue should be assigned to an epic (provided the issue is not an epic itself),
  then set the parent issue (`--parent`) from `gh issue list --type Epic`.
- If this issue is blocked by, or blocks, another one, set that with the native Relationships
  feature — `--blocked-by`/`--blocking` on `gh issue create`, or `--add-blocked-by`/
  `--add-blocking` on `gh issue edit`.
- If this issue is merely related to another (no dependency either way), the native "Relates to"
  relationship is web UI only for now — no `gh` CLI or GraphQL support — so tell the user to add
  it by hand rather than scripting it. Use a bare `#<number>` inline in the body only when
  neither relationship type fits.
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
- `CLAUDE.md` — Decision records section, for the `Proposed`/`Accepted` status referenced above.
- `.claude/skills/pull-request/SKILL.md` — companion skill for opening PRs that close these
  issues.
