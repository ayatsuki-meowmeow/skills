# TypeScript コードレビュー

## レビュー対象

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

## 問題点と改善案

### 1. エラーハンドリングが不明確

**問題:**
`catch (e)` のブロックで `e` の型が `unknown` であるにもかかわらず、型チェックなしで再スローしている。また、エラーメッセージ `'fetch failed'` が曖昧で、デバッグ時に有用な情報（ステータスコード等）が含まれていない。

**改善案:**
```typescript
if (!res.ok) throw new Error(`fetch failed: ${res.status} ${res.statusText}`);
```

---

### 2. `res.json()` の戻り値が `any` 型

**問題:**
`res.json()` は `Promise<any>` を返すため、`User` 型へのキャストが暗黙的に行われる。実際のレスポンスが `User` の形状を持つ保証がなく、型安全性が損なわれる。

**改善案:**
zod などのバリデーションライブラリでレスポンスの形状を検証する。

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  // ...
});

async function getUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error(`fetch failed: ${res.status} ${res.statusText}`);
  const data = await res.json();
  return UserSchema.parse(data);
}
```

---

### 3. `catch` ブロックが無意味なラッパーになっている

**問題:**
`catch (e)` ブロックは `console.error(e)` を呼び出してから `throw e` しているだけで、エラーを変換・処理しておらず、実質的に何もしていない。ログ出力の責務を呼び出し元に委ねるか、エラーをラップして追加情報を付与すべき。

**改善案 A（try-catch を削除してシンプルにする）:**
```typescript
async function getUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error(`fetch failed: ${res.status} ${res.statusText}`);
  return res.json() as Promise<User>;
}
```

**改善案 B（エラーをラップして追加情報を付与する）:**
```typescript
async function getUser(id: string): Promise<User> {
  try {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) throw new Error(`fetch failed: ${res.status} ${res.statusText}`);
    return res.json() as Promise<User>;
  } catch (e) {
    throw new Error(`getUser(${id}) failed`, { cause: e });
  }
}
```

---

### 4. Result 型による明示的なエラー伝播（推奨パターン）

**問題:**
例外ベースのエラーハンドリングは、関数のシグネチャからエラーの可能性が読み取れず、呼び出し元がエラーハンドリングを忘れやすい。

**改善案（neverthrow を使用）:**
`neverthrow` の `Result` 型を使うことで、エラーの可能性を型で明示できる。

```typescript
import { Result, ok, err } from 'neverthrow';

async function getUser(id: string): Promise<Result<User, Error>> {
  try {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) return err(new Error(`fetch failed: ${res.status} ${res.statusText}`));
    const data = await res.json();
    return ok(UserSchema.parse(data));
  } catch (e) {
    return err(e instanceof Error ? e : new Error(String(e)));
  }
}
```

---

## まとめ

| 問題 | 優先度 |
|------|--------|
| エラーメッセージが不明確 | 中 |
| `res.json()` の型安全性がない | 高 |
| `catch` ブロックが無意味なラッパー | 中 |
| 例外ベースのエラーハンドリング | 低〜中（プロジェクト方針次第） |

最低限、`res.json()` のレスポンスをバリデーションし、エラーメッセージにステータスコードを含めることを推奨する。
