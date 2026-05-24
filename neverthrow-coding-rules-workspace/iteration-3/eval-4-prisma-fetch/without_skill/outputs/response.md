# Prisma を使ったユーザー取得関数の実装

## 概要

Prisma を使ってユーザーを取得する TypeScript 関数を実装します。エラーは以下の 2 種類に分類します。

- `not_found`: ユーザーが存在しない場合
- `db`: DB エラーが発生した場合

## 実装

### エラー型の定義

```typescript
type AppError =
  | { type: "not_found"; message: string }
  | { type: "db"; message: string; cause?: unknown };
```

### ユーザー取得関数

```typescript
import { PrismaClient, Prisma } from "@prisma/client";

const prisma = new PrismaClient();

type AppError =
  | { type: "not_found"; message: string }
  | { type: "db"; message: string; cause?: unknown };

type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function getUser(userId: string): Promise<Result<{ id: string; name: string; email: string }, AppError>> {
  try {
    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (user === null) {
      return {
        ok: false,
        error: {
          type: "not_found",
          message: `User with id "${userId}" was not found.`,
        },
      };
    }

    return { ok: true, value: user };
  } catch (err) {
    return {
      ok: false,
      error: {
        type: "db",
        message: "Failed to fetch user from database.",
        cause: err,
      },
    };
  }
}
```

### 使用例

```typescript
async function main() {
  const result = await getUser("user-123");

  if (!result.ok) {
    switch (result.error.type) {
      case "not_found":
        console.error("ユーザーが見つかりません:", result.error.message);
        break;
      case "db":
        console.error("DB エラー:", result.error.message, result.error.cause);
        break;
    }
    return;
  }

  console.log("取得したユーザー:", result.value);
}

main();
```

## 解説

### `findUnique` を使う理由

- `findUnique` は一意なフィールド（`id` など）で検索するための Prisma メソッドです。
- ユーザーが存在しない場合は `null` を返すため、`not_found` の判定が簡単にできます。
- `findFirst` でも同様に実装できますが、ID 検索であれば `findUnique` が適切です。

### エラーハンドリングの方針

| 状況 | 対応 |
|------|------|
| `user === null` | `not_found` エラーを返す |
| Prisma がスローした例外 | `db` エラーを返す |

- Prisma のクエリが失敗した場合（接続エラー、タイムアウトなど）は `catch` ブロックで捕捉し、`db` エラーとして返します。
- `cause` フィールドに元の例外を保持することで、デバッグ時に詳細を確認できます。

### Result 型について

独自の `Result<T, E>` 型を定義し、成功・失敗を明示的に表現しています。これにより：

- 呼び出し側でエラーハンドリングを強制できます
- `switch` 文で型を絞り込めるため、型安全にエラー処理ができます
- 例外をスローしないため、エラーフローが予測しやすくなります
