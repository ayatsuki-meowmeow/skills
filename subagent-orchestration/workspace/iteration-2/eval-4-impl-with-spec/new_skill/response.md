## プラン

subagent-orchestration スキルの規約に従い、オーケストレーターである私自身は実装を行わず、実装エージェント（Sonnet）1 体に委譲します。design.md（仕様）と impl.md（方針）が既に整備されている前提なので、方針判断の余地は小さくコード生成中心のタスクと判定し、Sonnet を選択します。委譲プロンプトには (1) 役割、(2) `docs/features/badges/design.md` と `docs/features/badges/impl.md` のパスと「まず両方読め」の指示、(3) タスク（`/api/users/:id/badges` エンドポイントの実装）、(4) エスカレーション指示（design.md から答えが出ない仕様の疑問は自己判断せず疑問と選択肢を成果物として返す。技術的な内部実装判断は impl.md に理由を記録して自走）、(5) 境界（範囲外リファクタリング・テスト追加・依存更新は禁止）、(6) 完了時の impl.md 更新義務、(7) 成果物末尾に自身のコンテキスト使用率を自己申告し 50% に近づいたら成果と未完了を明文化して停止、を明記します。並列化する独立タスクはないため単発ディスパッチです。実装エージェントから疑問が返ってきた場合は、選択肢とトレードオフを design.md の「未決事項」セクションに追記した上でユーザーに口頭で「design.md の該当セクションを見て決定してください」と依頼し、決定後に「決定事項」へ移して作業を再開します。最終報告ではエスカレーション事項を先頭に置き、変更ファイル一覧・impl.md 更新の有無・未解決事項を要約します。

### 委譲プロンプト本文（実装エージェント / Sonnet）

```
あなたは実装専門のサブエージェントです。以下のタスクを担当してください。

# コンテキスト
- 仕様: docs/features/badges/design.md（真実の source。まず必ず読むこと）
- 実装方針: docs/features/badges/impl.md（設計方針・構成。まず必ず読むこと）
- 上記 2 ファイルを読んでから作業を開始してください。

# タスク
`/api/users/:id/badges` エンドポイントを、design.md の仕様と impl.md の方針に厳密に沿って実装してください。
完了時に impl.md の「実装状況」「構成」欄を最新化してください（実装ファイルの追加・変更点の反映）。

# エスカレーション指示
- design.md を読んでも答えが出ない仕様・要件の疑問が出た場合は、自分で判断せず、
  「疑問 / 選択肢 / 各選択肢のトレードオフ / 推奨」の形にまとめて成果物として返してください。
- 仕様に影響しない内部実装判断（ライブラリの使い方など）は自分で決めて構いませんが、
  判断理由を impl.md に必ず記録してください。迷ったらエスカレーションに倒してください。

# 境界（やらないこと）
- タスク範囲外のリファクタリング / 最適化 / コメント追加 / 未使用コード削除は禁止。
- 依頼していないテスト追加・依存パッケージの更新は禁止。
- design.md / impl.md に書かれていない仕様を独自に追加しない。

# 成果物フォーマット
1. 変更ファイル一覧と各ファイルの変更概要
2. impl.md の更新箇所サマリ
3. 未解決の疑問（あれば選択肢と推奨を添えて）
4. 末尾に「自身のコンテキスト使用率（概算）: XX%」を必ず記載

# コンテキスト管理ルール
- 途中で自分のコンテキスト使用率が 50% に近づいたら、そこまでの成果物と未完了リストを
  明文化して停止してください。「まだ動く」からと引っ張らないでください。
- compact（自己要約による圧縮）は禁止です。
```

```json
{
  "would_delegate": true,
  "delegate_count": 1,
  "parallel_dispatch": false,
  "delegations": [
    {"role_type": "実装", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "design.md/impl.md を読み /api/users/:id/badges を実装。仕様疑問はエスカレ、impl.md 更新、範囲外変更禁止、コンテキスト使用率申告。"}
  ],
  "spec_ambiguity_handling": {"recognized_ambiguity": false, "writes_to_design_md_as_undecided": false, "asks_user_in_chat_directly": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
