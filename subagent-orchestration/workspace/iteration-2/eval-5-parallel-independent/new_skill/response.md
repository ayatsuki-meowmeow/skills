# プラン

featureA と featureB は独立しているため、subagent-orchestration 規約に従い、2 つの調査サブエージェントを**同一ターンで並列起動**します。いずれも調査タスクなので判断・読解が主となり、モデルは **Opus** を指定します。調査エージェントはコードを変更せず、成果物は「関連ファイルパス / 現状の構造 / 制約の要約 / 未解決の疑問」です。委譲プロンプトには (1) 役割、(2) design.md / impl.md のパスと「まず読め」、(3) タスク内容、(4) 仕様の疑問はチャットに列挙して返す（自分で判断しない）というエスカレーション指示、(5) 境界（コード変更禁止・タスク範囲外の作業禁止・impl.md 更新はしない）、(6) 成果物末尾でのコンテキスト使用率自己申告と 50% 接近時の停止規約、を全て含めます。仕様に関する疑問が返ってきた場合は、選択肢と推奨を添えて design.md の「未決事項」セクションに追記し、ユーザーには「design.md の該当セクションを見て決定してください」とだけ依頼します（チャットに選択肢は貼らない）。impl.md への反映が必要な場合は別途ドキュメントエージェントに委譲します。最終報告はエスカレーション事項を先頭に、次に featureA / featureB の要約という順で並べます。

## 委譲プロンプト本文（featureA 調査エージェント宛、Opus）

```
あなたは調査専門サブエージェントです。コードは一切変更しないでください。

# コンテキスト
- 対象機能: featureA
- まず次のファイルを読んでください（存在しない場合はその旨を報告に含める）:
  - docs/featureA/design.md
  - docs/featureA/impl.md
- 既存の設計判断・実装状況を必ずこの 2 ファイルから出発点として把握してください。

# タスク
featureA の現状を調査し、以下を成果物として返してください:
1. 関連ファイル・ディレクトリのパス一覧（役割つき）
2. 現状のモジュール構造・データフローの要約
3. 既知の制約・技術的負債・未実装箇所
4. design.md との乖離があればその指摘
5. 仕様として判断が割れる余地のある未解決の疑問（選択肢つき）

# エスカレーション指示
仕様・要件に関わる疑問（design.md に答えのない選択）を見つけても、あなたの判断で確定させないでください。疑問・選択肢・各選択肢のトレードオフ・あなたの推奨を成果物に列挙して返してください。オーケストレーターが design.md 経由でユーザーに諮ります。

# 境界
- コードは変更しない
- design.md / impl.md も更新しない（調査エージェントの範囲外）
- タスク範囲を超えたリファクタや最適化は行わない

# コンテキスト管理
成果物の末尾に、あなた自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら、そこまでの成果と未完了リストを明文化して停止してください。続きは別のサブエージェントに引き継ぎます。
```

featureB 用も同一雛形で、対象機能名とドキュメントパスだけ差し替えます。

```json
{
  "would_delegate": true,
  "delegate_count": 2,
  "parallel_dispatch": true,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "featureA の関連ファイル・構造・制約・未解決疑問を、design.md/impl.md を起点にコード変更せず調査させる"},
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "featureB の関連ファイル・構造・制約・未解決疑問を、design.md/impl.md を起点にコード変更せず調査させる"}
  ],
  "spec_ambiguity_handling": {"recognized_ambiguity": false, "writes_to_design_md_as_undecided": false, "asks_user_in_chat_directly": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
