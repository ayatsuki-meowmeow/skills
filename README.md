# Skills

A collection of Claude Code skills for development.

> Japanese version: [README.ja.md](./README.ja.md)

## Available Skills

| Skill | Description |
|-------|-------------|
| [`ts-type-safety`](./ts-type-safety/SKILL.md) | Enforces TypeScript coding conventions — bans `as` casts, `any`, and `@ts-ignore`, and provides safe alternatives |
| [`function-signature-typing`](./function-signature-typing/SKILL.md) | Enforces explicit type annotations on function signatures (arguments and return values) across statically-typed languages — turns inferred types into contracts that capture design intent |
| [`neverthrow-setup`](./neverthrow-setup/SKILL.md) | Sets up `neverthrow` in a TypeScript project: package install, `AppError` union type, `AppResult` alias, `fromXxx` helpers, and ESLint config |
| [`neverthrow-coding-rules`](./neverthrow-coding-rules/SKILL.md) | Enforces `neverthrow` coding conventions — bans raw `throw`, `try/catch` for logic errors, and unwrapped `Result` values |

## Skill Directory Structure

Each skill directory bundles everything related to that skill. The contents vary by skill type:

### Type 1 — Rules only

For skills that only define coding conventions via a prompt, with no automated side effects to verify.

```
ts-type-safety/
└── SKILL.md          # skill definition
```

### Type 2 — Setup

For skills that perform concrete, observable actions (install packages, write files, run commands). The distributable binary and evals are included; a separate workspace is not needed because the result is verifiable by running the setup itself.

```
neverthrow-setup/
├── SKILL.md                  # skill definition
├── evals/                    # eval configs
│   └── evals.json
└── neverthrow-setup.skill    # distributable binary
```

### Type 3 — Coding rules with behavioral proof

For skills that change how the model writes code. A `workspace/` directory is included to record eval iterations as evidence that the skill actually shifts model behavior (before/after comparison).

```
neverthrow-coding-rules/
├── SKILL.md                          # skill definition
├── evals/                            # eval configs
│   └── evals.json
├── neverthrow-coding-rules.skill     # distributable binary
└── workspace/                        # eval iteration results
    ├── trigger-eval.json
    ├── iteration-1/
    ├── iteration-2/
    └── iteration-3/
```

## Copying Skills to a Project

Skills live in `<project>/.claude/skills/<skill-name>/SKILL.md`. Copy any skill you need into your project's `.claude/skills/` directory.

### 1. Clone this repository

```bash
git clone git@github.com:ayatsuki-meowmeow/skills.git ~/skills
```

### 2. Copy a single skill

```bash
# From inside your project root
mkdir -p .claude/skills
cp -r ~/skills/<skill-name> .claude/skills/
```

Example — copying `ts-type-safety`:

```bash
mkdir -p .claude/skills
cp -r ~/skills/ts-type-safety .claude/skills/
```

### Copy all skills

```bash
mkdir -p .claude/skills
cp -r ~/skills/*/ .claude/skills/
```

After copying, Claude Code picks up the skill automatically — no further configuration required.
