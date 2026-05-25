# fetch でユーザー情報を取得する関数の実装

neverthrow コーディング規約に従い、`/api/users/:id` からユーザー情報を取得する関数を実装します。

## 実装コード

```typescript
import { ResultAsync, err } from 'neverthrow'

// --- エラー型定義（判別共用体） ---
type AppError =
  | { kind: 'not_found'; resource: string }
  | { kind: 'unknown'; cause: unknown }

// --- 型エイリアス ---
type AppResultAsync<T> = ResultAsync<T, AppError>

// --- ユーザー型 ---
type User = {
  id: string
  name: string
  email: string
}

// --- 実装 ---
const fetchUser = (id: string): AppResultAsync<User> =>
  ResultAsync.fromPromise(
    fetch(`/api/users/${id}`),
    (e): AppError => ({ kind: 'unknown', cause: e }), // ネットワーク断・例外のみ
  ).andThen((res) => {
    if (res.status === 404)
      return err<User, AppError>({ kind: 'not_found', resource: `/api/users/${id}` })
    if (!res.ok)
      return err<User, AppError>({ kind: 'unknown', cause: res })
    return ResultAsync.fromPromise(
      res.json() as Promise<User>,
      (e): AppError => ({ kind: 'unknown', cause: e }),
    )
  })
```

## 使用例

```typescript
const result = await fetchUser('123')

result.match(
  (user) => {
    console.log('取得成功:', user)
  },
  (err) => {
    switch (err.kind) {
      case 'not_found':
        console.error(`リソースが見つかりません: ${err.resource}`)
        break
      case 'unknown':
        console.error('予期しないエラー:', err.cause)
        break
      // 漏れがあればコンパイルエラーになる
    }
  },
)
```

## 説明

### 規約への準拠

1. **`fromPromise` の errMapper は unknown error 専用**
   - ネットワーク断や予期しない例外（`fetch` が reject した場合）のみを `{ kind: 'unknown', cause: e }` にマップしています。
   - 404 のような「既知のエラー」は errMapper で処理していません。

2. **既知のエラーは `andThen` + `err()` で表現**
   - `res.status === 404` を `andThen` 内で検出し、`err({ kind: 'not_found', ... })` として Result に変換しています。
   - known error を `throw` して errMapper でキャッチする禁止パターンは使っていません。

3. **AppError は判別共用体**
   - `kind` フィールドで識別できる判別共用体として定義しています。クラス継承は使っていません。

4. **型エイリアスの使用**
   - `AppResultAsync<T>` エイリアスを使い、`ResultAsync<T, AppError>` とは直接書いていません。

5. **`match` + `switch` で exhaustive check**
   - 使用例では `switch(err.kind)` を使って全ケースを網羅しており、新しい `kind` が追加された場合にコンパイルエラーで検出できます。
