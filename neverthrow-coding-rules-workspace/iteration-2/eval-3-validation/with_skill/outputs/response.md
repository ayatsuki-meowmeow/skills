# バリデーション関数の実装（neverthrow コーディング規約準拠）

neverthrow のコーディング規約に従い、`Result` 型を使ってバリデーション関数を実装します。

## 設計方針

- バリデーション失敗は**既知のエラー**なので `Result` 型でモデリングする
- `AppError` は判別共用体で定義し、クラス継承は使わない
- 返り値は `AppResult<T>` エイリアスを使う（`Result<T, AppError>` と直接書かない）
- `try/catch` は使わない（バリデーションに例外は不要）

## 実装コード

```typescript
import { ok, err, Result } from 'neverthrow'

// AppError 型（判別共用体）
type AppError =
  | { kind: 'validation'; message: string }
  | { kind: 'not_found'; resource: string }
  | { kind: 'unauthorized' }
  | { kind: 'db'; cause: unknown }
  | { kind: 'unknown'; cause: unknown }

// 型エイリアス
type AppResult<T> = Result<T, AppError>

// バリデーション対象の型
type UserInput = {
  name: string
  email: string
}

// --- 個別バリデーション関数 ---

function validateName(name: string): AppResult<string> {
  if (name.length < 1) {
    return err({ kind: 'validation', message: '名前は1文字以上で入力してください' })
  }
  return ok(name)
}

function validateEmail(email: string): AppResult<string> {
  if (!email.includes('@')) {
    return err({ kind: 'validation', message: 'メールアドレスには @ を含めてください' })
  }
  return ok(email)
}

// --- メインのバリデーション関数 ---

function validateUserInput(name: string, email: string): AppResult<UserInput> {
  return validateName(name).andThen((validName) =>
    validateEmail(email).map((validEmail) => ({
      name: validName,
      email: validEmail,
    }))
  )
}

// --- 使用例 ---

const result = validateUserInput('Alice', 'alice@example.com')

result.match(
  (data) => {
    console.log('バリデーション成功:', data)
    // => { name: 'Alice', email: 'alice@example.com' }
  },
  (error) => {
    switch (error.kind) {
      case 'validation':
        console.error('バリデーションエラー:', error.message)
        break
      case 'not_found':
        console.error('リソースが見つかりません:', error.resource)
        break
      case 'unauthorized':
        console.error('認証エラー')
        break
      case 'db':
        console.error('DBエラー:', error.cause)
        break
      case 'unknown':
        console.error('不明なエラー:', error.cause)
        break
      // switch の網羅チェックがコンパイラで保証される
    }
  },
)

// 失敗例1: 名前が空
validateUserInput('', 'alice@example.com').match(
  (data) => console.log('成功:', data),
  (error) => {
    if (error.kind === 'validation') {
      console.error(error.message) // => '名前は1文字以上で入力してください'
    }
  },
)

// 失敗例2: メールに @ がない
validateUserInput('Alice', 'invalid-email').match(
  (data) => console.log('成功:', data),
  (error) => {
    if (error.kind === 'validation') {
      console.error(error.message) // => 'メールアドレスには @ を含めてください'
    }
  },
)
```

## ポイント解説

### `Result` 型でエラーをモデリングする理由

バリデーション失敗は**呼び出し側がリカバリできる既知のエラー**です。`throw` ではなく `Result` 型に包むことで、関数の型シグネチャから「この関数は失敗する可能性がある」ことが伝わり、呼び出し側が必ずエラーを処理するようコンパイラが強制します。

### `andThen` + `map` でチェーン処理

`validateName` が成功した場合のみ `validateEmail` を実行するよう `andThen` でつなぎます。最初のバリデーションエラーで処理が短絡するため、不要な検査を省けます。複数フィールドを一括で収集したい場合は `combine` の利用も検討してください。

### `AppError` を判別共用体にする理由

`switch (error.kind)` による網羅チェックがコンパイラで保証されます。クラス継承（`class ValidationError extends Error`）では exhaustive check が効きません。

### `_unsafeUnwrap()` は使わない

本番コードでは `_unsafeUnwrap()` を使わず、必ず `.match()` または `.andThen()` / `.mapErr()` で両ブランチを処理します。
