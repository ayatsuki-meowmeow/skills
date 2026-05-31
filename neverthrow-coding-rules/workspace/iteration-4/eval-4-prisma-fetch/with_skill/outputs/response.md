neverthrow の規約に従って実装しました。ポイントは以下の通りです。

- **`fromPromise` の errMapper は unknown error（reject / 接続断）専用**として使い、ここでは Prisma の reject を `db` エラーに変換します。
- **`not_found` は既知のエラー**なので、Prisma が返した `null` を見て `andThen` + `err()` で Result に表現します（errMapper の中で握り潰さない）。
- 戻り値は型エイリアス `AppResultAsync` を使い、`E` には**この関数が実際に返し得る `kind` だけ**（`not_found | db`）を明示します。`AppError` 全体は渡しません。

```typescript
import { PrismaClient, type User } from '@prisma/client'
import { ResultAsync, err, ok } from 'neverthrow'
// AppError / AppResultAsync / ErrorOf はセットアップ済みとする

const prisma = new PrismaClient()

// この関数が返し得るエラーだけに E を絞る
type FetchUserError = ErrorOf<'not_found' | 'db'>

// DB アクセスのラッパー — reject（接続断・予期せぬ例外）は db エラーに変換
const fromDb = <T>(promise: Promise<T>): AppResultAsync<T, ErrorOf<'db'>> =>
  ResultAsync.fromPromise(promise, (e): ErrorOf<'db'> => ({ kind: 'db', cause: e }))

export const fetchUser = (id: string): AppResultAsync<User, FetchUserError> =>
  // 1. DB アクセスの失敗（reject）は fromDb が db エラーに変換
  fromDb(prisma.user.findUnique({ where: { id } }))
    // 2. user が null = 既知のエラー。throw せず andThen + err() で not_found に
    .andThen((user) =>
      user
        ? ok<User, FetchUserError>(user)
        : err<User, FetchUserError>({ kind: 'not_found', resource: 'user' }),
    )
```

### 呼び出し側

`E` を `not_found | db` に絞っているので、`switch` はこの 2 つだけを扱えば網羅チェックが通ります（`validation` などを書くと型に存在せずコンパイルエラー）。

```typescript
fetchUser(id).match(
  (user) => {
    // 成功: user は User 型
  },
  (e) => {
    switch (e.kind) {
      case 'not_found':
        return /* 404 相当の処理（e.resource が使える） */
      case 'db':
        return /* DB エラーの処理（e.cause が使える） */
    }
  },
)
```

補足:

- `prisma.user.findUnique` は対象が無いとき `null` を返すため、`not_found` 判定は `null` チェックで行っています。`findUniqueOrThrow` のように throw する API を使うと既知のエラーが reject 経由になり、errMapper で known error を扱う禁止パターンに陥るため、ここでは `findUnique` を使います。
- バグ起因の予期せぬ例外（OOM 等）はそのまま `throw` させ、アプリケーション境界でキャッチする方針です。Result に入れるのは呼び出し側がリカバリ可能な `not_found` / `db` のみです。
