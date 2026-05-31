`fetch` で `/api/users/:id` からユーザー情報を取得する関数を実装します。

neverthrow の規約に沿って、以下の方針で書きます。

- **既知のエラー（404）** は `Result` でモデリングし、`andThen` + `err()` で表現します。`throw` してから `errMapper` で拾うパターンは使いません。
- **未知のエラー（ネットワーク断・JSON パース失敗・その他の HTTP エラー）** は `unknown` として扱います。`fromPromise` の `errMapper` は、この unknown error（Promise の reject）専用にします。
- 戻り値の型エイリアスには、この関数が**実際に返し得る `kind` だけ**を `E` に明示します（`not_found | unknown`）。`AppError` 全体は渡しません。

```typescript
import { ResultAsync, err } from 'neverthrow'

// この関数が実際に返し得るエラーだけを E に明示する
type FetchUserError = ErrorOf<'not_found' | 'unknown'>

type User = {
  id: string
  name: string
  email: string
}

export const fetchUser = (
  id: string,
): AppResultAsync<User, FetchUserError> =>
  ResultAsync.fromPromise(
    // errMapper はネットワーク断・例外（reject）のみを担当する
    fetch(`/api/users/${id}`),
    (e): FetchUserError => ({ kind: 'unknown', cause: e }),
  ).andThen((res) => {
    // 既知の失敗（404）は throw せず err() で Result に乗せる
    if (res.status === 404)
      return err<User, FetchUserError>({
        kind: 'not_found',
        resource: `/api/users/${id}`,
      })

    // それ以外の HTTP エラーは unknown 扱い
    if (!res.ok)
      return err<User, FetchUserError>({ kind: 'unknown', cause: res })

    // JSON パース失敗（reject）も unknown
    return ResultAsync.fromPromise(
      res.json() as Promise<User>,
      (e): FetchUserError => ({ kind: 'unknown', cause: e }),
    )
  })
```

呼び出し側では `match` で分岐します。`E` を `not_found | unknown` に絞っているので、`switch` はこの 2 つだけを扱えば網羅になり、漏れがあればコンパイルエラーになります。

```typescript
fetchUser('123').match(
  (user) => {
    // 成功時：user は User 型
    console.log(user.name)
  },
  (error) => {
    switch (error.kind) {
      case 'not_found':
        // error.resource が使える
        console.warn(`user not found: ${error.resource}`)
        break
      case 'unknown':
        // error.cause に元の例外/レスポンスが入っている
        console.error('unexpected error', error.cause)
        break
      // 'validation' や 'db' はこの関数の E に存在しないため、
      // ここに書こうとすると型エラーになる
    }
  },
)
```

### 設計のポイント

- **404 を `andThen` + `err()` で表現**: 404 は呼び出し側がリカバリ可能な「既知のエラー」なので `Result` に乗せます。`throw` してから `fromPromise` の `errMapper` で拾うのは規約違反です（`errMapper` は unknown error 専用）。
- **戻り値の型に返し得るエラーが現れる**: シグネチャ `AppResultAsync<User, ErrorOf<'not_found' | 'unknown'>>` を見るだけで、この関数が何を返すか分かります。`db` などを返すコードを書けばコンパイルが通りません。
- **`try/catch` を使わない**: 成否はすべて `Result` で表現し、未知のエラーは `unknown` にラップしてアプリケーション境界まで型として運びます。
