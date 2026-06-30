---
name: neverthrow-coding-rules
description: |
  neverthrow を使ったプロジェクトで TypeScript コードを書くときに必ず参照すべきコーディング規約スキル。
  fetch・DB・バリデーション等の実装タスクや TypeScript コードレビューで、このスキルのルールを強制する。

  TRIGGER:
  - TypeScript で fetch / API コール / DB アクセス / バリデーション関数を実装するよう依頼されたとき
  - try/catch・async/await・Promise を含む TypeScript コードを書くとき
  - TypeScript / neverthrow のコードレビューを依頼されたとき
  - "Result型" "ResultAsync" "neverthrow" "エラーハンドリング" が含まれる TypeScript 実装タスク
  - エラーを返す関数・サービス層・リポジトリ層を TypeScript で書くとき

  SKIP:
  - FE presentation 層（React コンポーネント・hooks・TanStack Query の queryFn 等）
  - neverthrow の初期導入・セットアップ（neverthrow-setup スキルが担当）
  - コーディング以外のタスク（設計相談・調査のみ）
  - JavaScript のみのファイル（.js / .jsx）
---

# neverthrow Coding Rules

## 目的

neverthrow が導入された TypeScript プロジェクトで、`AppError` の判別共用体・`E` 必須の型エイリアス・`fromPromise` の errMapper 用途分離などの規約を強制する。

## 参照

- ルール本体は `references/rules.md` を参照する。

## 実行手順

1. 作業開始時に `references/rules.md` を読み、エラー分類・型エイリアス・外部境界変換のルールを把握する。
2. 関数の戻り値は必ず `AppResult` / `AppResultAsync` を使い、`E` には実際に返し得る `kind` の部分集合だけを `ErrorOf<...>` で明示する。
3. `fromPromise` の errMapper は unknown error 専用とし、HTTP ステータス等の known error は `andThen` + `err()` で表現する。
4. presentation 層では neverthrow を使わず、`match` で unwrap して TanStack Query 等に委譲する。
5. 規約から外れる必要がある場合は `references/rules.md` の「やってはいけないこと」を確認し、ユーザーに判断を仰ぐ。
