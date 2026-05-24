# コードレビュー結果

## レビュー対象コード

```typescript
async function getUser(id: string): Promise<User> {
  try {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) throw new Error('fetch failed');
    return await res.json();
  } catch (e) {
    console.error(e);
    throw e;
  }
}
```

---

## 問題点

### 1. 戻り値の型が `Promise<User>` になっている（規約違反）

neverthrow コーディング規約では、domain 層の非同期関数は `AppResultAsync<T>` を返す必要があります。`Promise<User>` のままでは、呼び出し側がエラーを `try/catch` で処理せざるを得ず、エラーハンドリングの漏れが静的に検出できません。

### 2. `try/catch` で既知のエラーを処理している（規約違反）

`res.ok` が `false` のケース（HTTP 400系・404 等）は**既知のエラー**です。規約では既知のエラーを `throw` で扱うのではなく、`Result` / `ResultAsync` でモデリングする必要があります。

### 3. 外部境界（fetch）を `ResultAsync.fromPromise` でラップしていない（規約違反）

fetch 等の外部境界は `ResultAsync.fromPromise` を使って `AppError` にマッピングする必要があります。生の `fetch` を直接呼び出し `try/catch` で処理するパターンは規約で禁止されています。

### 4. エラーが `AppError` 判別共用体で表現されていない

`throw new Error('fetch failed')` は文字列メッセージを持つ汎用 `Error` です。規約では `AppError` の判別共用体（`kind` フィールドで識別）を使う必要があります。これにより `switch(err.kind)` による exhaustive check が可能になります。

### 5. `console.error` して `throw e` するだけのキャッチは冗長

既知のエラーを `Result` で表現すれば、このような「ログして再スロー」パターンは不要になります。

---

## 改善案

### AppError 型の定義（共通）

```typescript
type AppError =
  | { kind: 'not_found'; resource: string }
  | { kind: 'network'; cause: unknown }
  | { kind: 'unknown'; cause: unknown }

type AppResultAsync<T> = ResultAsync<T, AppError>
```

### fetch ヘルパーの定義

外部境界を一箇所にまとめ、レスポンスのステータスコードに応じて適切な `AppError` にマッピングします。

```typescript
import { ResultAsync } from 'neverthrow'

const fromFetch = <T>(req: RequestInfo): AppResultAsync<T> =>
  ResultAsync.fromPromise(
    fetch(req).then(async (res) => {
      if (res.status === 404) {
        return Promise.reject({ kind: 'not_found', resource: String(req) } satisfies AppError)
      }
      if (!res.ok) {
        return Promise.reject({ kind: 'network', cause: res.statusText } satisfies AppError)
      }
      return res.json() as Promise<T>
    }),
    (e): AppError =>
      isAppError(e) ? e : { kind: 'unknown', cause: e },
  )

function isAppError(e: unknown): e is AppError {
  return typeof e === 'object' && e !== null && 'kind' in e
}
```

### getUser の改善後

```typescript
function getUser(id: string): AppResultAsync<User> {
  return fromFetch<User>(`/api/users/${id}`)
}
```

### 呼び出し側での使い方

```typescript
getUser(id).match(
  (user) => {
    // 成功時の処理
    console.log(user)
  },
  (err) => {
    switch (err.kind) {
      case 'not_found':
        // ユーザーが存在しない
        return showNotFoundMessage(err.resource)
      case 'network':
        // ネットワークエラー
        return showNetworkError(err.cause)
      case 'unknown':
        // 予期しないエラー
        return showUnexpectedError(err.cause)
      // 漏れがあればコンパイルエラーになる
    }
  },
)
```

---

## まとめ

| 問題 | 規約 | 改善 |
|------|------|------|
| 戻り値が `Promise<User>` | `AppResultAsync<T>` を使う | `AppResultAsync<User>` に変更 |
| `try/catch` で既知エラーを処理 | 既知エラーは `Result` でモデリング | `fromPromise` 内でマッピング |
| 生 `fetch` を直接使用 | 外部境界は `fromFetch` 等のヘルパーで変換 | `fromFetch` ヘルパーを導入 |
| エラーが汎用 `Error` | `AppError` 判別共用体を使う | `kind` フィールドで識別 |
| `console.error` + 再スロー | `Result` で表現すれば不要 | `match` で適切にハンドリング |
