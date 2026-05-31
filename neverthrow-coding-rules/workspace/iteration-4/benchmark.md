# Skill Benchmark: neverthrow-coding-rules (iteration-4 — E 明示精度の検証)

**Model**: claude-opus-4-8  
**Config A** = with_skill（E 明示必須版）, **Config B** = old_skill（git HEAD / E 固定版）  
**Evals**: eval-1-api-fetch / eval-2-code-review / eval-3-validation / eval-4-prisma-fetch（各1 run）

## Summary

| Metric | with_skill | old_skill | Delta |
|--------|-----------|-----------|-------|
| Pass Rate | 100% | 44% | +56pt |
| Time | 44.4s | 45.0s | -0.7s |
| Tokens | 16874 | 15737 | +1137 |

## Per-eval pass rate

| Eval | with_skill | old_skill |
|------|-----------|-----------|
| eval-1-api-fetch | 4/4 | 2/4 |
| eval-2-code-review | 4/4 | 2/4 |
| eval-3-validation | 4/4 | 1/4 |
| eval-4-prisma-fetch | 4/4 | 2/4 |

## ガードレール核心アサーション

| Assertion | with_skill | old_skill |
|-----------|-----------|-----------|
| E を型引数として明示している | 4/4 | 0/4 |
| E が AppError 全体でなく部分集合になっている | 4/4 | 0/4 |