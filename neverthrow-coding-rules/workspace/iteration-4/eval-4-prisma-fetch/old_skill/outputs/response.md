neverthrow のコーディング規約に従って実装します。ポイントは以下の通りです。

- 返り値は `ResultAsync<T, AppError>` を直接書かず、型エイリアス `AppResultAsync<T>` を使う。
- エラー型は**判別共用体**（`kind` フィールドで識別）で定義し、クラス継承は使わない。これにより `switch` の網羅チェックがコンパイラで保証される。
- **DB エラー（未知のエラー）** は `ResultAsync.fromPromise` の errMapper で `{ kind: 'db' }` に変換する。Prisma の reject はすべて DB 障害として扱えるため、errMapper のみで完結する。
- **not_found（既知のエラー）** は errMapper では処理しない。`andThen` + `err()` で Result に変換する。`throw` してシグナルを送り errMapper でキャッチするパターンは禁止されているため使わない。

## エラー型と型エイリアス

```typescript
import { ResultAsync, err, ok } from 'neverthrow'

type AppError =
  | { kind: 'not_found'; resource: string }
  | { kind: 'db'; cause: unknown }

type AppResultAsync<T> = ResultAsync<T, AppError>
```

## ユーザー取得関数

```typescript
import { PrismaClient, type User } from '@prisma/client'

const prisma = new PrismaClient()

// DB（Prisma）境界のヘルパー。reject はすべて unknown な DB 障害として扱う
const fromDb = <T>(promise: Promise<T>): AppResultAsync<T> =>
  ResultAsync.fromPromise(promise, (e): AppError => ({ kind: 'db', cause: e }))

export const getUser = (id: string): AppResultAsync<User> =>
  // DB エラーは errMapper（db）で。
  fromDb(prisma.user.findUnique({ where: { id } }))
    // not_found は既知のエラーなので throw せず andThen + err() で表現する
    .andThen((user) =>
      user === null
        ? err<User, AppError>({ kind: 'not_found', resource: `user:${id}` })
        : ok<User, AppError>(user),
    )
```

## 呼び出し側での分岐

`match` でエラーを分岐します。`kind` による `switch` なので、エラー種別の追加漏れがあればコンパイルエラーになります。

```typescript
getUser('user-123').match(
  (user) => {
    console.log('found:', user.name)
  },
  (e) => {
    switch (e.kind) {
      case 'not_found':
        console.warn('user not found:', e.resource)
        return
      case 'db':
        console.error('db error:', e.cause)
        return
      // 種別を追加すると、ここで網羅チェックが効く
    }
  },
)
```

### 補足

- `findUnique` は対象が無いとき例外ではなく `null` を返すため、`not_found` を「既知のエラー」として `andThen` 内で扱えます。例外を投げる `findUniqueOrThrow` ではなく `findUnique` を使うのが、規約（known error を throw しない）と整合します。
- `User` 型は `@prisma/client` の生成型をそのまま利用しています。プロジェクトの import パスに合わせて調整してください。
