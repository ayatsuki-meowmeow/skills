neverthrow の規約に従い、`ResultAsync` を返す形で実装します。ポイントは以下の通りです。

- **404 は既知のエラー**なので `throw` せず、`andThen` + `err()` で `not_found` として `Result` に表現します。
- **ネットワーク断や JSON パース失敗などの未知のエラー**は `fromPromise` の errMapper で `unknown` にラップします。
- エラー型は**判別共用体**で定義し、関数の返り値には**型エイリアス** `AppResultAsync<T>` を使います。

## エラー型と型エイリアス

```typescript
import { ResultAsync, err } from 'neverthrow'

type AppError =
  | { kind: 'not_found'; resource: string }
  | { kind: 'unknown'; cause: unknown }

type AppResultAsync<T> = ResultAsync<T, AppError>
```

## 実装

```typescript
type User = {
  id: string
  name: string
  email: string
}

const fetchUser = (id: string): AppResultAsync<User> => {
  const url = `/api/users/${id}`

  return ResultAsync.fromPromise(
    fetch(url),
    // errMapper は unknown error 専用（ネットワーク断・例外）
    (e): AppError => ({ kind: 'unknown', cause: e }),
  ).andThen((res) => {
    // 404 は既知のエラー → throw せず err() で not_found に変換
    if (res.status === 404)
      return err<User, AppError>({ kind: 'not_found', resource: url })

    // それ以外の HTTP 異常も既知の失敗として扱い unknown に
    if (!res.ok)
      return err<User, AppError>({ kind: 'unknown', cause: res })

    // JSON パース失敗（reject）は unknown error
    return ResultAsync.fromPromise(
      res.json() as Promise<User>,
      (e): AppError => ({ kind: 'unknown', cause: e }),
    )
  })
}
```

## 呼び出し側での分岐

`match` で成功・失敗を分け、エラーは `switch (err.kind)` で網羅的に処理します。漏れがあればコンパイルエラーになります。

```typescript
fetchUser('123').match(
  (user) => {
    console.log('取得成功:', user)
  },
  (err) => {
    switch (err.kind) {
      case 'not_found':
        console.warn(`ユーザーが見つかりません: ${err.resource}`)
        break
      case 'unknown':
        console.error('不明なエラー:', err.cause)
        break
    }
  },
)
```

### 設計上のポイント

- `fetch` が reject するのはネットワーク断などの**未知のエラー**だけなので、`fromPromise` の errMapper は `unknown` のラップのみを担当します。
- HTTP 404 という**既知の失敗**は `throw` でシグナルを送るのではなく、`andThen` の中で `err()` を返して `Result` に明示的に変換しています（known error を errMapper で処理しない）。
- 返り値は `Result<User, AppError>` と直接書かず、型エイリアス `AppResultAsync<User>` を使っています。
