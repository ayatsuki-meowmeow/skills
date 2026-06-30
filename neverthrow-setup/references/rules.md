# neverthrow セットアップ手順

## 1. パッケージインストール

ユーザーの使用パッケージマネージャで `neverthrow` と `eslint-plugin-neverthrow` をインストールするよう案内する。

```
# npm
npm install neverthrow
npm install -D eslint-plugin-neverthrow

# pnpm
pnpm add neverthrow
pnpm add -D eslint-plugin-neverthrow

# yarn
yarn add neverthrow
yarn add -D eslint-plugin-neverthrow
```

## 2. AppError 型の定義

エラーは**判別共用体**で定義する。クラス継承は使わない（exhaustive check が効かなくなるため）。

プロジェクトのエラー種別をユーザーに確認し、それに合わせて生成する。最低限 `unknown` を末尾に含める。

```typescript
// src/types/errors.ts（パスはプロジェクト構造に合わせる）
export type AppError =
  | { kind: 'validation'; message: string }
  | { kind: 'not_found'; resource: string }
  | { kind: 'unauthorized' }
  | { kind: 'db'; cause: unknown }
  | { kind: 'unknown'; cause: unknown }
```

`kind` フィールドで識別することで、`match` 内の `switch` 文が網羅チェックになる。

## 3. 型エイリアスの定義

エラー型 `E` は**必ず明示**させる。デフォルト値を置かないことで「省略するとコンパイルエラー」となり、エラー型の明示が型レベルのガードレールになる。

```typescript
// src/types/result.ts（または errors.ts と同じファイルでも可）
import { Result, ResultAsync } from 'neverthrow'
import type { AppError } from './errors'

// E は必須。デフォルトを置かない＝省略不可（ガードレール）
export type AppResult<T, E extends AppError> = Result<T, E>
export type AppResultAsync<T, E extends AppError> = ResultAsync<T, E>

// AppError から kind の部分集合を取り出すヘルパー
export type ErrorOf<K extends AppError['kind']> = Extract<AppError, { kind: K }>
```

関数ごとに**実際に返し得る `kind` だけ**を `E` に指定する。これにより：

- シグネチャを見るだけで、その関数が返すエラー種別が分かる（実装を読まなくてよい）
- 想定外の `kind` を返すとコンパイルエラーになる（返すべきでないエラーの流出を型で防ぐ）

```typescript
// ✅ 返し得るのは not_found / unauthorized / unknown だけ、と契約が型に現れる
const fetchUser = (id: string): AppResultAsync<User, ErrorOf<'not_found' | 'unauthorized' | 'unknown'>> => ...

// ❌ E を省略 → コンパイルエラー（ガードレールが働く）
const fetchUser = (id: string): AppResultAsync<User> => ...
```

`E` に `AppError` 全体を渋々渡すのは精度を捨てる行為なので避ける。実際に返し得る部分集合だけを書く。

## 4. fromXxx ヘルパーの作成

外部境界（fetch、DB、外部 SDK 等）ごとに変換ヘルパーを1つ作る。neverthrow 自体をラップするのではなく、エラー変換のみを担う小さな関数。

ユーザーが使用する外部境界をヒアリングし、それに合わせて生成する。

### 重要：throw を使わない

`ResultAsync.fromPromise(promise, errMapper)` の `errMapper` は **予期しない例外（ネットワーク断・パースエラー等）専用**。HTTP 404 / 401 のような既知のエラーケースを `throw` で errMapper に流す実装は絶対に避ける。

**NG（throw を使ったアンチパターン）:**
```typescript
// ❌ やってはいけない
ResultAsync.fromPromise(
  fetch(url).then(res => {
    if (res.status === 401) throw { kind: 'unauthorized' }  // known error を throw している
    return res.json()
  }),
  (e): AppError =>
    e && typeof e === 'object' && 'kind' in e ? (e as AppError) : { kind: 'unknown', cause: e },
)
```

この実装が問題な理由：
- 既知エラー（HTTP ステータス）を例外として扱い、Result のセマンティクスを壊す
- errMapper が AppError かどうかを動的に判定しなければならず、型安全性が失われる
- `throw` が飛んだ場所とキャッチ場所が遠くなり、追跡が難しくなる

**OK（andThen を使った正しいパターン）:**
```typescript
// ✅ 正しいパターン（E は実際に返し得る kind だけに絞る）
type E = ErrorOf<'unauthorized' | 'unknown'>
ResultAsync.fromPromise(
  fetch(url),
  (e): E => ({ kind: 'unknown', cause: e }), // ここはネットワーク断のみ
).andThen((res) => {
  // 既知エラーは andThen の中で err() として返す
  if (res.status === 401) return err<T, E>({ kind: 'unauthorized' })
  return ResultAsync.fromPromise(res.json() as Promise<T>, (e): E => ({ kind: 'unknown', cause: e }))
})
```

### 実装例

ヘルパーの戻り値型も、そのヘルパーが**実際に返し得る `kind` だけ**を `E` に明示する。

```typescript
// src/lib/result-helpers.ts

import { ResultAsync, err } from 'neverthrow'
import type { AppResultAsync, ErrorOf } from '../types/result'

// fetch 用：返し得るのは not_found / unauthorized / unknown のみ
type FetchError = ErrorOf<'not_found' | 'unauthorized' | 'unknown'>

export const fromFetch = <T>(
  request: RequestInfo | URL,
  init?: RequestInit,
): AppResultAsync<T, FetchError> =>
  ResultAsync.fromPromise(
    fetch(request, init),
    (e): FetchError => ({ kind: 'unknown', cause: e }), // ネットワーク断のみ
  ).andThen((res) => {
    if (res.status === 404)
      return err<T, FetchError>({ kind: 'not_found', resource: String(request) })
    if (res.status === 401)
      return err<T, FetchError>({ kind: 'unauthorized' })
    if (!res.ok)
      return err<T, FetchError>({ kind: 'unknown', cause: res })
    return ResultAsync.fromPromise(
      res.json() as Promise<T>,
      (e): FetchError => ({ kind: 'unknown', cause: e }),
    )
  })

// Prisma 用（使用する場合）：DB エラーのみ
export const fromDb = <T>(promise: Promise<T>): AppResultAsync<T, ErrorOf<'db'>> =>
  ResultAsync.fromPromise(promise, (e): ErrorOf<'db'> => ({ kind: 'db', cause: e }))
```

## 5. eslint-plugin-neverthrow の設定

Result を `.match()` / `.unwrapOr()` 等でハンドリングせずに放置するとエラーにする。

```javascript
// eslint.config.js（Flat Config）
import neverthrow from 'eslint-plugin-neverthrow'

export default [
  {
    plugins: { neverthrow },
    rules: {
      'neverthrow/must-use-result': 'error',
    },
  },
]
```

```json
// .eslintrc.json（Legacy Config）
{
  "plugins": ["neverthrow"],
  "rules": {
    "neverthrow/must-use-result": "error"
  }
}
```

## セットアップ完了後

- エラー種別の追加・変更は `AppError` 型を修正するだけで、`switch` 文の網羅チェックが漏れを検出する
- 関数を書くときは戻り値の `E` に実際に返し得る `kind` だけを `ErrorOf<...>` で明示する（省略はコンパイルエラー）
- 新たな外部境界が増えたら `fromXxx` ヘルパーを1つ追加する
- presentation 層（React コンポーネント・hooks 等）では neverthrow は使わず TanStack Query 等に委譲する
