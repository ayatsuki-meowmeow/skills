# コードレビュー

このプロジェクトは neverthrow を採用しているため、エラーハンドリングの規約に照らしてレビューします。結論から言うと、現状のコードは規約違反がいくつかあるため、`ResultAsync` ベースに書き換えることを推奨します。

## 指摘事項

### 1. 既知のエラーを `throw` で表現している（要修正）

`!res.ok` のとき `throw new Error('fetch failed')` していますが、HTTP のステータス異常（404 / 400 等）は呼び出し側がリカバリ可能な**既知のエラー**です。これは `throw` ではなく `Result` / `ResultAsync` でモデリングすべきです。

特に「ユーザーが存在しない（404）」と「ネットワーク断などの未知のエラー」が、どちらも同じ `Error` として throw されてしまい、呼び出し側で区別できません。

### 2. `try/catch` で既知のエラーを握り潰している（要修正）

`catch (e) { console.error(e); throw e }` は、既知・未知を問わず全エラーを一律に握って再 throw しているだけで、型情報が失われています。既知のエラーは `Result` の `err()` で、未知のエラー（接続断・例外）は `fromPromise` の errMapper でラップする、という分離ができていません。

### 3. 戻り値が `Promise<User>` で成否が型に表れていない（要修正）

戻り値の型 `Promise<User>` には「失敗しうる」という情報がありません。`AppResultAsync<User>` を返すことで、呼び出し側に成否のハンドリングを型で強制できます。

### 4. レスポンスを無検証で `User` にキャストしている（要改善）

`await res.json()` の結果を無条件に `User` として返しています。外部境界からの値なので、本来はバリデーションが望ましいですが、最低限 `json()` の失敗（不正な JSON）も未知エラーとして扱う必要があります。

### 5. `console.error` での副作用混入（要改善）

ドメイン層の取得関数の中でログ出力という副作用を行うのは責務が混ざっています。エラーは `Result` で呼び出し側へ返し、ログ出力するかどうかは上位（アプリケーション境界）で判断させるべきです。

## 改善後のコード

規約に従い、`fromPromise` の errMapper は**未知のエラー専用**とし、HTTP の既知エラーは `andThen` + `err()` で `Result` に変換します。エラー型は判別共用体の `AppError` を使います。

```typescript
import { ResultAsync, err } from 'neverthrow'

// プロジェクト共通の定義（既出ならインポートのみ）
type AppError =
  | { kind: 'validation'; message: string }
  | { kind: 'not_found'; resource: string }
  | { kind: 'unauthorized' }
  | { kind: 'unknown'; cause: unknown }

type AppResultAsync<T> = ResultAsync<T, AppError>

function getUser(id: string): AppResultAsync<User> {
  const url = `/api/users/${id}`

  return ResultAsync.fromPromise(
    fetch(url),
    // errMapper は reject / ネットワーク断などの「未知のエラー」専用
    (e): AppError => ({ kind: 'unknown', cause: e }),
  ).andThen((res) => {
    // HTTP ステータス異常は「既知のエラー」なので err() で Result に変換する
    if (res.status === 404)
      return err<User, AppError>({ kind: 'not_found', resource: url })
    if (res.status === 401)
      return err<User, AppError>({ kind: 'unauthorized' })
    if (!res.ok)
      return err<User, AppError>({ kind: 'unknown', cause: res })

    // json() のパース失敗は未知のエラーとしてラップ
    return ResultAsync.fromPromise(
      res.json() as Promise<User>,
      (e): AppError => ({ kind: 'unknown', cause: e }),
    )
  })
}
```

## 呼び出し側での扱い

`throw` していた頃と違い、呼び出し側は `match` で網羅的にエラーを分岐できます。`kind` の case 漏れがあればコンパイルエラーになります。

```typescript
getUser(id).match(
  (user) => render(user),
  (e) => {
    switch (e.kind) {
      case 'not_found':    return showNotFound(e.resource)
      case 'unauthorized': return redirectToLogin()
      case 'validation':   return showMessage(e.message)
      case 'unknown':      return showGenericError(e.cause)
      // 漏れがあればコンパイルエラー
    }
  },
)
```

なお、この関数を React の presentation 層（hooks / コンポーネント）から使う場合は、neverthrow を直接持ち込まず `queryFn` の中で `match` して unwrap し、TanStack Query 側の `data` / `error` に渡してください。
