---
name: neverthrow-coding-rules
description: |
  neverthrow を使ったプロジェクトで TypeScript コードを書くときに必ず参照すべきコーディング規約スキル。
  fetch・DB・バリデーション等の実装タスクや TypeScript コードレビューで、このスキルのルールを強制する。

  このスキルを必ず使うべきケース（積極的にトリガーすること）:
  - TypeScript で fetch / API コール / DB アクセス / バリデーション関数を実装するよう依頼されたとき
  - try/catch・async/await・Promise を含む TypeScript コードを書くとき
  - TypeScript / neverthrow のコードレビューを依頼されたとき
  - "Result型" "ResultAsync" "neverthrow" "エラーハンドリング" が含まれる TypeScript 実装タスク
  - エラーを返す関数・サービス層・リポジトリ層を TypeScript で書くとき

  SKIP:
  - FE presentation 層（React コンポーネント・hooks・TanStack Query の queryFn 等）
  - neverthrow の初期導入・セットアップ（neverthrow-setup スキルが担当）
  - コーディング以外のタスク（設計相談・調査のみ）
  - JavaScript のみのファイル（.js / .jsx）
---

# neverthrow コーディング規約

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

```typescript
import { Result, ResultAsync } from 'neverthrow'

type AppResult<T> = Result<T, AppError>
type AppResultAsync<T> = ResultAsync<T, AppError>
```

関数の返り値には必ず `AppResult<T>` / `AppResultAsync<T>` を使う。`Result<T, AppError>` と直接書かない。

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
const fromFetch = <T>(url: RequestInfo): AppResultAsync<T> =>
  ResultAsync.fromPromise(
    fetch(url),
    (e): AppError => ({ kind: 'unknown', cause: e }), // ネットワーク断のみ
  ).andThen((res) => {
    if (res.status === 404)
      return err<T, AppError>({ kind: 'not_found', resource: String(url) })
    if (!res.ok)
      return err<T, AppError>({ kind: 'unknown', cause: res })
    return ResultAsync.fromPromise(
      res.json() as Promise<T>,
      (e): AppError => ({ kind: 'unknown', cause: e }),
    )
  })

// DB（Prisma 等）— DB エラーはすべて unknown なので errMapper のみでよい
const fromDb = <T>(promise: Promise<T>): AppResultAsync<T> =>
  ResultAsync.fromPromise(promise, (e): AppError => ({ kind: 'db', cause: e }))
```

### 原則

- `fromPromise` errMapper → **unknown error のみ**（reject / 例外 / ネットワーク断）
- HTTP ステータスコードなど **既知の失敗** → `andThen` + `err()` で Result に変換
- `throw` を意図的に使って errMapper で catch するパターンは禁止

## エラーハンドリングのパターン

### match で分岐（推奨）

```typescript
result.match(
  (data) => { /* 成功 */ },
  (err) => {
    switch (err.kind) {
      case 'validation': return ...
      case 'not_found':  return ...
      case 'db':         return ...
      case 'unknown':    return ...
      // 漏れがあればコンパイルエラー
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
- `Result<T, AppError>` と直接書く（エイリアスを使う）
- presentation 層で neverthrow を使う
- `_unsafeUnwrap()` を本番コードで使う（テスト専用）
