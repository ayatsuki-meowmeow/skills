# Skills

A collection of Claude Code skills for development.

> Japanese version: [README.ja.md](./README.ja.md)

## Available Skills

| Skill | Description |
|-------|-------------|
| [`ts-type-safety`](./ts-type-safety/SKILL.md) | Enforces TypeScript coding conventions — bans `as` casts, `any`, and `@ts-ignore`, and provides safe alternatives |
| [`neverthrow-setup`](./neverthrow-setup/SKILL.md) | Sets up `neverthrow` in a TypeScript project: package install, `AppError` union type, `AppResult` alias, `fromXxx` helpers, and ESLint config |

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
