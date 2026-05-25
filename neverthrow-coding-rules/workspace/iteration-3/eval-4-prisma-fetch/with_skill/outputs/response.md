# Prisma でユーザーを取得する関数の実装

neverthrow コーディング規約に従い、`ResultAsync` を使って実装します。

## 規約のポイント

- `ResultAsync.fromPromise` の errMapper は **DB 例外（unknown error）専用**
- ユーザーが存在しない（`null` が返ってきた）という **既知の失敗** は `andThen` + `err()` で表現する
- エラー型は判別共用体（`AppError`）で定義し、クラス継承は使わない
- 返り値には `AppResultAsync<T>` エイリアスを使う

## 実装

```typescript
import { Result, ResultAsync, err, ok } from 'neverthrow'
import { PrismaClient } from '@prisma/client'

// -------- AppError 型 --------
type AppError =
  | { kind: 'not_found'; resource: string }
  | { kind: 'db'; cause: unknown }

// -------- 型エイリアス --------
type AppResult<T> = Result<T, AppError>
type AppResultAsync<T> = ResultAsync<T, AppError>

// -------- Prisma クライアント --------
const prisma = new PrismaClient()

// -------- ユーティリティ: DB Promise を AppResultAsync に変換 --------
const fromDb = <T>(promise: Promise<T>): AppResultAsync<T> =>
  ResultAsync.fromPromise(
    promise,
    (e): AppError => ({ kind: 'db', cause: e }), // unknown error（DB 例外）のみ担当
  )

// -------- ユーザー取得関数 --------
type User = {
  id: number
  name: string
  email: string
}

const getUser = (id: number): AppResultAsync<User> =>
  fromDb(
    prisma.user.findUnique({ where: { id } }),
  ).andThen((user) => {
    // findUnique は存在しない場合 null を返す → 既知の失敗なので andThen + err() で表現
    if (user === null) {
      return err<User, AppError>({ kind: 'not_found', resource: `user:${id}` })
    }
    return ok(user)
  })
```

## 呼び出し例

```typescript
const result = await getUser(42)

result.match(
  (user) => {
    console.log('取得成功:', user.name)
  },
  (error) => {
    switch (error.kind) {
      case 'not_found':
        console.error(`ユーザーが見つかりません: ${error.resource}`)
        break
      case 'db':
        console.error('DB エラー:', error.cause)
        break
      // 新しい kind を追加し忘れるとコンパイルエラーになる（網羅チェック）
    }
  },
)
```

## 設計の説明

| 失敗ケース | 処理方法 | 理由 |
|-----------|---------|------|
| `findUnique` が `null` を返す（ユーザー不在） | `andThen` + `err({ kind: 'not_found', ... })` | 呼び出し側がリカバリできる**既知の失敗**のため、Result でモデリングする |
| Prisma が例外を throw する（接続断・クエリエラー等） | `fromPromise` の errMapper で `{ kind: 'db', cause: e }` に変換 | Promise が reject した場合（**unknown error**）のみ errMapper が担当する |

`fromPromise` の errMapper は「DB が例外を投げた場合（不明な失敗）」のみを担当し、
「ユーザーが存在しない（既知の失敗）」は `andThen` の中で明示的に `err()` として返すのが規約の核心です。
