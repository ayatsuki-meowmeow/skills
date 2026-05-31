バリデーション失敗は「呼び出し側がリカバリできる既知のエラー」なので、例外を投げずに `Result` でモデリングします。同期処理なので `ResultAsync` ではなく `AppResult` を使い、エラー型 `E` はこの関数が実際に返し得る `'validation'` だけに絞ります。

```typescript
import { ok, err } from 'neverthrow'

type ValidatedInput = {
  name: string
  email: string
}

// この関数が返し得るエラーは validation のみ。E をそこに絞る
type ValidateError = ErrorOf<'validation'>

const validateInput = (
  name: string,
  email: string,
): AppResult<ValidatedInput, ValidateError> => {
  if (name.length < 1) {
    return err({ kind: 'validation', message: '名前は1文字以上で入力してください' })
  }

  if (!email.includes('@')) {
    return err({ kind: 'validation', message: 'メールアドレスには @ を含めてください' })
  }

  return ok({ name, email })
}
```

呼び出し側では `match` で成否を分岐します。`E` を `ValidateError` に絞っているので、`switch` は実際に返し得る `'validation'` だけを扱えばよく、他の `kind` を書こうとすると型エラーになります。

```typescript
validateInput(name, email).match(
  (input) => {
    // input.name / input.email を使った後続処理
  },
  (e) => {
    switch (e.kind) {
      case 'validation':
        return e.message // バリデーションメッセージをそのまま利用
      // 'not_found' / 'db' などはこの関数からは来ない。
      // 漏れがあればコンパイルエラーになる
    }
  },
)
```

ポイント:

- バリデーション失敗は既知のエラーなので `throw` せず `err()` で `Result` に表現しています。
- 戻り値は素の `Result<T, E>` ではなく型エイリアス `AppResult` を使い、`E` は実際に返す `ErrorOf<'validation'>` だけに明示しています。これによりシグネチャだけでこの関数が validation エラーしか返さないことが分かります。
- 複数フィールドを `andThen` でチェーンしたい場合も、各バリデータが `AppResult<_, ValidateError>` を返すようにすれば同じ方針で合成できます。
