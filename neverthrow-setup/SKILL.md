---
name: neverthrow-setup
description: |
  Use this skill when a user wants to introduce or bootstrap neverthrow into a TypeScript project.
  Key triggers: asking to add/install/setup neverthrow, wanting to create AppError discriminated
  union types from scratch, creating AppResult/AppResultAsync type aliases, building fromFetch or
  fromDb helper functions, or configuring eslint-plugin-neverthrow. Also trigger when the user
  asks "where do I start with neverthrow" or describes their stack (e.g., uses Prisma, fetch) and
  wants neverthrow wired in. This is a first-time setup skill — skip only when neverthrow is
  already fully configured and the user wants help implementing specific features or reviewing
  existing code (use neverthrow-coding-rules skill instead).
---

# neverthrow セットアップ

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

```typescript
// src/types/result.ts（または errors.ts と同じファイルでも可）
import { Result, ResultAsync } from 'neverthrow'
import type { AppError } from './errors'

export type AppResult<T> = Result<T, AppError>
export type AppResultAsync<T> = ResultAsync<T, AppError>
```

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
// ✅ 正しいパターン
ResultAsync.fromPromise(
  fetch(url),
  (e): AppError => ({ kind: 'unknown', cause: e }), // ここはネットワーク断のみ
).andThen((res) => {
  // 既知エラーは andThen の中で err() として返す
  if (res.status === 401) return err<T, AppError>({ kind: 'unauthorized' })
  return ResultAsync.fromPromise(res.json() as Promise<T>, (e): AppError => ({ kind: 'unknown', cause: e }))
})
```

### 実装例

```typescript
// src/lib/result-helpers.ts

import { ResultAsync, err } from 'neverthrow'
import type { AppError } from '../types/errors'

// fetch 用
export const fromFetch = <T>(
  request: RequestInfo | URL,
  init?: RequestInit,
): AppResultAsync<T> =>
  ResultAsync.fromPromise(
    fetch(request, init),
    (e): AppError => ({ kind: 'unknown', cause: e }), // ネットワーク断のみ
  ).andThen((res) => {
    if (res.status === 404)
      return err<T, AppError>({ kind: 'not_found', resource: String(request) })
    if (res.status === 401)
      return err<T, AppError>({ kind: 'unauthorized' })
    if (!res.ok)
      return err<T, AppError>({ kind: 'unknown', cause: res })
    return ResultAsync.fromPromise(
      res.json() as Promise<T>,
      (e): AppError => ({ kind: 'unknown', cause: e }),
    )
  })

// Prisma 用（使用する場合）
// DB エラーはすべて unknown なので errMapper のみでよい
export const fromDb = <T>(promise: Promise<T>): AppResultAsync<T> =>
  ResultAsync.fromPromise(promise, (e): AppError => ({ kind: 'db', cause: e }))
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
- 新たな外部境界が増えたら `fromXxx` ヘルパーを1つ追加する
- presentation 層（React コンポーネント・hooks 等）では neverthrow は使わず TanStack Query 等に委譲する
