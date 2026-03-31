# `_resolve_needed` Refactor Report

## Overview

`_resolve_needed` is the core of the course-recommendation engine. Given a
`BooleanList` prerequisite tree, a set of completed courses, and a visited set,
it returns the specific courses the student should consider taking *right now* to
make forward progress toward their target.

The original implementation handled both the OR and AND cases inside a single
~100-line function, mixing early-exit logic, progress detection, eligibility
collection, and deep recursion all in one place. This has been broken into six
focused helper functions plus a thin dispatcher.

---

## Helper Functions

### 1. `_or_is_already_satisfied(prereqs, completed) → bool`

**What it does.**
Scans every direct child of an OR node and returns `True` the moment it finds
one that is already fully satisfied. If none are satisfied it returns `False`.

**Why it exists.**
An OR requirement is complete as soon as *any* alternative is done — there is
nothing left to suggest. Checking this first lets every other helper assume the
OR is still unsatisfied, keeping their logic simple.

**Item types handled.**

| Child type | Satisfied when… |
|---|---|
| `str` (course code) | code is in `completed` |
| `BooleanList` | `BooleanList.is_satisfied(completed)` is `True` |
| `CreditCondition` | `credits_satisfied(completed)` is `True` |

---

### 2. `_partition_or_children(prereqs, completed, graph) → (list, list)`

**What it does.**
Splits the children of an OR node into two lists:

- `with_progress` — `BooleanList` children where `_has_progress` returns `True`
  (the student has already completed at least one sub-item inside that branch).
- `without_progress` — everything else that is still actionable (string course
  codes that exist in the graph and are not yet completed).

**Why it exists.**
When a student has already started one branch of an OR (e.g. they've taken
MAT137 toward an `OR[MAT137, STA237]` group) we should keep steering them down
that branch rather than scattering suggestions across all alternatives. Isolating
the partitioning logic here keeps it testable and easy to reason about
independently of the collection step.

**Important edge case.**
Single course-code strings never count as "a branch with progress" — they are
always placed in `without_progress`. Progress is a concept that only applies to
multi-course `BooleanList` branches.

---

### 3. `_collect_eligible_from_or_children(graph, children, completed, visited) → (set[str], list)`

**What it does.**
Given a list of OR children to explore (already chosen by the caller), splits
them into:

- `eligible_courses` — course codes the student can enrol in right now, plus any
  courses produced by recursing into `BooleanList` sub-nodes.
- `non_eligible_children` — children that produced nothing actionable yet.

**Why it exists.**
This is the "easy path first" rule: if *any* branch has an immediately takeable
course, we surface only those and skip the harder alternatives entirely. Separating
collection from the decision of what to do with the results makes both clearer.

**Recursion.**
For `BooleanList` children it calls `_resolve_needed` recursively. If the result
is non-empty it is merged into `eligible_courses`; if empty the child is placed
in `non_eligible_children` for possible deeper recursion later.

---

### 4. `_recurse_into_non_eligible_or(graph, non_eligible_children, completed, visited) → set[str]`

**What it does.**
Called only when `_collect_eligible_from_or_children` found *nothing* eligible.
For each string child that has not yet been visited, it marks the course as
visited (cycle guard), looks up its own prerequisite tree, and calls
`_resolve_needed` on that tree to find what is blocking it.

**Why it exists.**
This handles the case where the student needs to take prerequisites-of-prerequisites
before any course in the current OR node becomes available. Isolating this
"dig deeper" step avoids mixing it with the "collect easy wins" logic above.

**Why BooleanList items are skipped here.**
BooleanList children were already fully recursed inside
`_collect_eligible_from_or_children`. If they returned empty there, calling them
again would produce nothing new, so they are intentionally ignored.

---

### 5. `_resolve_or(graph, prereqs, completed, visited) → set[str]`

**What it does.**
Orchestrates the complete OR-node resolution by calling the four helpers above
in order:

1. `_or_is_already_satisfied` → early return if done.
2. `_partition_or_children` → decide which branches to explore.
3. `_collect_eligible_from_or_children` on the chosen branches.
4. Return eligible courses if any; otherwise `_recurse_into_non_eligible_or`.

**Why it exists.**
Before the refactor, all five steps lived interleaved inside `_resolve_needed`.
Having a dedicated OR orchestrator makes the decision flow readable as a
straight-line sequence of named steps.

---

### 6. `_resolve_and(graph, prereqs, completed, visited) → set[str]`

**What it does.**
Handles AND nodes. Because *all* children must eventually be satisfied, it
collects actionable courses from every unsatisfied child simultaneously.

For each child:
- **`str`**: skip if completed / visited / not in graph. Add directly if eligible;
  otherwise add to `visited` and recurse into that course's own prereq tree.
- **`BooleanList`**: skip if already satisfied; otherwise recurse via `_resolve_needed`.
- **`CreditCondition`**: always skipped — no specific course to suggest.

**Why it exists.**
AND logic is simpler than OR (no branching preferences, no progress detection)
and is best kept separate so readers can understand it without wading through
the OR strategy at the same time.

---

### 7. `_resolve_needed(graph, prereqs, completed, visited) → set[str]` (refactored)

The public entry-point is now a ~10-line dispatcher:

```
if prereqs.items is None: return set()
if prereqs.operator == 'OR': return _resolve_or(...)
else:                         return _resolve_and(...)
```

The visited set and all recursive calls are still threaded through exactly as
before — the behaviour is identical to the original.

---

## Call Graph

```
get_next_needed_courses
└── _resolve_needed              (dispatcher)
    ├── _resolve_or
    │   ├── _or_is_already_satisfied
    │   ├── _partition_or_children
    │   │   └── _has_progress    (existing helper, unchanged)
    │   ├── _collect_eligible_from_or_children
    │   │   └── _resolve_needed  (recursive)
    │   └── _recurse_into_non_eligible_or
    │       └── _resolve_needed  (recursive)
    └── _resolve_and
        └── _resolve_needed      (recursive)
```

---

## What Did Not Change

- `_has_progress` — already a well-scoped helper; left untouched.
- All public functions (`get_next_needed_courses`, `eligible_relevant_courses`,
  `get_relevant_courses`, `get_course_codes`, `search_courses`) — signatures and
  behaviour are identical.
- The `visited` cycle-guard mechanism — still mutated in-place and threaded
  through all recursive calls exactly as before.
