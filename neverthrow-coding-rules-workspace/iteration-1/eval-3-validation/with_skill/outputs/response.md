# バリデーション関数の実装

## 規約の適用

このタスクはバリデーション失敗（既知のエラー）を扱うため、スキル規約に従い `Result` を使ってモデリングします。

- バリデーション失敗 → `AppError` の `kind: 'validation'` で表現
- 返り値は `AppResult<T>` 型エイリアスを使用
- `throw` や `try/catch` は使わない

## 実装

```typescript
import { ok, err } from 'neverthrow'
import type { Result } from 'neverthrow'

// ---------- AppError 判別共用体 ----------
type AppError =
  | { kind: 'validation'; message: string }
  | { kind: 'not_found'; resource: string }
  | { kind: 'unauthorized' }
  | { kind: 'db'; cause: unknown }
  | { kind: 'unknown'; cause: unknown }

// ---------- 型エイリアス ----------
type AppResult<T> = Result<T, AppError>

// ---------- バリデーション対象の型 ----------
type UserInput = {
  name: string
  email: string
}

// ---------- バリデーション関数 ----------

/** 名前を検証する（1文字以上） */
const validateName = (name: string): AppResult<string> => {
  if (name.length === 0) {
    return err({ kind: 'validation', message: '名前は1文字以上で入力してください' })
  }
  return ok(name)
}

/** メールアドレスを検証する（@ を含む） */
const validateEmail = (email: string): AppResult<string> => {
  if (!email.includes('@')) {
    return err({ kind: 'validation', message: 'メールアドレスに @ が含まれていません' })
  }
  return ok(email)
}

/** 名前とメールをまとめて検証する */
const validateUserInput = (input: UserInput): AppResult<UserInput> =>
  validateName(input.name).andThen((name) =>
    validateEmail(input.email).map((email) => ({ name, email }))
  )

// ---------- 使用例 ----------

validateUserInput({ name: 'Alice', email: 'alice@example.com' }).match(
  (data) => {
    console.log('OK:', data)
  },
  (err) => {
    switch (err.kind) {
      case 'validation':
        console.error('バリデーションエラー:', err.message)
        break
      case 'not_found':
        console.error('リソースが見つかりません:', err.resource)
        break
      case 'unauthorized':
        console.error('認証エラー')
        break
      case 'db':
        console.error('DBエラー:', err.cause)
        break
      case 'unknown':
        console.error('不明なエラー:', err.cause)
        break
      // switch が網羅的でなければコンパイルエラーになる
    }
  },
)
```

## 説明

### ポイント

| ポイント | 内容 |
|---------|------|
| エラー分類 | バリデーション失敗は「既知のエラー」なので `Result` でモデリング |
| AppError | 判別共用体で定義。`kind: 'validation'` にエラーメッセージを持たせる |
| 型エイリアス | `Result<T, AppError>` とは直接書かず、`AppResult<T>` を使用 |
| チェーン | `andThen` で名前 → メールの順に検証をチェーン。最初に失敗した時点で短絡 |
| exhaustive check | `match` 内の `switch(err.kind)` で全 `kind` を網羅。漏れはコンパイルエラー |

### バリデーションの流れ

1. `validateName` で名前が空でないか確認 → 失敗なら即 `err` を返す
2. `andThen` で `validateEmail` に渡し、メールに `@` が含まれるか確認
3. 両方成功すれば `ok({ name, email })` を返す

### やっていないこと（規約違反の回避）

- `try/catch` でバリデーション失敗を握り潰していない
- `class ValidationError extends Error` のようなクラス継承は使っていない
- `Result<T, AppError>` と直接書かず `AppResult<T>` エイリアスを使っている
- `_unsafeUnwrap()` を使っていない
