# superpowers 実走トライアル計画

作成日: 2026-08-31
対象リポジトリ: `~/koshu`（実走環境） / `~/skills`（取り込み先）
評価対象: [obra/superpowers](https://github.com/obra/superpowers) v6.3.0（`~/superpowers` に clone 済み、MIT）
目的: superpowers を koshu で 1 回だけ実走させ、`~/skills` のワークフロー 4 スキルに取り込む候補を判定する

---

## 0. このドキュメントの使い方

トライアル前に観察項目を固定し、走らせた後に「なんとなく良かった」で終わらせないための記録用紙。
セクション 3 の記録欄はトライアル中／直後に埋める。セクション 4 の判定はその記録だけを根拠に行う。

---

## 1. 環境構築

### 1-1. トライアル用 worktree を作る

```bash
cd ~/koshu
.claude/skills/koshu-worktree/scripts/koshu-wt <branch> origin/develop
```

`~/koshu-worktrees/<branch>` が作られ、`.env.local` / `.vercel` の symlink、非 `team-*` スキルの symlink、
`.claude/tickets` / `.claude/eslint` の symlink、`pnpm run setup` までが完了する。

### 1-2. 衝突するスキルの symlink を worktree 内だけで外す

`.claude/skills` の非 `team-*` は**メインへの symlink**なので、worktree 側で消してもメインは無傷。
`pnpm run apply-skills` は `team-*` しか同期しないため復活もしない。

```bash
cd ~/koshu-worktrees/<branch>
mkdir -p .claude/skills-disabled
for s in subagent-orchestration implement-review-loop code-review-agent ticket-docs koshu-worktree; do
  mv ".claude/skills/$s" ".claude/skills-disabled/$s"
done
ls -1 .claude/skills
```

**外す 5 つ（superpowers と正面衝突）**

| 外すスキル | 衝突する superpowers 側 |
|---|---|
| `subagent-orchestration` | `subagent-driven-development` / `dispatching-parallel-agents` |
| `implement-review-loop` | `executing-plans` |
| `code-review-agent` | `requesting-code-review` / `receiving-code-review` |
| `ticket-docs` | `brainstorming` / `writing-plans` |
| `koshu-worktree` | `using-git-worktrees` |

**残す（直交。消すとコード品質が落ちて評価が濁る）**

`ts-type-safety` / `function-signature-typing` / `readonly-array-type` / `koshu-local-eslint` /
`conflict-resolution` / `team-*` 8 個

- `team-test` は必須。superpowers の TDD スキルが書くテストが `check:no-to-be` や team のテスト規約に
  違反すると、評価が「規約違反の後始末」に埋もれる。
- `team-git` も残す。実プロジェクトなのでチームの git 規約は破らない。

### 1-3. superpowers をセッション限定で読み込む

グローバル install（`/plugin install`）はしない。`--plugin-dir` はそのセッションのみ有効で、
`~/skills` や koshu 本体のセッションには一切影響しない。

```bash
cd ~/koshu-worktrees/<branch>
claude --plugin-dir ~/superpowers
```

スキルは自動発火するので、起動後は普通に依頼するだけ。手動 invoke は不要。

### 1-4. 環境差分として認識しておくこと

worktree の `.claude/` には `settings.json` と `hooks/` が symlink されない（`koshu-wt` の対象外）。
したがってトライアル中は以下が**発火しない**:

- `lint-edited-file.py`（Write/Edit 後の自動 lint）
- `block-force-push.py` / `no-verify-guard.sh`
- `warn-sibling-word.py`（`settings.local.json` 由来）

→ 編集後の lint は自動で入らないので、区切りごとに `pnpm run check` を手で回す。
これは既存の worktree 運用と同じ条件であり、superpowers の評価には影響しない。

### 1-5. ベースライン記録（2026-08-31 実測）

superpowers の `using-git-worktrees` が要求する「クリーンなテストベースライン」を、
worktree 作成直後に `pnpm run check` で実測した結果:

```
Tasks:    6 successful, 6 total
Cached:    1 cached, 6 total
  Time:    1m26.737s
Type Errors  no errors
```

`check:lint` / `check:knip` / `check:no-to-be` / `check:types` / `test` すべてグリーン。
トライアル中に落ちたものは、すべて superpowers セッションの変更由来と判定してよい。

---

## 2. タスク選定基準

- 規模: 半日〜1 日
- 自己完結（他チケットと依存しない）
- クリティカルパス外
- **テストが既にある領域**（最重要。テスト基盤が無い場所を選ぶと
  `test-driven-development` の導入コストに全評価が埋もれる）

選定タスク: **KS-547 — `PUT /v1/google_configs/optout` の API クライアント実装**
ブランチ名: `KS-547/google-reserve-optout-api`（base `origin/develop`）
worktree: `/Users/konoreiji/koshu-worktrees/KS-547-google-reserve-optout-api`

命名は KS-545（`google-reserve-config-update-api` = API クライアント実装本体）の型に合わせた。
画面配線チケットが後続する場合は KS-561 の型に倣って `-api-binding` になる想定。

base の注意: KS-545（PR #874, draft・develop 未マージ）が追加した共有コード
（`google-config-response.ts` の `parseAsResult` / `PreconditionError` 系）に依存することが
brainstorming で判明した場合は、worktree を作り直さず `origin/develop` から
`KS-545/google-reserve-config-update-api` へ rebase して stack する。

---

## 3. 観察項目（走らせる前に固定 / 走らせた後に記録）

| # | 観察点 | superpowers 側 | 現行 `~/skills` 側 | 記録 |
|---|---|---|---|---|
| 1 | 意図の引き出し | `brainstorming`（ソクラテス式に質問して design doc を出す） | `ticket-docs` の design.md | |
| 2 | 計画の粒度 | `writing-plans`（1 タスク 2〜5 分、ファイルパスと検証手順まで明記） | impl.md の方針記述 | |
| 3 | 実装エージェントの事故率 | `subagent-driven-development`（タスクごとに fresh subagent） | `subagent-orchestration` | |
| 4 | レビューの当たり方 | `requesting-code-review`（2 段: 仕様適合 → 品質） | `code-review-agent`（5 lens + confidence 75） | |
| 5 | 完了判定の強さ | `test-driven-development` + `verification-before-completion` | machine-verification gate | |
| 6 | デバッグ手順 | `systematic-debugging`（4 フェーズ根本原因追跡） | 対応物なし | |
| 7 | ブランチの畳み方 | `finishing-a-development-branch` | `commit-workflow`（コミット単位まで） | |
| 8 | プロセスの重さ | 全体を通した体感（待ち時間・介入回数・手戻り） | — | |

自由記述（想定外に良かった / 悪かったこと）:

---

## 4. 判定

観察項目のうち、セクション 3 の記録を根拠に「取り込む」と判断したものだけを列挙する。

| 取り込む対象 | 根拠（観察項目 #） | 移植方針 |
|---|---|---|
| | | |

移植のルール:

- **ファイルをコピーしない。** `SKILL.md`（薄い entry / 20〜35 行）+ `references/rules.md` の
  リポジトリ規約に書き直す（`CLAUDE.md` 参照）。
- 挙動を変えるスキルは Type 3 扱い。`evals/evals.json` と `workspace/iteration-N/` で
  適用前後の差を証跡として残す。
- superpowers は全ハーネス対応のため記述が汎用的。Opus 5 前提のチューニング
  （`docs/2026-07-28-opus5-alignment-plan.md`）と噛み合うか確認してから写す。
- 規約本文を実質流用する場合は `references/rules.md` に出典 1 行を残す（MIT）。

---

## 5. 後始末

```bash
# 無効化したスキルの symlink を戻す（worktree を残す場合）
cd ~/koshu-worktrees/<branch>
mv .claude/skills-disabled/* .claude/skills/ && rmdir .claude/skills-disabled

# worktree ごと畳む場合
cd ~/koshu && git worktree remove ../koshu-worktrees/<branch>
```

`--plugin-dir` はセッション限定なので、プラグインの後始末は不要（`~/superpowers` の clone を
消すかどうかだけ）。グローバル install していないため `/plugin uninstall` も不要。
