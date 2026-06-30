# neverthrow コーディング規約 ルール本体

## エラーの分類

| エラー種別 | 対応 |
|-----------|------|
| 既知のエラー（バリデーション失敗・400系・not_found 等） | `Result` / `ResultAsync` でモデリング |
| 未知のエラー（バグ・OOM・接続断等） | `throw` のまま。アプリケーション境界でキャッチ |

呼び出し側がリカバリできるエラーを `Result` に入れる。バグ起因や回復不能なものは `throw` で良い。

## AppError 型

エラー型は**判別共用体**で定義する。クラス継承は使わない（exhaustive check が効かなくなるため）。

```typescript
type AppError =
  | { kind: 'validation'; message: string }
  | { kind: 'not_found'; resource: string }
  | { kind: 'unauthorized' }
  | { kind: 'db'; cause: unknown }
  | { kind: 'unknown'; cause: unknown }  // 未知エラーのラップ先
```

`kind` で識別することで、`switch` 文の網羅チェックがコンパイラで保証される。

## 型エイリアス

エラー型 `E` は**必須**。デフォルトを置かないことで、省略するとコンパイルエラーになる＝エラー型の明示が型レベルのガードレールになる。

```typescript
import { Result, ResultAsync } from 'neverthrow'

// E は必須（デフォルトなし）
type AppResult<T, E extends AppError> = Result<T, E>
type AppResultAsync<T, E extends AppError> = ResultAsync<T, E>

// AppError から kind の部分集合を取り出すヘルパー
type ErrorOf<K extends AppError['kind']> = Extract<AppError, { kind: K }>
```

関数の返り値には必ずエイリアスを使い、**`E` には実際に返し得る `kind` の部分集合だけを明示**する。

```typescript
// ✅ 返し得るエラーがシグネチャに現れる。'db' を返すとコンパイルエラー
const fetchUser = (id: string): AppResultAsync<User, ErrorOf<'not_found' | 'unauthorized' | 'unknown'>> => ...

// ❌ E を省略 → コンパイルエラー（ガードレール）
const fetchUser = (id: string): AppResultAsync<User> => ...

// ❌ 実際は一部しか返さないのに AppError 全体を渡す → 精度が無に帰す
const fetchUser = (id: string): AppResultAsync<User, AppError> => ...
```

このガードレールが守るもの：

- **読み手（実装者・AIエージェント）**: シグネチャだけでその関数が返すエラーが分かり、実装を読む必要がない
- **書き手**: 想定外の `kind` を返すコードはコンパイルが通らない

## 外部境界での変換

### fromPromise の errMapper は unknown error 専用

`ResultAsync.fromPromise` の errMapper（第2引数）は **Promise が reject した場合（ネットワーク断・例外等）** のみを担当する。HTTP 404 のような「既知のエラー」を errMapper で処理してはならない。

❌ 禁止パターン：known error を throw して errMapper でキャッチする

```typescript
// NG: 404 を throw してシグナルを送り、errMapper で変換している
ResultAsync.fromPromise(
  fetch(url).then(res => {
    if (res.status === 404) throw { _tag: 'not_found' }  // known error なのに throw
    return res.json()
  }),
  (e): AppError =>
    (e as any)._tag === 'not_found'
      ? { kind: 'not_found', resource: url }
      : { kind: 'unknown', cause: e },
)
```

✅ 正しいパターン：known error は `andThen` + `err()` で表現する

```typescript
// OK: fromPromise は unknown error のみ。known error は andThen で err() に
// E はこのヘルパーが実際に返し得る kind だけに絞る
type FetchError = ErrorOf<'not_found' | 'unknown'>

const fromFetch = <T>(url: RequestInfo): AppResultAsync<T, FetchError> =>
  ResultAsync.fromPromise(
    fetch(url),
    (e): FetchError => ({ kind: 'unknown', cause: e }), // ネットワーク断のみ
  ).andThen((res) => {
    if (res.status === 404)
      return err<T, FetchError>({ kind: 'not_found', resource: String(url) })
    if (!res.ok)
      return err<T, FetchError>({ kind: 'unknown', cause: res })
    return ResultAsync.fromPromise(
      res.json() as Promise<T>,
      (e): FetchError => ({ kind: 'unknown', cause: e }),
    )
  })

// DB（Prisma 等）— DB エラーのみ
const fromDb = <T>(promise: Promise<T>): AppResultAsync<T, ErrorOf<'db'>> =>
  ResultAsync.fromPromise(promise, (e): ErrorOf<'db'> => ({ kind: 'db', cause: e }))
```

### 原則

- `fromPromise` errMapper → **unknown error のみ**（reject / 例外 / ネットワーク断）
- HTTP ステータスコードなど **既知の失敗** → `andThen` + `err()` で Result に変換
- `throw` を意図的に使って errMapper で catch するパターンは禁止

## エラーハンドリングのパターン

### match で分岐（推奨）

`E` を絞っているので、`switch` はその関数が**実際に返し得る `kind` だけ**を扱えばよい。E に無い `kind` は型に存在しないため、書こうとすると到達不能でエラーになる。

```typescript
// 戻り値が AppResultAsync<User, ErrorOf<'not_found' | 'unauthorized' | 'unknown'>> の場合
result.match(
  (data) => { /* 成功 */ },
  (err) => {
    switch (err.kind) {
      case 'not_found':    return ...
      case 'unauthorized': return ...
      case 'unknown':      return ...
      // 'db' / 'validation' はそもそも来ない。漏れがあればコンパイルエラー
    }
  },
)
```

### チェーン処理

```typescript
fetchUser(id)
  .andThen(validateUser)
  .map(transformUser)
  .match(onSuccess, onError)
```

## レイヤー分担

```
BE / FE domain 層   →  neverthrow（Result で成否をモデリング）
FE presentation 層  →  TanStack Query 等（loading / data / error の3状態管理）
```

presentation 層（React コンポーネント・hooks）では neverthrow を使わない。
`queryFn` の中で neverthrow の結果を `match` で unwrap して TanStack Query に渡す。

```typescript
// presentation 層での境界
const { data, isLoading } = useQuery({
  queryFn: () =>
    fetchUser(id).match(
      (data) => data,
      (err) => { throw new Error(String(err.kind)) },
    ),
})
```

## やってはいけないこと

- `try/catch` で既知のエラーを握り潰す
- `fromPromise` の errMapper 内で known error（404 等）を処理する（errMapper は unknown error 専用）
- known error を `throw` して errMapper でキャッチするパターンを使う
- AppError をクラス継承で定義する（`class ValidationError extends Error`）
- `Result<T, E>` と直接書く（エイリアスを使う）
- エラー型 `E` を省略する（型エイリアスにデフォルトを持たせない＝省略はコンパイルエラー）
- 実際に返し得る範囲より広いユニオン（`AppError` 全体など）を `E` に渡す（精度が失われる）
- presentation 層で neverthrow を使う
- `_unsafeUnwrap()` を本番コードで使う（テスト専用）
