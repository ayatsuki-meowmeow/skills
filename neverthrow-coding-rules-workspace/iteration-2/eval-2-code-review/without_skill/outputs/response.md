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

---

## 指摘事項

### 1. レスポンスの型安全性がない

**重要度: 高**

`res.json()` の戻り値は `Promise<any>` であり、`User` 型へのキャストは行われていない。実際のレスポンスが `User` の形状を満たさない場合でも TypeScript はエラーを出さない。

```typescript
// 問題: 型の保証がない
return await res.json(); // as User の暗黙的キャスト
```

**改善案:** `zod` などのバリデーションライブラリでレスポンスをパースする。

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  // ...
});

const data = UserSchema.parse(await res.json());
return data;
```

---

### 2. エラーメッセージが不十分

**重要度: 中**

`throw new Error('fetch failed')` はステータスコードや URL などのコンテキスト情報を含まない。デバッグ時に原因特定が困難になる。

**改善案:**

```typescript
if (!res.ok) {
  throw new Error(`fetch failed: ${res.status} ${res.statusText} (GET /api/users/${id})`);
}
```

---

### 3. catch ブロックが再スローするだけで意味が薄い

**重要度: 低〜中**

`console.error(e)` してから `throw e` するだけのパターンは、ログが重複したり、呼び出し元でも catch される場合に二重ログになりやすい。エラーハンドリングの責務を整理すべき。

**改善案:**
- ログは呼び出し元で一元管理するか、あるいはこの関数内でラップして再スローする。
- エラーをそのまま再スローするだけなら `try/catch` 自体を省略できる。

```typescript
// シンプルに try/catch を省略する場合
async function getUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) {
    throw new Error(`fetch failed: ${res.status} ${res.statusText}`);
  }
  return await res.json();
}
```

---

### 4. `e` の型が `unknown`（TypeScript 4.0+）

**重要度: 低**

TypeScript 4.0 以降、`catch` の `e` は `unknown` 型になった。`console.error(e)` は問題なく動作するが、`e` を `Error` として扱う場合は型ガードが必要。

```typescript
catch (e) {
  if (e instanceof Error) {
    console.error(e.message);
  } else {
    console.error(e);
  }
  throw e;
}
```

---

### 5. ネットワークエラーとHTTPエラーが区別されていない

**重要度: 中**

`fetch` がネットワーク障害でスローする例外と、HTTPステータスが非 2xx の場合で `throw` するケースが同じ `catch` で処理されている。呼び出し元でエラーの種別を判断できないため、リトライ戦略などを実装しにくい。

**改善案:** カスタムエラークラスを定義して区別する。

```typescript
class HttpError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'HttpError';
  }
}
```

---

## まとめ

| # | 指摘内容 | 重要度 |
|---|----------|--------|
| 1 | レスポンスの型バリデーションがない | 高 |
| 2 | エラーメッセージにコンテキストがない | 中 |
| 3 | catch ブロックの再スローが冗長 | 中 |
| 4 | `e` の型が `unknown` への対応漏れ | 低 |
| 5 | ネットワークエラーとHTTPエラーの区別がない | 中 |

最も優先すべきはレスポンスの型バリデーション（指摘1）で、ランタイムの型安全性を担保するために `zod` などの導入を検討してください。
