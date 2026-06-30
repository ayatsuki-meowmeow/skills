---
name: ts-type-safety
description: |
  TypeScript のコーディング規約を適用するスキル。以下の禁止事項を強制する:
  - `as` キャスト（型アサーション）— `as Record<string, unknown>` 等のユーティリティ用途も含む
  - `any` 型
  - `@ts-ignore` / `@ts-expect-error` コメント

  TRIGGER when:
  - .ts / .tsx ファイルを編集・新規作成するとき
  - TypeScript のコードを実装・計画するよう依頼されたとき（「TypeScript で〜を実装して」「〜のコードを書いて」など）
  - TypeScript のコードが会話のコンテキストに含まれているとき

  SKIP:
  - TypeScript を含まない純粋な JavaScript（.js / .jsx）
  - コーディング以外のタスク（調査、ドキュメント作成、設計相談のみなど）
---

# TypeScript Type Safety

## 目的

TypeScript コードで `as` キャスト・`any` 型・`@ts-ignore` の使用を禁止し、`zod` / ジェネリクス / 型ガードなどの型安全な代替手段で実装させる。

## 参照

- ルール本体は `references/rules.md` を参照する。

## 実行手順

1. 作業開始時に `references/rules.md` を読み、禁止事項と代替手段の対応表を把握する。
2. .ts / .tsx の実装・修正時、`as` / `any` / `@ts-ignore` を書かず、代替手段が存在するならそのまま代替実装を提供する。
3. 真に代替手段がない箇所のみ `references/rules.md` の「使用が避けられない場合」に従い、理由を明示してユーザーに許可を求める。
