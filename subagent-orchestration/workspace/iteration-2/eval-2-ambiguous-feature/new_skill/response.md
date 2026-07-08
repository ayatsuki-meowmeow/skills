# プラン

「バッジを表示する機能」は仕様が全く決まっていない（バッジの種類・獲得条件・表示形式・データソース・既存モデルとの関係など未定）ので、いきなり実装に入れません。オーケストレーション規約に従い、まず調査エージェントを 1 体（Opus）起動して、リポジトリの現状（プロフィール画面の実装・ユーザーモデル・design.md / impl.md の有無）を掴みます。その成果を元に、私（オーケストレーター）が design.md の「未決事項」セクションにバッジ機能の疑問と選択肢・推奨を整理して追記し、ユーザーに「design.md を見て決定してほしい」とだけエスカレーションします。決定が下りてから、実装エージェント（Sonnet）を別ターンで起動する構成です。この時点で並列にする理由はない（実装は仕様確定待ち、ドキュメントも調査結果待ち）ので逐次実行にします。

## 調査エージェントへの委譲プロンプト本文

> あなたは調査専門のサブエージェントです。コードは変更せず、以下を成果物として返してください。
>
> **コンテキスト**: プロジェクトルートの `design.md` と `impl.md` を最初に確認してください（無ければその旨を報告）。ユーザープロフィール画面に「バッジ」表示機能を追加する予定です。
>
> **タスク**:
> 1. プロフィール画面の実装ファイルパスと構造
> 2. User / Profile 関連のデータモデル・スキーマ
> 3. 既に「バッジ」「achievement」「badge」等に該当する既存概念があるか
> 4. UI コンポーネントライブラリ・スタイリング方針
> 5. design.md / impl.md の現状（存在しなければその事実）
>
> **エスカレーション指示**: 仕様に関する疑問（例: バッジの種類・獲得条件・表示位置）が生じても、あなたの判断で仕様を決めず、疑問リストとして返してください。
>
> **境界**: コード変更・ドキュメント更新・実装は一切行わない。読解と要約のみ。
>
> **コンテキスト自己申告**: 成果物末尾に現在のコンテキスト使用率（概算）を必ず記載。50% に近づいたらそこまでの成果と未完了リストを明文化して停止してください。

調査エージェントは impl.md の更新責務は持たない（調査のみ）ため、impl.md 更新指示は入れません。ユーザーへの質問はチャットに選択肢を貼らず、必ず design.md 経由で行います。最終報告時はエスカレーション事項を先頭に置きます。

```json
{
  "would_delegate": true,
  "delegate_count": 1,
  "parallel_dispatch": false,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "プロフィール画面・Userモデル・既存badge概念・UI方針・design.md/impl.md 有無を調査。仕様の疑問は判断せず疑問リストで返す。"}
  ],
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "writes_to_design_md_as_undecided": true, "asks_user_in_chat_directly": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
