# subagent-orchestration スキル比較レポート — iteration-2

**Verdict:** iteration-1 で示唆した短縮方向（並列化セクション廃止・具体例削除・重複記述削減）を実際に適用しても pass 率が 100% 保持されることを確認した。**skill は必要かつ運用可能なサイズに収まる**。

## iteration-2 の目的

iteration-1 の解釈で示唆した「eval-4 / eval-5 の重複記述を削れる」仮説を検証。`rules.md` を **125 行 → 96 行 (-23%)** に短縮した上で、同じ 5 evals を `old_skill` (v1 snapshot) と `new_skill` (v2 trimmed) の 2 条件で走らせた。

## v1 → v2 の変更内容

1. **「オーケストレーターがやらないこと」bullet の圧縮** — 4 項目の列挙 → 1 文。「規模を問わず委譲」の一文は残す (eval-1 の driver)。
2. **役割別の委譲プロンプト具体例を削除** — 調査/実装エージェント向けのフル例示（~20 行）を廃止し、役割別の差分のみ 1 行ずつ残す。抽象「共通要素リスト」で十分か検証。
3. **「並列実行」セクションを「委譲の仕方」節に吸収** — 独立した `## 並列実行` を廃止し、1 文で節末に統合。
4. **「進行報告」セクションを削除** — `SKILL.md` ステップ 5 に同内容があり rules.md 側で重複していた。

## 結果

| Eval | Old (v1) | New (v2) | 備考 |
|---|---|---|---|
| eval-1 small-fix | 3/3 | 3/3 | 委譲数 old 3体 → new 2体。規模問わず委譲は維持 |
| eval-2 ambiguous | 4/4 | 4/4 | 両者 design.md 未決事項経由でエスカレーション |
| eval-3 investigation | 5/5 | 5/5 | 委譲数 old 3並列 → new 1体。共通要素リストだけで design.md/impl.md 参照は成立 |
| eval-4 impl-with-spec | 5/5 | 5/5 | 実装エージェント例示を削っても Sonnet / impl.md 更新は維持 |
| eval-5 parallel | 3/3 | 3/3 | 独立セクション廃止 → 節末 1 文だけでも並列委譲は成立 |
| **合計** | **20/20 (100%)** | **20/20 (100%)** | rules.md -23% |

## 判定

トリミングは安全。削った内容は Claude Code のデフォルト挙動または SKILL.md 側の記述で代替できていた。加えて、新版は具体プロンプト例を削ったにもかかわらず、5 系統の観測点をすべて満たす委譲プロンプトを構造化して生成した — 抽象的な「共通要素リスト」（design.md/impl.md パス指示、エスカレーション境界など）が例示以上に効いていたことを示唆する。委譲数も適正化（例: eval-3 で 3並列 → 1体）しており、規約の簡潔さがプラン設計の簡潔さにも波及した。

## 次のイテレーションで検討する余地

- (a) SKILL.md 本体（現在 27 行）のさらなる圧縮
- (b) description ベースの自動 trigger 精度検証（skill-creator の `run_loop.py`）
- (c) 弱いモデル層 (Sonnet 4.7 / Haiku 4.5) での効き目測定

## 再現方法

```bash
# eval 定義
cat subagent-orchestration/evals/evals.json

# iteration-2 の生応答
ls subagent-orchestration/workspace/iteration-2/eval-*/{old,new}_skill/response.md

# v1 snapshot (baseline) は scratchpad 経由で参照済み
```
