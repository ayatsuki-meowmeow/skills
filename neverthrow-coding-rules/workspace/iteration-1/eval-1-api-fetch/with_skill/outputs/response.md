# fetch で /api/users/:id からユーザー情報を取得する実装

## 実装コード

```typescript
import { ResultAsync } from 'neverthrow'

// --- 型定義 ---

type User = {
  id: string
  name: string
  email: string
}

type AppError =
  | { kind: 'not_found'; resource: string }
  | { kind: 'unknown'; cause: unknown }

type AppResultAsync<T> = ResultAsync<T, AppError>

// --- 実装 ---

const fetchUser = (id: string): AppResultAsync<User> =>
  ResultAsync.fromPromise(
    fetch(`/api/users/${id}`).then(async (res) => {
      if (res.status === 404) {
        // 404 は既知のエラーとして throw し、fromPromise の errMapper で AppError に変換する
        throw { _tag: 'not_found' } as const
      }
      if (!res.ok) {
        throw new Error(`Unexpected status: ${res.status}`)
      }
      return res.json() as Promise<User>
    }),
    (e): AppError => {
      if (
        typeof e === 'object' &&
        e !== null &&
        '_tag' in e &&
        (e as { _tag: string })._tag === 'not_found'
      ) {
        return { kind: 'not_found', resource: 'user' }
      }
      return { kind: 'unknown', cause: e }
    },
  )

// --- 使用例 ---

fetchUser('123').match(
  (user) => {
    console.log('取得成功:', user)
  },
  (err) => {
    switch (err.kind) {
      case 'not_found':
        console.error(`リソースが見つかりません: ${err.resource}`)
        return
      case 'unknown':
        console.error('予期しないエラー:', err.cause)
        return
    }
  },
)
```

## 説明

### スキル規約の適用ポイント

**1. `AppError` を判別共用体で定義**

タスク要件に合わせて `not_found` と `unknown` の2種を定義しています。クラス継承は使わず `kind` フィールドで識別します。

**2. `AppResultAsync<T>` 型エイリアスを使用**

返り値型は `ResultAsync<User, AppError>` と直接書かず、`AppResultAsync<User>` エイリアスを使います。

**3. 外部境界を `ResultAsync.fromPromise` でラップ**

`fetch` は外部境界なので `ResultAsync.fromPromise` 経由で `AppError` にマッピングします。`try/catch` で既知のエラーを握り潰すことはしません。

**4. 404 を `not_found` として分離**

`res.status === 404` のときは専用のシグナルオブジェクト `{ _tag: 'not_found' }` を throw し、`errMapper` 内で `{ kind: 'not_found', resource: 'user' }` に変換します。それ以外のエラー（ネットワーク障害・5xx 等）は `{ kind: 'unknown', cause: e }` にまとめます。

**5. `match` + `switch(err.kind)` で exhaustive check**

`match` のエラー側で `switch(err.kind)` を使い、`case` の漏れがあればコンパイルエラーになります。
