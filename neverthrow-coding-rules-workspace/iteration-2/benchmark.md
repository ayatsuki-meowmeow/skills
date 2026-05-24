# Benchmark: neverthrow-coding-rules — iteration-2

**モデル**: claude-sonnet-4-6  
**日時**: 2026-05-24  
**Evals**: eval-1-api-fetch, eval-2-code-review, eval-3-validation（各1回）

---

## サマリー

| メトリクス | with_skill | without_skill | Delta |
|-----------|-----------|--------------|-------|
| Pass Rate | **1.00** ± 0.00 | 0.17 ± 0.12 | **+0.83** |
| 実行時間 | 36.2s ± 7.5s | 31.2s ± 7.7s | +5.0s |
| トークン数 | 12,946 ± 833 | 10,186 ± 260 | +2,760 |

---

## Eval 別詳細

### eval-1-api-fetch

| | with_skill | without_skill |
|--|-----------|--------------|
| Pass Rate | 4/4 (100%) | 0/4 (0%) |
| 実行時間 | 28.2s | 35.6s |
| トークン数 | 11,842 | 10,294 |

**with_skill**: ResultAsync.fromPromise + andThen パターンで規約通りの実装。AppResultAsync<T> エイリアス使用。  
**without_skill**: Promise<FetchUserResult> の独自ユニオン型 + try/catch で実装。neverthrow を使わない。

### eval-2-code-review

| | with_skill | without_skill |
|--|-----------|--------------|
| Pass Rate | 4/4 (100%) | 1/4 (25%) |
| 実行時間 | 46.3s | 37.6s |
| トークン数 | 13,855 | 10,436 |

**with_skill**: 4つすべての規約違反を指摘し、AppResultAsync + AppError 判別共用体への移行例を提示。  
**without_skill**: try/catch の冗長さは指摘するが、neverthrow/ResultAsync への移行は提案しない。改善案として zod やクラス継承を提案。

### eval-3-validation

| | with_skill | without_skill |
|--|-----------|--------------|
| Pass Rate | 4/4 (100%) | 1/4 (25%) |
| 実行時間 | 34.2s | 20.4s |
| トークン数 | 13,141 | 9,828 |

**with_skill**: AppResult<T> エイリアス + ok()/err({ kind: 'validation', ... }) パターンで規約通りの実装。  
**without_skill**: success フラグパターンの独自ユニオン型で実装。neverthrow の ok()/err() は使わない。

---

## 考察

- **スキルの効果は iteration-1 と一致**（with_skill 100%、without_skill 16.7%）。結果の再現性が確認された。
- **スキルなしの傾向**:
  - fetch 実装：独自ユニオン型 + try/catch（neverthrow ゼロ）
  - コードレビュー：zod やクラス継承を提案し neverthrow への移行を見逃す
  - バリデーション：success フラグパターン（neverthrow ゼロ）
- **スキルのコスト**: +5.0s / +2,760 トークンの増加は規約準拠の品質向上に対して妥当なトレードオフ。