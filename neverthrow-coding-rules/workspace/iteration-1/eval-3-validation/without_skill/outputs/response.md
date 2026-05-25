# バリデーション関数の実装

## 実装コード

```typescript
type ValidationError = {
  field: string;
  message: string;
};

type ValidationResult =
  | { success: true }
  | { success: false; errors: ValidationError[] };

function validateUserInput(name: string, email: string): ValidationResult {
  const errors: ValidationError[] = [];

  if (name.length < 1) {
    errors.push({ field: "name", message: "名前は1文字以上入力してください。" });
  }

  if (!email.includes("@")) {
    errors.push({ field: "email", message: "メールアドレスには @ を含める必要があります。" });
  }

  if (errors.length > 0) {
    return { success: false, errors };
  }

  return { success: true };
}
```

## 使用例

```typescript
const result1 = validateUserInput("Alice", "alice@example.com");
// => { success: true }

const result2 = validateUserInput("", "not-an-email");
// => {
//      success: false,
//      errors: [
//        { field: "name", message: "名前は1文字以上入力してください。" },
//        { field: "email", message: "メールアドレスには @ を含める必要があります。" }
//      ]
//    }

if (!result2.success) {
  result2.errors.forEach((e) => console.error(`[${e.field}] ${e.message}`));
}
```

## 説明

- `ValidationResult` はユニオン型で、成功時と失敗時で型が明確に分かれます。
- バリデーションエラーは配列に蓄積し、複数のフィールドが同時に失敗した場合もすべてのエラーを返します。
- 呼び出し側は `result.success` で分岐することで、型安全にエラー情報にアクセスできます。
