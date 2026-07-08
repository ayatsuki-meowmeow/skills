## プラン

featureA と featureB は独立した機能なので、同一ターンで **調査エージェントを 2 つ並列起動** します（rules.md「並列実行」節に準拠）。オーケストレーター自身は広範なコードリーディングを行わず、結論だけを受け取ります。モデルは調査タスク（思考と判断が主）なので **Opus** を指定します。各エージェントには対応する feature の `docs/<feature>/design.md` と `impl.md` を先に読ませ、なければその旨を報告させます。コード変更は禁止、境界は「担当 feature 以外に踏み込まない」で明示します。仕様・要件に関わる疑問はサブエージェントに判断させず「未解決の疑問」として返させ、返ってきたらこちらで design.md の未決事項セクションに記録してユーザーに決定を仰ぎます。コンテキスト使用率は自己申告させ、50% に近づいたら成果と未完了リストを明文化して停止させます。両者の成果が揃ったら要約し、エスカレーション（未解決の疑問）を先頭に置いた形でユーザーに報告します。

### 委譲プロンプト（調査エージェント A / Opus・並列）

```
あなたはコードベース調査の専門エージェントです。

コンテキスト:
- まず docs/featureA/design.md と docs/featureA/impl.md を読んでください。
- 存在しない場合は「未整備」と成果物冒頭に明記してください（作成はしない）。

タスク: featureA の現状を調査する。
- 実装済み範囲 / 未実装範囲
- 関連ファイル・モジュールのパス一覧
- 依存関係・外部連携・制約
- design.md の仕様と実装の乖離

成果物として返すもの:
- 上記の要約（結論ファースト）
- 関連ファイルパス一覧
- 未解決の疑問（仕様・要件に関わるものは自分で判断せず必ずここに列挙）
- 成果物末尾に自身のコンテキスト使用率（概算可）を必ず申告

エスカレーション: 仕様・要件に関わる疑問は自分で判断しない。選択肢とトレードオフを添えて「未解決の疑問」に入れる。

境界:
- コードは一切変更しない。
- featureA の範囲を超える調査（featureB や他機能）はしない。
- コンテキスト使用率が 50% に近づいたら、そこまでの成果と未完了リストを明文化して停止する。
```

### 委譲プロンプト（調査エージェント B / Opus・並列）

上記と同一構造で「featureA」→「featureB」に置換したもの。docs パス、成果物、境界すべて featureB に読み替える。

```json
{
  "would_delegate": true,
  "delegate_count": 2,
  "parallel_dispatch": true,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "featureA の現状（実装範囲・関連ファイル・依存・制約・design.md との乖離）を調査。コード変更禁止、範囲は featureA のみ、仕様の疑問は未解決として報告。"},
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "featureB の現状（実装範囲・関連ファイル・依存・制約・design.md との乖離）を調査。コード変更禁止、範囲は featureB のみ、仕様の疑問は未解決として報告。"}
  ],
  "spec_ambiguity_handling": {"recognized_ambiguity": false, "writes_to_design_md_as_undecided": false, "asks_user_in_chat_directly": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
