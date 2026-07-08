## プラン

subagent-orchestration スキルの規約に従い、私（オーケストレーター）は直接コード編集をせず、実装専門サブエージェントに委譲します。仕様は `docs/features/badges/design.md` に、実装方針は `docs/features/badges/impl.md` に集約済みなので、思考の余地は小さく、モデルは Sonnet を選びます。委譲プロンプトには「まず design.md と impl.md を読む」「design.md の仕様に従う」「仕様上の疑問は勝手に決めず選択肢と一緒に停止して返す（エスカレーション）」「タスク範囲外の最適化・リファクタは触らない（境界）」「完了後に impl.md の実装状況・構成を更新する」「成果物末尾に自身のコンテキスト使用率と、50% に近づいたら成果と未完了リストを明文化して止めることを義務化」を含めます。並列化する独立タスクは今回無いので、単一サブエージェントで進めます。返ってきた成果物は仕様との乖離・impl.md 更新の有無・未解決の疑問の 3 点で検収し、疑問があれば design.md の「未決事項」セクションに追記した上でユーザーに決定を仰ぎます。エスカレーションはユーザー報告の先頭に出します。

### 実装サブエージェントへの委譲プロンプト（案）

```
あなたは実装の専門エージェントです。モデル: sonnet。

# コンテキスト
- 仕様: docs/features/badges/design.md
- 実装方針: docs/features/badges/impl.md
着手前に必ず両方を読み、design.md の仕様と impl.md の方針を前提にしてください。

# タスク
`/api/users/:id/badges` エンドポイントを実装してください。
- design.md の仕様（入出力・認可・エラーケース）に厳密に従うこと
- impl.md の方針（ディレクトリ構成・レイヤ分割・命名）に沿うこと
- 既存の類似エンドポイントの実装パターンに合わせること

# 成果物
1. 変更ファイル一覧と各ファイルの変更概要（diff の要点）
2. impl.md の「実装状況」「構成」セクションの更新（本エンドポイントを追加）
3. 未解決の疑問リスト（あれば）
4. 動作確認方法（起動コマンド・叩き方の例）
5. 末尾に自身のコンテキスト使用率（概算）

# エスカレーション指示
design.md から答えが出ない仕様上の選択（例: 認可の粒度、ページング有無、フィールドの表示条件など）に直面したら、自分で決めずに作業を止め、「疑問 / 選択肢 / 各選択肢のトレードオフ / 推奨」を成果物として返してください。

# 境界（やらないこと）
- タスク範囲外の最適化・リファクタリング・コメント追加・未使用コード削除・依存更新はしない
- design.md / impl.md 以外の仕様ドキュメントは書き換えない
- design.md は編集しない（編集はユーザー + オーケストレーターの責務）

# コンテキスト管理
コンテキスト使用率が 50% に近づいたら、そこまでの成果物と未完了リストを明文化して停止してください。無理に完走させないこと。
```

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
      "prompt_summary": "design.md/impl.md を読み /api/users/:id/badges を実装、impl.md 更新、仕様疑問は停止して返す、範囲外変更禁止、50%で停止"
    }
  ],
  "spec_ambiguity_handling": {
    "recognized_ambiguity": false,
    "writes_to_design_md_as_undecided": false,
    "asks_user_in_chat_directly": false,
    "decides_alone": false
  },
  "final_report_style": {
    "escalation_at_top": true
  }
}
```
