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

# TypeScript コーディング規約

## 禁止事項

TypeScript のコードを書く際、以下は**原則として使用禁止**です:

- `as` キャスト（型アサーション）— あらゆる形式を含む
  - `foo as Bar`
  - `<Bar>foo`
  - `value as Record<string, unknown>` 等のユーティリティ用途も対象
- `any` 型（明示的・暗黙的問わず）
  - `let x: any`
  - `function f(x: any)`
- `@ts-ignore` / `@ts-expect-error` コメント

## 禁止事項を使わずに実装する

代替手段が存在する場合は、許可を求めずそのまま代替実装を提供してよい。ユーザーは実装コードをレビューする。

### `as` キャストの代替

| 用途 | 代替手段 |
|------|---------|
| 外部データの型付け | `zod` によるスキーマ定義とパース |
| 型ガード内のプロパティアクセス | `zod`、または `Object.prototype.hasOwnProperty` + `in` 演算子の組み合わせ |
| `as Record<string, unknown>` | `zod` の `z.record()` またはインデックスシグネチャ付き型定義 |
| 定数の型絞り込み | `as const satisfies T` |
| DOM 要素の型絞り込み | `instanceof` による型ガード |

### `any` の代替

| 用途 | 代替手段 |
|------|---------|
| 外部データ | `unknown` + `zod` パース |
| 汎用関数 | ジェネリクス `<T>` |
| イベントハンドラー | `MouseEvent`、`KeyboardEvent` 等の正確な型 |

### `@ts-ignore` の代替

| 用途 | 代替手段 |
|------|---------|
| 外部ライブラリの型不足 | Declaration Merging（`declare module`） |
| 型エラーの回避 | 型定義の修正、オーバーロード |

## 使用が避けられない場合

真に代替手段がない場合のみ:

1. **実装を止める**
2. **理由を明示する**（なぜ代替手段が取れないのか）
3. **ユーザーに許可を求める**

> `as` キャストを使用したい箇所があります。許可を求めます。
>
> **理由:** 〇〇のため、型安全な代替手段では対応できません。
>
> 許可していただけますか？
