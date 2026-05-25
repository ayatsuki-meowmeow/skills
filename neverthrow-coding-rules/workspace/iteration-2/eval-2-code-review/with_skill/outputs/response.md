# コードレビュー

## 対象コード

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

## 規約違反の指摘

このコードは neverthrow コーディング規約に対して複数の違反があります。

---

### 違反1: 返り値が `Promise<User>` になっている（最重要）

**問題**: 呼び出し側がリカバリできるエラー（HTTP エラー等）が含まれているにもかかわらず、返り値が `Promise<User>` のため、エラーの発生可能性が型から読み取れない。

**規約**: 外部 API コールのような「既知のエラーが発生し得る処理」は `AppResultAsync<T>` を返すべき。

```typescript
// NG
async function getUser(id: string): Promise<User>

// OK
function getUser(id: string): AppResultAsync<User>
```

---

### 違反2: `try/catch` で既知のエラーを握り潰し、再 `throw` している

**問題**: `catch` ブロックで `console.error(e)` を呼んでから `throw e` で再スローしている。既知のエラー（`!res.ok` のケース）も未知のエラーも同一の `catch` で処理されており、エラーの種別が型として表現されていない。

**規約**: 「やってはいけないこと」として、`try/catch` で既知のエラーを握り潰すことは禁止されている。

---

### 違反3: `!res.ok` を `throw` で処理している（known error を throw している）

**問題**: `if (!res.ok) throw new Error('fetch failed')` は、HTTP エラーという「既知のエラー」を `throw` で表現している。これは errMapper でキャッチさせるパターンと同様に禁止されている。

**規約**: 既知の失敗（HTTP ステータスコードのエラー等）は `andThen` + `err()` で Result に変換する。

---

### 違反4: `AppError` 型を使っていない

**問題**: `new Error('fetch failed')` という汎用エラーを使っており、判別共用体の `AppError` 型（`{ kind: 'not_found' }` 等）でエラーをモデリングしていない。

**規約**: エラー型は判別共用体で定義し、`AppError` を使う。

---

## 修正後のコード例

```typescript
import { ResultAsync, err } from 'neverthrow'

type AppError =
  | { kind: 'not_found'; resource: string }
  | { kind: 'unknown'; cause: unknown }

type AppResultAsync<T> = ResultAsync<T, AppError>

function getUser(id: string): AppResultAsync<User> {
  return ResultAsync.fromPromise(
    fetch(`/api/users/${id}`),
    (e): AppError => ({ kind: 'unknown', cause: e }), // ネットワーク断のみ
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
}
```

### 修正のポイント

1. **返り値を `AppResultAsync<User>` に変更** — エラーの可能性が型で明示される
2. **`try/catch` を廃止** — `ResultAsync.fromPromise` で unknown error（ネットワーク断）を処理
3. **known error（`!res.ok`）は `andThen` + `err()`** — `throw` を使わない
4. **`AppError` 判別共用体を使用** — `kind` による網羅チェックが可能になる
5. **`console.error` を除去** — エラーのロギングは呼び出し側の責務にする（または専用のエラーハンドラーで行う）

---

## 呼び出し側での使い方

```typescript
getUser(id).match(
  (user) => {
    // 成功
    console.log(user)
  },
  (err) => {
    switch (err.kind) {
      case 'not_found':
        return showNotFoundMessage(err.resource)
      case 'unknown':
        return showGenericError(err.cause)
      // 漏れがあればコンパイルエラーになる
    }
  },
)
```

---

## まとめ

| 項目 | 元のコード | 修正後 |
|------|-----------|--------|
| 返り値の型 | `Promise<User>`（エラー情報なし） | `AppResultAsync<User>` |
| エラー表現 | `throw new Error(...)` | `err({ kind: '...' })` |
| unknown error の処理 | `catch (e) { throw e }` | `fromPromise` の errMapper |
| known error の処理 | `throw new Error('fetch failed')` | `andThen` + `err()` |
| エラー型 | `Error`（汎用） | `AppError`（判別共用体） |
