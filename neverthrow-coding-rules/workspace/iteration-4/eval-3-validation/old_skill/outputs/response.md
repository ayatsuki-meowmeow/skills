名前とメールのバリデーション関数を neverthrow を使って実装します。

## 設計方針

バリデーション失敗は「呼び出し側がリカバリできる既知のエラー」なので、`throw` ではなく `Result` でモデリングします。エラー型は判別共用体の `AppError` で定義し、`kind: 'validation'` を使います。同期処理なので返り値は `AppResult<T>` を使います。

## 実装

```typescript
import { Result, ok, err } from 'neverthrow'

// --- エラー型（判別共用体）---
type AppError =
  | { kind: 'validation'; message: string }
  | { kind: 'not_found'; resource: string }
  | { kind: 'unauthorized' }
  | { kind: 'db'; cause: unknown }
  | { kind: 'unknown'; cause: unknown }

// --- 型エイリアス ---
type AppResult<T> = Result<T, AppError>

// --- バリデーション対象のドメイン型 ---
type ValidatedUser = {
  name: string
  email: string
}

// --- 各フィールドのバリデーション ---
const validateName = (name: string): AppResult<string> => {
  if (name.length < 1) {
    return err({ kind: 'validation', message: '名前は1文字以上で入力してください' })
  }
  return ok(name)
}

const validateEmail = (email: string): AppResult<string> => {
  if (!email.includes('@')) {
    return err({ kind: 'validation', message: 'メールアドレスは@を含む必要があります' })
  }
  return ok(email)
}

// --- 合成したバリデーション関数 ---
const validateUser = (name: string, email: string): AppResult<ValidatedUser> =>
  validateName(name).andThen((validName) =>
    validateEmail(email).map((validEmail) => ({
      name: validName,
      email: validEmail,
    })),
  )
```

## 使い方

成功・失敗の分岐は `match` で行います。`err.kind` を `switch` で網羅すると、ケースの漏れがコンパイラで検出されます。

```typescript
validateUser('Alice', 'alice@example.com').match(
  (user) => {
    console.log('バリデーション成功:', user)
  },
  (error) => {
    switch (error.kind) {
      case 'validation':
        console.error('入力エラー:', error.message)
        break
      case 'not_found':
        console.error('見つかりません:', error.resource)
        break
      case 'unauthorized':
        console.error('認可エラー')
        break
      case 'db':
        console.error('DBエラー:', error.cause)
        break
      case 'unknown':
        console.error('不明なエラー:', error.cause)
        break
      // 漏れがあればコンパイルエラー
    }
  },
)
```

## ポイント

- バリデーション失敗は既知のエラーなので `throw` せず `Result` で返しています。
- エラー型はクラス継承ではなく判別共用体（`kind` フィールド）で定義しているため、`switch` の網羅チェックがコンパイラで保証されます。
- 返り値は `Result<T, AppError>` と直接書かず、型エイリアス `AppResult<T>` を使っています。
- `validateName` → `validateEmail` を `andThen` でチェーンしているため、名前が不正なら最初のエラーを返し、メールのバリデーションには進みません（早期リターン）。
- エラーメッセージは `match` の失敗ハンドラ（または `mapErr` 等）で取り出せます。本番コードで `_unsafeUnwrap()` は使いません。
