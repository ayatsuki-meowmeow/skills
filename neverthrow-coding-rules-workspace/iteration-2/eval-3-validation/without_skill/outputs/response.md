# バリデーション関数の TypeScript 実装

名前（string）とメール（string）を受け取るバリデーション関数を実装します。バリデーション失敗時はエラーメッセージを返します。

## 実装コード

```typescript
type ValidationResult =
  | { success: true }
  | { success: false; errors: string[] };

function validateUser(name: string, email: string): ValidationResult {
  const errors: string[] = [];

  if (name.length < 1) {
    errors.push("名前は1文字以上で入力してください。");
  }

  if (!email.includes("@")) {
    errors.push("メールアドレスには @ を含める必要があります。");
  }

  if (errors.length > 0) {
    return { success: false, errors };
  }

  return { success: true };
}
```

## 使用例

```typescript
const result1 = validateUser("Alice", "alice@example.com");
if (result1.success) {
  console.log("バリデーション成功");
} else {
  console.log("エラー:", result1.errors);
}
// => バリデーション成功

const result2 = validateUser("", "not-an-email");
if (!result2.success) {
  console.log("エラー:", result2.errors);
}
// => エラー: ["名前は1文字以上で入力してください。", "メールアドレスには @ を含める必要があります。"]
```

## 解説

- `ValidationResult` 型は判別共用体（discriminated union）を使い、成功・失敗を型安全に表現します。
- バリデーションエラーは配列 `errors` に蓄積し、複数のエラーをまとめて返せるようにしています。
- 名前のチェック: `name.length < 1` で空文字を弾きます。
- メールのチェック: `email.includes("@")` で `@` の存在を確認します。
- エラーがなければ `{ success: true }` を返し、1件以上あれば `{ success: false, errors }` を返します。
