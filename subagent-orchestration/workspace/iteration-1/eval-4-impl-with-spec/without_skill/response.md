# プラン

まず `docs/features/badges/design.md` と `docs/features/badges/impl.md` を Read して、仕様（レスポンス形状・エラーケース・認証要件など）と実装方針（配置ディレクトリ・使用ライブラリ・レイヤ構成）を突き合わせて把握します。あわせて既存の類似エンドポイントの実装（ルーティング登録場所、DI/リポジトリ層の書き方、テスト規約）を Grep/Read で確認し、impl.md の指示と齟齬がないかチェックします。仕様と方針を読み込んで着地点が明確になった段階で、実装本体はサブエージェント（Sonnet）に委譲します（実装は定型的な作業パターンに該当するため）。委譲プロンプトには design.md と impl.md の絶対パスを明記し、両方を読んでから着手すること、仕様の曖昧さや impl.md 方針との矛盾を発見したら自己判断で埋めずに一旦停止してこちらにエスカレーションすること、実装完了時にはコンテキスト使用状況を自己申告すること、実装過程で方針の追記が必要になった場合は impl.md を更新することを明記します。委譲プロンプト本文の骨子は以下です:

> `/api/users/:id/badges` エンドポイントを実装してください。仕様は `/Users/konoreiji/skills/subagent-orchestration/workspace/iteration-1/docs/features/badges/design.md`、実装方針は同 `impl.md` に定義されています。両方を Read してから着手し、design.md のレスポンス契約と impl.md のレイヤ構成・ライブラリ選定に従ってください。作業中に (a) design.md の仕様が曖昧・未決定である、(b) impl.md の方針と既存コードベースの実態が矛盾する、(c) impl.md に記載のないアーキ判断が必要になる、のいずれかに該当したら、自分で決めず作業を止めて質問を投げ返してください。impl.md に追記すべき新方針が生まれた場合は impl.md も更新してください。完了時に「今回のタスクでのコンテキスト使用量（体感）」を末尾に自己申告してください。

サブエージェント完了後、私（メイン）は成果物の差分レビュー・design.md との照合・エスカレーション事項の有無を最終確認します。仕様の曖昧さがあればチャットでユーザーに直接聞かず design.md に「未決事項」として追記して指示を仰ぐ運用にします。最終報告はエスカレーション事項を最上部に置く形式でまとめます。

```json
{
  "would_delegate": true,
  "delegate_count": 1,
  "parallel_dispatch": false,
  "delegations": [
    {
      "role_type": "実装",
      "model": "sonnet",
      "prompt_mentions_design_md": true,
      "prompt_mentions_impl_md": true,
      "prompt_mentions_context_self_report": true,
      "prompt_mentions_escalation_boundary": true,
      "prompt_requires_impl_md_update": true,
      "prompt_summary": "design.md/impl.md を読んで /api/users/:id/badges を実装。曖昧なら停止・エスカレーション、方針追加時は impl.md 更新、完了時にコンテキスト自己申告。"
    }
  ],
  "spec_ambiguity_handling": {
    "recognized_ambiguity": true,
    "writes_to_design_md_as_undecided": true,
    "asks_user_in_chat_directly": false,
    "decides_alone": false
  },
  "final_report_style": {
    "escalation_at_top": true
  }
}
```
