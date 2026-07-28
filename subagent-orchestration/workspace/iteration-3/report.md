# subagent-orchestration スキル比較レポート — iteration-3

**Verdict:** Opus 5 alignment（項目 1 の委譲判断基準・項目 4 の自己申告撤廃・項目 0 のポインタ化）を適用した現行版は、5 evals 21 assertions を **全 pass**。旧版は 18/21。委譲数は合計 **28 体 → 20 体 (-29%)** に減り、削減は小規模タスクに集中している（大きい曖昧タスクでは減らない = 意図どおり）。

## iteration-3 の目的

`docs/2026-07-28-opus5-alignment-plan.md` の項目 0〜7 を適用した後の回帰確認。plan doc §5 が「変更後に既存 eval を回して、削減で品質が落ちていないことを確認する」としていたもの。

- `old_skill` = `origin/main` 時点（rules.md 129 行 / SKILL.md 27 行）
- `new_skill` = alignment 適用後（rules.md 153 行 / SKILL.md 27 行）
- 両 arm ともスナップショット 2 ファイルのみを参照させ、リポジトリの他ファイルは読ませない条件で実行（Opus、各 arm 独立コンテキスト）

**eval-1 は本 iteration で再設計している。** 旧 assertion（`delegates_even_for_small_task` / `does_not_direct_edit`）は項目 1 で撤回した「規模の大小を問わず委譲する」を前提にしており、現行規約と正面から矛盾していたため、観測点を「委譲の判断基準の境界を正しく引けるか」に差し替えた。あわせてプロンプトから仕様の穴（`null` 以外の異常系の扱い）を除き、コミットまで含めることで git 委譲の例外も同時に観測できるようにした。

## 結果

| Eval | Old | New | 委譲数 old → new | 備考 |
|---|---|---|---|---|
| eval-1 small-fix | **2/4** | **4/4** | **8 → 3** | old は「規模が小さい修正でも直接実装はせず、全ての作業を専門サブエージェントに委譲する」と宣言し実装エージェントを起動。new は境界（単一ファイル / 数行 / 仕様判断なし / lint・typecheck で閉じる）を明示して自分で編集 |
| eval-2 ambiguous | 4/4 | 4/4 | 7 → 8 | 両者 design.md 未決事項経由。new は「重い判断」と分類して AskUserQuestion を**使わない**選択をした |
| eval-3 investigation | **4/5** | **5/5** | 4 → 3 | old は全 4 プロンプトにコンテキスト使用率の自己申告を含み `prompt_omits_context_self_report` で fail |
| eval-4 impl-with-spec | 5/5 | 5/5 | **6 → 3** | 方針が固まっているタスクで old は調査 + ドキュメント + doc review を前置。new は実装 → doc review → code review に圧縮 |
| eval-5 parallel | 3/3 | 3/3 | 3 → 3 | 並列委譲は両者成立。new は design.md 作成を調査後に回した |
| **合計** | **18/21 (85.7%)** | **21/21 (100%)** | **28 → 20 (-29%)** | |

## 観測できたこと

**項目 1（委譲の判断基準）は効いている。** eval-1 で old は 8 体、new は 3 体。new が残した 3 体はドキュメント・ドキュメントレビュー・コミットで、いずれも「委譲する」側の条件（reviewer != author の担保 / git 書き込みの権限境界）に該当する。境界の内側にある実装作業だけが直接編集に落ちており、境界の引き方が意図どおり。

**削減は小規模タスクに限定されている。** eval-2（曖昧な機能追加）は 7 → 8 で増えた。new は調査を 2 観点に分けて並列化し、コミットエージェントを条件付きで積んだ結果。判断基準は「真に独立していて並列化できる作業は委譲する」なので規約違反ではなく、**「とにかく委譲」を撤回しても大きいタスクの起動数は減らない**ことの確認になる。

**項目 4（自己申告撤廃）は完全に抜けた。** old の全 28 委譲プロンプトに自己申告指示が入っていたのに対し、new は 20 件すべてで 0 件。5 レンズにコピーされて無意味な数字が返る問題は消えた。

**項目 5（AskUserQuestion 開放）はルート選択が機能している。** new は eval-1（`undefined` の扱い = 選択肢 2〜3 個）と eval-3（リファクタの主眼）で AskUserQuestion を選び、いずれも「1 往復で閉じなければ design.md ルートに切り替える」「決定は design.md の決定事項に転記してから進む」を明記した。一方 eval-2（バッジ機能の仕様全体）では「重い判断」と分類して design.md ルートを選んでいる。軽い判断への開放が重い判断へ漏れていない。

**docs フローは規模で省略されていない。** eval-1 new は 3 行の修正でも design.md 確認 → impl.md 作成 → reviewer != author のドキュメントレビューを維持した（2026-07-28 のユーザー判断「軽微な修正でも docs の例外を設けない」に一致）。ただしこれは **8 → 3 で止まる理由**でもある。項目 1 が削れたのは実装エージェント 1 体分で、残る 3 体は docs とコミットに由来する。起動数をさらに下げたい場合は docs 側に境界を入れる別判断が必要になる。

## 判定

回帰なし。旧版が落とした 3 assertion はいずれも「撤回した規約を前提にしていた観測点」であり、現行版が落とした assertion は無い。alignment は安全に適用できている。

## 次のイテレーションで検討する余地

- (a) `implement-review-loop` / `code-review-agent` の eval 新設 — 項目 2（レンズ抑制の削除）と項目 3（doc review 起動契機）は現在どの eval でも観測できていない
- (b) 項目 2 の副作用確認 — レンズ側抑制を外した結果 Haiku 採点に流れ込む件数と、閾値 80 の妥当性
- (c) 弱いモデル層（Sonnet / Haiku）での効き目測定

## 再現方法

```bash
# eval 定義
cat subagent-orchestration/evals/evals.json

# iteration-3 の生応答
ls subagent-orchestration/workspace/iteration-3/eval-*/{old,new}_skill/response.md

# arm のスキル本文
git show origin/main:subagent-orchestration/references/rules.md   # old
cat subagent-orchestration/references/rules.md                    # new
```
