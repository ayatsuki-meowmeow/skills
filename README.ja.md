# Skills

開発向け Claude Code スキル集です。

> English version: [README.md](./README.md)

## スキル一覧

| スキル | 説明 |
|--------|------|
| [`ts-type-safety`](./ts-type-safety/SKILL.md) | TypeScript のコーディング規約を強制する — `as` キャスト・`any`・`@ts-ignore` を禁止し、安全な代替手段を提供する |
| [`neverthrow-setup`](./neverthrow-setup/SKILL.md) | TypeScript プロジェクトへの `neverthrow` 導入を一括サポート: パッケージインストール・`AppError` 判別共用体・`AppResult` 型エイリアス・`fromXxx` ヘルパー・ESLint 設定 |

## スキルをプロジェクトにコピーする方法

スキルは `<プロジェクトルート>/.claude/skills/<スキル名>/SKILL.md` に配置します。必要なスキルをプロジェクトの `.claude/skills/` ディレクトリにコピーしてください。

### 1. このリポジトリをクローンする

```bash
git clone git@github.com:ayatsuki-meowmeow/skills.git ~/skills
```

### 2. スキルを1つコピーする

```bash
# プロジェクトルートで実行
mkdir -p .claude/skills
cp -r ~/skills/<スキル名> .claude/skills/
```

例 — `ts-type-safety` をコピーする場合:

```bash
mkdir -p .claude/skills
cp -r ~/skills/ts-type-safety .claude/skills/
```

### すべてのスキルをコピーする

```bash
mkdir -p .claude/skills
cp -r ~/skills/*/ .claude/skills/
```

コピー後は追加設定不要で、Claude Code がスキルを自動的に認識します。
