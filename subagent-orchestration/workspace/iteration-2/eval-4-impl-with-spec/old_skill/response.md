## プラン

このタスクはドキュメントが揃っている実装作業（design.md に仕様、impl.md に方針）なので、subagent-orchestration スキルの規約に従い、私（オーケストレーター）は直接コードに触れず、実装専門のサブエージェントに委譲します。まず design.md と impl.md の両方を確認できる状態でサブエージェントを起動しますが、着手前に私自身は両ファイルの存在と概要だけ Read で軽く確認し、委譲プロンプトに具体的なパスと期待成果物を明記します。

モデル選択は、方針が impl.md に落ちている前提のため実装向けに **Sonnet** を採用します（判断余地が小さい定型実装のため）。委譲プロンプトには (1) 役割、(2) コンテキスト=design.md / impl.md のパスと「まず読め」の指示、(3) タスク=`/api/users/:id/badges` エンドポイント実装、(4) エスカレーション指示=design.md から答えが出ない仕様判断は勝手に決めず疑問と選択肢を返して停止、(5) 境界=タスク範囲外の変更禁止、(6) impl.md の構成・実装状況を更新、(7) 成果物末尾に自身のコンテキスト使用率を自己申告、50% に近づいたら成果と未完了リストを明文化して停止、を含めます。

サブエージェントから仕様上の疑問が返ってきた場合は、私が design.md の「未決事項」セクションに疑問・選択肢・トレードオフ・推奨を追記し、ユーザーには「design.md の該当セクションを見て決定してください」とだけ伝え、決定後に「決定事項」へ移してから再開します。チャットで選択肢を並べたり独断で仕様を決めることはしません。並列化余地は今回ありません（単一エンドポイントの実装）。完了後は impl.md 更新の確認と、成果物の要約報告（エスカレーションがあれば先頭）を行います。

### 委譲プロンプト本文（実装エージェント / Sonnet）

```
あなたは実装の専門エージェントです。
まず以下を必ず読んでください:
- docs/features/badges/design.md（仕様・要件）
- docs/features/badges/impl.md（実装方針・現状構成）

タスク:
- `/api/users/:id/badges` エンドポイントを実装する。
- 仕様は design.md に従い、実装方針・レイヤ構成・命名・エラーハンドリング等は impl.md の方針に沿うこと。

エスカレーション指示:
- design.md から答えが出ない仕様上の選択に直面したら、実装で勝手に決めないこと。
- その疑問・想定される選択肢・各選択肢の影響を成果物として返し、作業を止めてオーケストレーターに戻すこと。

境界:
- タスク範囲外の変更（無関係なリファクタ、依存更新、テスト追加以外の整理など）はしない。
- 既存の他エンドポイントの挙動を変えない。

完了時の成果物:
- 変更/追加ファイル一覧と各ファイルの変更概要
- impl.md の構成・実装状況の更新（このエンドポイントを反映）
- 動作確認手段（型チェック・テスト等）
- 未解決の疑問（あれば）
- 応答末尾に自身のコンテキスト使用率（概算）を必ず記載

コンテキスト管理:
- 使用率が 50% に近づいたら、そこまでの成果と未完了リストを明文化して停止し、引き継ぎ可能な形で返すこと。
```

```json
{
  "would_delegate": true,
  "delegate_count": 1,
  "parallel_dispatch": false,
  "delegations": [
    {"role_type": "実装", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "design.md/impl.mdを読み /api/users/:id/badges を実装。仕様不明はエスカレーション、impl.md更新、コンテキスト自己申告。"}
  ],
  "spec_ambiguity_handling": {"recognized_ambiguity": false, "writes_to_design_md_as_undecided": false, "asks_user_in_chat_directly": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
