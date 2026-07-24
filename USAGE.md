# USAGE — Development Workflow with the Four Interlocking Skills

> Japanese version: [USAGE.ja.md](./USAGE.ja.md)

Among the skills in this repository, the following four reference each other and together form a single development workflow:

- [`subagent-orchestration`](./subagent-orchestration/SKILL.md) — turns the main agent into an orchestrator
- [`design-impl-docs`](./design-impl-docs/SKILL.md) — context management via `design.md` / `impl.md`
- [`implement-review-loop`](./implement-review-loop/SKILL.md) — implement → review → record → fix iteration loop
- [`code-review-agent`](./code-review-agent/SKILL.md) — 5-lens parallel review + confidence scoring

The other skills (`ts-type-safety`, `neverthrow-*`, `commit-workflow`, etc.) are independent of this workflow and can be used standalone or in combination as needed.

## The big picture

Roles and information flow are captured concisely by the diagram below.

```mermaid
flowchart TD
    User["👤 User<br/>・decision-maker on spec/requirements<br/>・reviews design.md and hands back decisions"]
    Main["🎯 Main Claude (orchestrator)<br/>・dialogue, task decomposition, delegation, acceptance, summary reporting<br/>・does not write code directly"]
    Investigate["🔍 Investigation agent"]
    Implement["🛠 Implementation agent"]
    Doc["📝 Documentation agent"]
    Review["✅ Review agent"]
    Docs[("📄 design.md / impl.md<br/>everyone reads/writes here")]

    User -- "instructions" --> Main
    Main -- "escalation" --> User

    Main -- "delegate" --> Investigate
    Main -- "delegate" --> Implement
    Main -- "delegate" --> Doc
    Main -- "delegate" --> Review

    Investigate <--> Docs
    Implement <--> Docs
    Doc <--> Docs
    Review <--> Docs
```

The four skills below stack up to formalize this structure and information flow as conventions.

## How the four skills relate

```
[User] ⇄ [Main agent : subagent-orchestration]
              │
              │ referenced as the context source throughout
              ├──▶ design-impl-docs
              │      ├─ design.md  (spec/requirements, edited by User + Claude)
              │      └─ impl.md    (implementation details, edited by Claude only)
              │
              │ delegates the implementation phase
              ▼
        implement-review-loop
              │   implement → lint → review → classify → record → fix (looped)
              │
              │ invoked at step 3 (review)
              ▼
        code-review-agent
              5 lenses in parallel → Haiku confidence scoring → threshold filter
```

- **`subagent-orchestration`** is the top-level convention. The main agent focuses on dialogue and decision-making, delegating all work to subagents.
- **`design-impl-docs`** is the shared foundation across every phase. Specs live in `design.md`, implementation details in `impl.md`.
- **`implement-review-loop`** is a sub-workflow dedicated to the implementation phase. It runs under `subagent-orchestration`.
- **`code-review-agent`** is a review-only sub-workflow invoked at step 3 (review) of `implement-review-loop`.

## A typical session flow

1. **Task received** — the user requests a feature, fix, or investigation.
2. **Doc setup** (`design-impl-docs`) — the main agent checks/creates the task's `design.md` (spec/requirements). `impl.md` is **not** created upfront — it's generated on the first record write inside the loop, when there's actually something to record.
3. **Fill in spec gaps** (`subagent-orchestration` + `design-impl-docs`) — never let subagents guess on ambiguous specs. **Write the question, options, trade-offs, and recommendation into `design.md`'s open-questions section**; in chat, say only *"I've added open questions to `design.md` — please write your decision there."* Do **not** list options in chat, do not run Q&A back-and-forth in chat, do not accept verbal decisions without persisting them to `design.md`. This applies regardless of who surfaced the question (a subagent, or the orchestrator noticing a gap on its own). Once the user writes a decision into `design.md`, move it to the decisions section per `design-impl-docs` rules.
4. **Enter the implementation phase** (`implement-review-loop`) — with `design.md` in place, start the iteration loop (counter N = 1). `impl.md` may not exist yet; the loop creates it on first record.
5. **One iteration**:
   - Delegate to an implementation agent (if `impl.md` doesn't exist yet, the agent creates it on completion and records the structure/status)
   - Run lint (prefer Claude Code hook; if absent, run from the orchestrator)
   - **Delegate to the review agent** (`code-review-agent`) — 5 lenses in parallel → Haiku confidence scoring → drop items below the threshold
   - Classify findings as either "spec/design" or "implementation judgment"
   - Escalate spec/design findings via `design.md` (same protocol as step 3 — write to open-questions, chat is pointer-only); record the rest in `impl.md` per iteration
   - Delegate fixes to the implementation agent and increment N
6. **Stopping condition** — when "0 review findings + lint passes + no open questions" is reached, delegate to the **commit agent** as the loop's final step (see the "git operations" section of `subagent-orchestration`; the delegation prompt should point at a project-specific commit skill such as `commit-workflow` when available). The orchestrator never runs `git add` / `git commit` itself. **User verification after commit is opt-in, not default** — request it only when the change touches UI/UX, external systems or irreversible side effects, `design.md` explicitly flags verification, or user decisions in the loop need visual confirmation. For pure internal changes (refactors, type fixes, review-finding cleanups), just report completion and finish. If N == 3 without meeting the condition, record status, options, and recommendation in the `design.md` open-questions section and escalate to the user.

> **Note on hook-based enforcement (optional)**
> `implement-review-loop` runs the final commit via a commit agent, but two orthogonal hook setups can back it up if you want a mechanical safety net:
> - **Commit-time skill invocation** — if a project has its own commit conventions (e.g. `commit-workflow`), a Claude Code PreToolUse hook or a `pre-commit` git hook can invoke that skill so the convention is applied regardless of which caller triggered the commit.
> - **Preventing orchestrator direct-commit** — putting `Bash(git commit:*)` into `permissions.ask` catches cases where the orchestrator would otherwise call git directly (commit-agent-driven commits still go through as expected).
>
> These are project-level infrastructure choices, not part of this skill. The loop assumes only that a commit — routed through the commit agent — happens at the end of a successful iteration.

## Where to start reading

Pick an entry point based on your goal.

| Goal | Entry point |
|------|-------------|
| Adopt the whole workflow across all four skills | Read `subagent-orchestration` → `design-impl-docs` → `implement-review-loop` → `code-review-agent` in that order |
| Only need session resumption / context sharing | `design-impl-docs` alone |
| Want the implementation phase as an iteration loop (`design.md` already in place) | Skim `design-impl-docs`, then `implement-review-loop` |
| Only want to switch reviews to the 5-lens style | `code-review-agent` (requires `design.md`; `impl.md` may be absent at first) |

## Dependency summary

| Skill | Prerequisites | Invokes |
|-------|---------------|---------|
| `subagent-orchestration` | Environment with subagent (Task/Agent) tools available | `design-impl-docs` (context source) / `implement-review-loop` (implementation phase) |
| `design-impl-docs` | — | — |
| `implement-review-loop` | `design.md` is prepared (`impl.md` is generated inside the loop) | `code-review-agent` (step 3 review) |
| `code-review-agent` | `design.md` is prepared; `impl.md` if it exists is passed as extra context; subagents available | — |
