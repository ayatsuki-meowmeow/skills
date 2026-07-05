# 認証セッション管理 — 実装詳細

## 構成

- `src/auth/session.ts` — セッションの発行・検証

## 技術的判断

- 有効期限は `SESSION_TTL_MINUTES` 定数（60 分）で管理。設定ファイル化は現時点では不要と判断
- 期限判定は `expiresAt` との比較のみ（`isSessionValid`）

## 実装状況

- [x] セッション発行（`createSession`）
- [x] 有効期限の検証（`isSessionValid`）

## 既知の制約・TODO

- セッションストア（永続化）は未実装。現状はインメモリ前提
