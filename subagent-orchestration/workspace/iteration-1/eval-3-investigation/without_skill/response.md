## プラン

Next.js プロジェクトの認証周りの実装を調査するタスクなので、私（メイン CC）は指揮に徹し、調査系サブエージェント 1 台を起動して並行に動かします。まずリポジトリ全体の構造を把握してもらい、`app/` または `pages/` の route handler、`middleware.ts`、`lib/auth/` 系、NextAuth / Auth.js / Clerk / Supabase Auth などの認証ライブラリ利用箇所、セッション管理、Cookie / JWT の扱い、RBAC 相当のガード実装、環境変数の使われ方までを一通り洗い出す想定です。調査結果を踏まえてリファクタしやすいポイント（重複しているガード、Server Component と Client Component の境界での session 取得の散らばり、middleware と route handler の責務重複、型が曖昧な session オブジェクトなど）を指摘してもらいます。サブエージェントは調査専任なので model は sonnet で十分、コード編集は禁止で読み取りのみに限定します。返ってきた結果は私がユーザーにそのまま構造化して報告し、リファクタ着手前に方針をユーザーに確認するフローにします。実装や設計判断はまだ行わず、あくまで現状把握と改善候補の列挙までに留めます。

委譲プロンプト本文（調査エージェント向け）:

> あなたは Next.js プロジェクトの認証実装を読み解く調査エージェントです。コードの編集は禁止、Read / Grep / Glob / Bash（read-only コマンドのみ）で調査してください。
> 
> 目的: 現状の認証実装を把握し、リファクタしやすいポイントを列挙する。設計や実装の判断はしないこと（判断はユーザーが行う）。
> 
> 調査観点:
> 1. どの認証方式・ライブラリを使っているか（NextAuth/Auth.js, Clerk, Supabase, 自前 JWT, Cookie session など）。`package.json` を確認。
> 2. エントリポイント: `middleware.ts` / `src/middleware.ts`, `app/api/auth/**`, `pages/api/auth/**` の役割分担。
> 3. セッション取得の実装: Server Component / Route Handler / Client Component それぞれで session をどう取得しているか、重複や薄いラッパーはあるか。
> 4. 認可（ガード）: ロール判定・ページ単位のガード・API 単位のガードがどこに散らばっているか。
> 5. 型の扱い: session / user の型定義、`any` や `as` の混入。
> 6. Cookie / トークンの扱い、環境変数キー名（値は絶対に読まない・出力しない。`.env`, `.env.*`, `.envrc` は禁止）。
> 7. テストの有無。
> 
> 出力フォーマット:
> - 現状サマリ（採用技術、ファイル構成の骨子）
> - 認証・認可フロー（ログイン、セッション検証、ログアウト）を箇条書きで
> - リファクタしやすいポイント Top 5〜8（該当ファイル:行、なぜ問題か、想定される整理方針の候補、影響範囲の大小）
> 
> 自己申告:
> - あなたのコンテキスト使用率（概算 %）と、途中で不足した情報があれば「未確認: 〜」として明示。
> 
> エスカレーション境界:
> - 仕様判断・技術選定・破壊的変更の是非はあなたの担当外。判断が必要な論点は「ユーザー確認事項」として列挙するに留めること。

```json
{
  "would_delegate": true,
  "delegate_count": 1,
  "parallel_dispatch": false,
  "delegations": [
    {
      "role_type": "調査",
      "model": "sonnet",
      "prompt_mentions_design_md": false,
      "prompt_mentions_impl_md": false,
      "prompt_mentions_context_self_report": true,
      "prompt_mentions_escalation_boundary": true,
      "prompt_requires_impl_md_update": false,
      "prompt_summary": "Next.js認証実装の現状把握とリファクタ候補列挙。編集禁止・読み取りのみ。判断はユーザーに委ねる。"
    }
  ],
  "spec_ambiguity_handling": {
    "recognized_ambiguity": false,
    "writes_to_design_md_as_undecided": false,
    "asks_user_in_chat_directly": false,
    "decides_alone": false
  },
  "final_report_style": {
    "escalation_at_top": false
  }
}
```
