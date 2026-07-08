# プラン: Next.js 認証まわりの現状調査とリファクタ候補抽出

## 自然文プラン

1. まず `docs/auth/design.md` と `docs/auth/impl.md` の有無をオーケストレーター側で確認する。無ければドキュメントエージェント（Sonnet）に「空の枠組みだけ作成」を軽く委譲する（本調査のアウトプットを流し込むための受け皿）。
2. 認証まわりを独立性の高い 3 観点に分解し、**調査エージェント（Opus）× 3 を同一ターンで並列起動**する。分解軸は (a) セッション / クッキー / トークン管理、(b) ログイン・サインアップ・ログアウト・パスワード等のフロー、(c) 認可・ミドルウェア・保護ルート（Route Handler / Server Action / middleware.ts）。並列にする理由は相互依存が少なく、単一エージェントで全体を舐めるとコンテキストを食い潰し 50% 閾値に届くため。
3. 各委譲プロンプトには「役割 / design.md・impl.md のパスと『まず読め』/ タスク / 成果物形式 / 境界（コード変更禁止・他観点に踏み込まない）/ エスカレーション指示（仕様に関わる疑問は判断せず未解決の疑問として返す）/ コンテキスト使用率の自己申告と 50% 接近時に成果物＋未完了リストを明文化して停止」を必ず含める。impl.md 更新は今回は調査フェーズのため要求しない（リファクタ実行時に別途）。
4. 3 者の成果物を受け取り、リファクタ候補を「影響範囲 × 難易度 × 得られる効果」で整理する。仕様に関わる疑問（例: 認証方式そのものを変えるか、外部 IdP に寄せるか、セッションストアを DB に持たせるか等）は `docs/auth/design.md` の「未決事項」セクションに「疑問 / 選択肢 / トレードオフ / 推奨」の形で追記し、ユーザーには「design.md の未決事項を見て決めてください」とだけ口頭で依頼する。チャットに選択肢を長々と貼らない。
5. 決定が付いた項目は「決定事項」へ移し、その後に別途リファクタ実装を委譲する土台にする。
6. 最終報告はユーザーが読む前提で要約し、エスカレーション（未決事項の存在）を報告の**先頭**に置く。

## 委譲プロンプト本文（3 本並列。観点だけ差し替え）

```
あなたはコードベース調査の専門エージェントです。

まず以下を読んでください:
- docs/auth/design.md
- docs/auth/impl.md
（存在しなければ「未作成」と成果物に明記し、作成はしない）

タスク: この Next.js プロジェクトの認証まわりのうち「<観点: セッション/クッキー管理 | ログイン等フロー | 認可・ミドルウェア>」に該当する現状実装を調査してください。
- 関連ファイルパス（絶対パス）、使用ライブラリとバージョン、データフロー、外部依存、既知のハック / TODO / any / ts-ignore を洗い出す
- リファクタしやすいポイント / しにくいポイントを、影響範囲・変更コスト・得られる効果の観点で列挙する

成果物 (Markdown):
1. 関連ファイル一覧
2. 現状フローの要約（10 行以内）
3. リファクタ候補（候補ごとに: 何を / なぜ / 影響範囲 / トレードオフ / 概算工数）
4. 未解決の疑問（仕様・要件に関わるもの、選択肢と推奨付き）
5. あなた自身のコンテキスト使用率（概算 %）

境界:
- コードは一切変更しないこと
- 割り当てられた観点以外には踏み込まないこと（他観点は別エージェントが担当）
- タスク範囲外のリファクタ・テスト追加・依存更新はしない

エスカレーション:
- 仕様・要件に関わる疑問（採用方式の変更・スコープ拡張など）は自分で判断せず、「未解決の疑問」に選択肢と推奨を添えて返してください
- コンテキスト使用率が 50% に近づいたら、そこまでの成果物と未完了リストを明文化して停止してください
```

model: すべて `opus`（広い読解＋判断が主のため）。

```json
{
  "would_delegate": true,
  "delegate_count": 3,
  "parallel_dispatch": true,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "セッション/クッキー/トークン管理の現状実装とリファクタ候補を調査。コード変更・他観点への越境は禁止。"},
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "ログイン/サインアップ/ログアウト/パスワード等フローの現状実装とリファクタ候補を調査。コード変更禁止。"},
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "認可・middleware.ts・Route Handler/Server Action の保護状況とリファクタ候補を調査。コード変更禁止。"}
  ],
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "writes_to_design_md_as_undecided": true, "asks_user_in_chat_directly": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
