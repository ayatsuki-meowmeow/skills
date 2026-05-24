# fetch で /api/users/:id からユーザー情報を取得する実装

## 実装コード

```typescript
type User = {
  id: string;
  name: string;
  email: string;
};

type FetchUserError =
  | { type: "not_found" }
  | { type: "unknown"; message: string };

type FetchUserResult =
  | { success: true; data: User }
  | { success: false; error: FetchUserError };

async function fetchUser(id: string): Promise<FetchUserResult> {
  try {
    const response = await fetch(`/api/users/${id}`);

    if (response.status === 404) {
      return {
        success: false,
        error: { type: "not_found" },
      };
    }

    if (!response.ok) {
      return {
        success: false,
        error: {
          type: "unknown",
          message: `HTTP error: ${response.status} ${response.statusText}`,
        },
      };
    }

    const data: User = await response.json();
    return { success: true, data };
  } catch (error) {
    return {
      success: false,
      error: {
        type: "unknown",
        message: error instanceof Error ? error.message : "Unknown error occurred",
      },
    };
  }
}
```

## 使用例

```typescript
const result = await fetchUser("123");

if (result.success) {
  console.log("取得成功:", result.data);
} else if (result.error.type === "not_found") {
  console.log("ユーザーが見つかりません");
} else {
  console.log("エラー:", result.error.message);
}
```

## 説明

- `User` 型でレスポンスの形状を定義しています。
- エラーは `FetchUserError` のユニオン型で `not_found` と `unknown` の2種類を区別します。
- 戻り値は `FetchUserResult` のユニオン型で、成功時は `{ success: true, data: User }`、失敗時は `{ success: false, error: FetchUserError }` を返します。
- HTTP ステータス 404 の場合は `not_found` として扱います。
- ネットワークエラーやその他の HTTP エラーは `unknown` として扱い、エラーメッセージを含めます。
- `response.ok` チェックにより 404 以外の HTTP エラー（500 など）も `unknown` として捕捉します。
