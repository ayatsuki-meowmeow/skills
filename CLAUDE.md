# CLAUDE.md

このリポジトリは Claude Code スキルのコレクションです。新しいスキルを追加する／既存のスキルを変更するときは、本ファイルの規約に従ってください。詳細な背景は [README.md](./README.md) を参照。

## スキル保存スタイル

新しいスキルは必ず **リポジトリ直下** に `<skill-name>/` ディレクトリを作成し、その中に全ての関連ファイルを収めます。スキル名は kebab-case（例: `neverthrow-setup`）。

スキルは以下の 3 タイプのいずれかに分類し、対応するディレクトリ構造で配置してください。

### 共通: SKILL.md と references/rules.md の分離

すべてのスキルは `SKILL.md` を薄い entry point（frontmatter 込みで 20〜35 行）に保ち、ルール本体は `references/rules.md` に分離します。トリガー判定時には description しか評価されず本文は invoke 後にロードされるため、本文を SKILL.md に詰めると毎回コンテキストに乗ってコスト・読み飛ばしリスクが増えます。

`SKILL.md` の構成は固定:

1. frontmatter（`name` / `description` に TRIGGER/SKIP を含む）
2. `# {Skill Name}`
3. `## 目的` — 1〜2 行
4. `## 参照` — `references/rules.md` を読む旨だけ
5. `## 実行手順` — 「rules.md を読んで適用する」を中心に 3〜5 ステップ

### Type 1 — Rules only（規約のみ）

プロンプトで規約を定義するだけで、自動的に観測可能な副作用を持たないスキル。

```
<skill-name>/
├── SKILL.md
└── references/
    └── rules.md
```

### Type 2 — Setup（セットアップ系）

パッケージインストール・ファイル生成・コマンド実行など、具体的に観測可能なアクションを行うスキル。実行結果そのものが検証材料になるため、`workspace/` は不要です。

```
<skill-name>/
├── SKILL.md
├── references/
│   └── rules.md
├── evals/
│   └── evals.json
└── <skill-name>.skill        # 配布用バイナリ
```

### Type 3 — Coding rules with behavioral proof（コーディング規約 + 挙動証跡）

モデルのコード生成挙動を変えるタイプのスキル。スキル適用前後の差を記録するため `workspace/` を含めます。

```
<skill-name>/
├── SKILL.md
├── references/
│   └── rules.md
├── evals/
│   └── evals.json
├── <skill-name>.skill        # 配布用バイナリ
└── workspace/
    ├── trigger-eval.json
    ├── iteration-1/
    ├── iteration-2/
    └── iteration-3/
```

カスタム grading スクリプトが必要な場合（`git log` 出力など、デフォルトの eval runner では検証できない副作用を見るケース）は `workspace/grade.py` として配置します。

## 必ず守ること

- `workspace/` は **必ずスキルディレクトリ配下** に置く。リポジトリ直下に `<skill-name>-workspace/` のような兄弟ディレクトリを作らない。
- 配布用バイナリ（`.skill` ファイル）の名前はスキルディレクトリ名と一致させる（例: `neverthrow-setup/neverthrow-setup.skill`）。
- 新しいスキルを追加したら [README.md](./README.md) と [README.ja.md](./README.ja.md) の "Available Skills" 表に 1 行追記する。
- スキル entry point のファイル名は `SKILL.md`（大文字固定）。ルール本体は `references/rules.md` に置く。
