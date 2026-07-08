## プラン

このタスクは仕様が大きく未確定です（「バッジ」の定義・データソース・表示位置・複数表示可否・クリック挙動などが不明）。subagent-orchestration および design-impl-docs スキルの規約に従い、**メインエージェントは実装を直接進めず、まず調査エージェントに現状把握と design.md 起票を委譲**します。仕様上の疑問は自分で判断せず、design.md の「未決事項」セクションに選択肢・トレードオフ・推奨を書き出し、ユーザーに決定を仰いでから実装に進みます。エスカレーション事項は口頭でチャットに長々と貼らず、「design.md の未決事項セクションを見て決定してください」とだけ伝えます。今回は依存関係があるため並列化はせず、まず調査＋design.md 起票の 1 エージェントのみ起動します。design.md の未決事項が確定した後、続くターンで実装エージェント（Sonnet）に委譲する予定です。

### 委譲プロンプト（調査 + design.md 起票エージェント / Opus）

```
あなたはコードベース調査と design.md 起票の専門エージェントです。実装は行いません。

コンテキスト:
- 対象タスク: ユーザープロフィール画面への「バッジ」表示機能追加
- 対象 design.md / impl.md のパスを最初に確認してください（存在しなければ design-impl-docs スキルの配置規約に従って新規作成）
- design-impl-docs スキルと subagent-orchestration スキルの規約に従うこと

タスク:
1. 既存プロフィール画面の実装箇所・データフロー・UI 構造を調査し、関連ファイルパスと現状構造を要約する
2. 「バッジ」機能に関する仕様の未確定点を洗い出し、design.md の「未決事項」セクションに以下の形式で追記する:
   - 疑問（例: バッジの種類は何を指すか？ 実績/認証済み/ロール/通知など）
   - 選択肢（各案）
   - 各選択肢のトレードオフ
   - 推奨案
   最低限カバーする論点:
     a. バッジの意味・種類（実績/認証/ロール/通知バッジ 等）
     b. データソース（静的/API/ユーザー属性から算出）
     c. 表示位置（アバター横/名前横/独立セクション）
     d. 単一 vs 複数表示、優先順位
     e. インタラクション（クリック・ホバーで詳細表示など）
     f. アクセシビリティ要件（alt text、色以外の識別）
3. 実装は絶対に行わない。コード変更・パッケージ追加もしない
4. impl.md には現時点で確定した実装方針が無いため、更新不要（存在しなければ雛形だけ用意）

エスカレーション指示:
- 追加で判断に迷う仕様上の疑問が出たら、自分で決めず未決事項として design.md に追記して返すこと

境界:
- タスク範囲外のリファクタリング・最適化・関連機能の変更をしない
- コンテキスト使用率が 50% に近づいたら、そこまでの成果と未完了リストを明文化して停止する

成果物:
- 更新した design.md / impl.md のパスと差分概要
- 未決事項のサマリ（ユーザーに提示する 1 行タイトルのリスト）
- 成果物末尾に自身のコンテキスト使用率（概算）を必ず含めること
```

### この後の進め方（実装ターン以降の予告）

- 調査エージェントからの成果を受け取り、ユーザーへ「design.md の未決事項セクションを確認して決定してください」と依頼する（選択肢の詳細はチャットに貼らない）。
- ユーザー決定後、決定事項を design.md の該当セクションに移し、実装エージェント（Sonnet, `model: "sonnet"`）に委譲する。委譲プロンプトには design.md / impl.md のパス、境界（タスク外変更禁止）、エスカレーション指示、impl.md 更新指示、コンテキスト自己申告を含める。
- 実装完了後は必要に応じてレビューエージェント（Opus）に design.md との乖離チェックを委譲する。

```json
{
  "would_delegate": true,
  "delegate_count": 1,
  "parallel_dispatch": false,
  "delegations": [
    {
      "role_type": "調査",
      "model": "opus",
      "prompt_mentions_design_md": true,
      "prompt_mentions_impl_md": true,
      "prompt_mentions_context_self_report": true,
      "prompt_mentions_escalation_boundary": true,
      "prompt_requires_impl_md_update": false,
      "prompt_summary": "プロフィール画面の現状調査と、バッジ仕様の未確定点を design.md 未決事項セクションに選択肢・推奨付きで起票させる（実装は行わせない）"
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
