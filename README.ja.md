# Skills

開発向け Claude Code スキル集です。

> English version: [README.md](./README.md)

このうち `subagent-orchestration` / `design-impl-docs` / `implement-review-loop` / `code-review-agent` の 4 スキルは互いに参照し合い、1 つの開発ワークフローとして機能します。関係と典型的なセッションの流れは [USAGE.ja.md](./USAGE.ja.md) を参照してください。

## スキル一覧

| スキル | 説明 |
|--------|------|
| [`ts-type-safety`](./ts-type-safety/SKILL.md) | TypeScript のコーディング規約を強制する — `as` キャスト・`any`・`@ts-ignore` を禁止し、安全な代替手段を提供する |
| [`function-signature-typing`](./function-signature-typing/SKILL.md) | 静的型付け言語のコーディング規約を強制する — 関数シグネチャ（引数・戻り値）の型アノテーション明示を必須化し、設計意図を契約として表現する |
| [`neverthrow-setup`](./neverthrow-setup/SKILL.md) | TypeScript プロジェクトへの `neverthrow` 導入を一括サポート: パッケージインストール・`AppError` 判別共用体・`AppResult` 型エイリアス・`fromXxx` ヘルパー・ESLint 設定 |
| [`neverthrow-coding-rules`](./neverthrow-coding-rules/SKILL.md) | `neverthrow` のコーディング規約を強制する — 生の `throw`・ロジックエラーへの `try/catch`・アンラップされた `Result` 値を禁止する |
| [`commit-workflow`](./commit-workflow/SKILL.md) | Git コミット作成のワークフローを強制する — 変更を意味単位（ビジネスロジック / ユーティリティ / UI / テスト 等）で分割し、コミットメッセージを「英語サマリ → 空行 → 日本語詳細」の形式で書き、`Co-Authored-By:` フッターを禁止する |
| [`design-impl-docs`](./design-impl-docs/SKILL.md) | design.md（仕様・要件、ユーザーと Claude が編集）と impl.md（実装詳細、Claude のみ編集）の 2 ドキュメントで開発コンテキストを管理する — セッション再開とサブエージェントへのコンテキスト共有を容易にする |
| [`subagent-orchestration`](./subagent-orchestration/SKILL.md) | メインエージェントをオーケストレーターにする — 調査・実装・ドキュメント・レビューを専門サブエージェントに委譲し、仕様・要件の疑問はユーザーへエスカレーションして決定を design.md に記録する |
| [`implement-review-loop`](./implement-review-loop/SKILL.md) | 実装フェーズを「実装 → レビュー → 指摘分類 → 記録 → 対応」の反復ループとして回す — 仕様・設計に関わる指摘は design.md 経由でユーザーへエスカレーション、それ以外は impl.md の「レビュー指摘と対応」に記録し、レビュー指摘 0 件かつユーザーが動作確認できる状態になるまで止めない |
| [`code-review-agent`](./code-review-agent/SKILL.md) | コードレビューを「5 レンズ並列 → Haiku confidence scoring → 閾値フィルタ → 分類ヒント付き指摘の返却」の構造で実行する — 5 レンズは (1) 外部仕様遵守 / (2) 内部整合性 / (3) バグ・エッジケース / (4) デグレ影響 / (5) 保守性・可読性。implement-review-loop の step 3 レビューで使う |

## スキルディレクトリの構成

各スキルディレクトリには、そのスキルに関連するファイルをすべてまとめます。中身はスキルの性質によって異なります。

どのスキルも `SKILL.md` は薄い entry point（20〜35 行）に保ち、ルール本体は `references/rules.md` に分離します。トリガー判定時には `SKILL.md` だけが読み込まれ、本体は invoke 後に必要に応じてロードされます。

### タイプ 1 — ルールのみ

コーディング規約をプロンプトで定義するだけのスキル。自動実行による副作用がないため、動作確認用の workspace は不要です。

```
ts-type-safety/
├── SKILL.md                  # 薄い entry point（frontmatter + 目的 / 参照 / 実行手順）
└── references/
    └── rules.md              # ルール本体
```

### タイプ 2 — セットアップ系

パッケージインストールやファイル生成など、副作用が明確なスキル。セットアップを実行するだけで結果を確認できるため、workspace は不要です。配布用バイナリと eval 設定を含みます。

```
neverthrow-setup/
├── SKILL.md                  # 薄い entry point
├── references/
│   └── rules.md              # セットアップ手順本体
├── evals/                    # eval 設定
│   └── evals.json
└── neverthrow-setup.skill    # 配布用バイナリ
```

### タイプ 3 — モデルの挙動変化を証明するコーディングルール系

モデルのコード生成スタイルを変えるスキル。スキルが実際にモデルの挙動を変えることを示す before/after の証拠として、`workspace/` に eval のイテレーション結果を記録します。

```
neverthrow-coding-rules/
├── SKILL.md                          # 薄い entry point
├── references/
│   └── rules.md                      # ルール本体
├── evals/                            # eval 設定
│   └── evals.json
├── neverthrow-coding-rules.skill     # 配布用バイナリ
└── workspace/                        # eval イテレーション結果
    ├── trigger-eval.json
    ├── iteration-1/
    ├── iteration-2/
    └── iteration-3/
```

カスタムな採点スクリプト（`git log` の出力や、デフォルトの eval runner では拾えない副作用を検証するためのスクリプトなど）が必要な場合は、`workspace/grade.py` として配置します。`<スキル名>-workspace/` のような兄弟ディレクトリをリポジトリ直下に作ってはいけません。eval 関連の成果物は必ずそのスキルディレクトリ配下の `workspace/` に置きます。

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
