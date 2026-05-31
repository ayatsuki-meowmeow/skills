# コードレビュー

このプロジェクトは neverthrow を採用しているため、エラーハンドリングは neverthrow の規約に沿わせる必要があります。現状のコードは「既知のエラー」と「未知のエラー」を区別せず、すべて `try/catch` + `throw` で処理しており、規約に反します。以下に指摘と改善コードを示します。

## 指摘

### 1. 既知のエラーを `Result` でモデリングしていない（最重要）

`!res.ok`（HTTP エラー）は呼び出し側がリカバリ可能な**既知のエラー**です。これは `throw` ではなく `Result` / `ResultAsync` でモデリングすべきです。現状は `throw new Error('fetch failed')` で送出しており、シグネチャ（`Promise<User>`）からはこの関数が失敗し得ること・どんなエラーを返すのかが一切読み取れません。

### 2. `try/catch` で既知のエラーを握り潰している

`catch (e) { console.error(e); throw e; }` は、既知エラー・未知エラーをまとめて捕まえて再 throw しているだけで、エラーの種別が型に現れません。規約では「`try/catch` で既知のエラーを握り潰す」ことを禁止しています。`console.error` での副作用ログも、エラーの伝播は呼び出し側（最終的にはアプリケーション境界）に任せるべきです。

### 3. 戻り値が生の `Promise<User>` で、エラー型が型レベルに現れていない

返り値には型エイリアス（`AppResultAsync`）を使い、`E` に**実際に返し得る `kind` の部分集合だけ**を明示する必要があります。これにより、シグネチャだけで「この関数が何で失敗するか」が読み手に伝わり、想定外の `kind` を返すコードはコンパイルエラーになります。

### 4. `res.json()` の結果を無検証で `User` とみなしている

`await res.json()` は `any` を返し、それをそのまま `User` として扱っています。パース失敗（不正な JSON）は `fromPromise` の errMapper で `unknown` に変換すべき未知のエラーです。最低限、JSON パース失敗も `ResultAsync` の経路に乗せて取りこぼさないようにします（スキーマ検証まで行う場合は別途バリデーションを `andThen` で追加してください）。

### 5. `fromPromise` の errMapper の責務分離

`fetch` 自体の reject（ネットワーク断・例外）は**未知のエラー**なので errMapper で `unknown` に変換します。一方、HTTP ステータス（404 や 4xx/5xx）は**既知のエラー**なので、`throw` してから errMapper でキャッチするのではなく、`andThen` + `err()` で `Result` に変換します。

## 改善後のコード

```typescript
import { ResultAsync, err } from 'neverthrow'

// この関数が実際に返し得る kind だけに E を絞る。
// 404 は not_found、それ以外の HTTP 失敗・ネットワーク断・JSON パース失敗は unknown。
type GetUserError = ErrorOf<'not_found' | 'unknown'>

const getUser = (id: string): AppResultAsync<User, GetUserError> =>
  ResultAsync.fromPromise(
    fetch(`/api/users/${id}`),
    // reject（ネットワーク断・例外）= 未知のエラーのみを担当
    (e): GetUserError => ({ kind: 'unknown', cause: e }),
  ).andThen((res) => {
    // 既知のエラーは andThen + err() で Result に表現する
    if (res.status === 404)
      return err<User, GetUserError>({
        kind: 'not_found',
        resource: `/api/users/${id}`,
      })
    if (!res.ok)
      return err<User, GetUserError>({ kind: 'unknown', cause: res })

    // JSON パース失敗も取りこぼさず未知のエラーに変換する
    return ResultAsync.fromPromise(
      res.json() as Promise<User>,
      (e): GetUserError => ({ kind: 'unknown', cause: e }),
    )
  })
```

## 呼び出し側の例

戻り値の `E` を `'not_found' | 'unknown'` に絞っているため、`match` の `switch` はこの 2 種類だけを扱えばよく、漏れがあればコンパイルエラーになります（`'db'` や `'validation'` はそもそも型に存在しないため書けません）。

```typescript
getUser(id).match(
  (user) => {
    // 成功時の処理
  },
  (e) => {
    switch (e.kind) {
      case 'not_found':
        return // 404 用の処理
      case 'unknown':
        return // 予期せぬ失敗用の処理
    }
  },
)
```

## 補足

- もし `getUser` を FE の presentation 層（React コンポーネント・hooks・TanStack Query の `queryFn`）から使う場合は、presentation 層で neverthrow を使わず、`queryFn` の中で `match` して unwrap し、TanStack Query の loading / data / error の3状態に委ねてください。
- レスポンスの型安全性をさらに高めたい場合は、`res.json()` 後に zod 等でスキーマ検証を行い、検証失敗を `validation` の既知エラーとして `andThen` + `err()` で表現することを検討してください（その場合は `E` に `'validation'` を追加します）。
