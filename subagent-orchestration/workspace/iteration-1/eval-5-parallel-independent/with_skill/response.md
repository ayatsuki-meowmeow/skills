## プラン

featureA と featureB は独立した機能なので、**同一ターンで 2 つの調査サブエージェントを並列起動**します。オーケストレーター側では、事前に `docs/featureA/design.md`・`impl.md`、`docs/featureB/design.md`・`impl.md` の存在をリポジトリ内で確認し、あれば各サブエージェントに参照パスを渡します（無い場合も委譲プロンプトで「無ければその旨を成果物に記載」と指示）。調査は広い読解と判断が要る Opus タスクとして、両サブエージェントに `model: "opus"` を指定します。実装コードの改変は禁止（境界）、仕様に関わる疑問が出たら勝手に決めず「未解決の疑問」として返却させます（エスカレーション指示）。両サブエージェントには成果物末尾に自己申告のコンテキスト使用率を必ず含めさせ、50% 接近時は成果と未完了リストを明文化して停止させます。戻ってきた成果物は 2 件をユーザー向けに要約し、もし仕様上の未解決疑問があれば `design.md` の「未決事項」セクションに追記した上で、報告の先頭でユーザーに決定を仰ぎます。impl.md の更新は今回「調査のみ」で実装差分がないため対象外とします。

### 委譲プロンプト本文（featureA 向け、featureB は名前差し替えで対称に発行）

```
あなたはコードベース調査の専門エージェントです。

【コンテキスト】
- 対象機能: featureA（featureB とは独立）
- まず docs/featureA/design.md と docs/featureA/impl.md を読んでください。存在しなければ「未整備」と成果物に明記してください。
- 他機能（featureB）には踏み込まないでください。

【タスク】
featureA の現状を調査してください。観点:
1. 実装エントリポイント・主要モジュールのファイルパス
2. 現在の構造・データフロー・依存関係
3. 既知の制約・TODO・未実装箇所（コード内コメントや impl.md から拾う）
4. design.md との乖離があれば指摘

【成果物】
- 上記 4 観点の要約（Markdown 箇条書き、関連ファイルパスを併記）
- 未解決の疑問（仕様に関わるもの）を「未解決の疑問」セクションで列挙
- 末尾に自身のコンテキスト使用率（概算 %）を必ず記載

【エスカレーション】
仕様・要件に関わる疑問は自分で判断せず、「未解決の疑問」として成果物に含めてください。

【境界】
- コードの変更・ファイル書き込みは一切しないこと（読み取り専用）
- タスク範囲外（featureB、無関係なリファクタ提案など）に踏み込まないこと
- コンテキスト使用率が 50% に近づいたら、そこまでの成果と未完了リストを明文化して停止してください
```

featureB 用は「featureA」を「featureB」に置換した対称版を同一ターン内で発行し並列実行します。

---

```json
{
  "would_delegate": true,
  "delegate_count": 2,
  "parallel_dispatch": true,
  "delegations": [
    {
      "role_type": "調査",
      "model": "opus",
      "prompt_mentions_design_md": true,
      "prompt_mentions_impl_md": true,
      "prompt_mentions_context_self_report": true,
      "prompt_mentions_escalation_boundary": true,
      "prompt_requires_impl_md_update": false,
      "prompt_summary": "featureAの実装エントリ・構造・制約・design.md乖離を読み取り専用で調査し未解決疑問と使用率を返却"
    },
    {
      "role_type": "調査",
      "model": "opus",
      "prompt_mentions_design_md": true,
      "prompt_mentions_impl_md": true,
      "prompt_mentions_context_self_report": true,
      "prompt_mentions_escalation_boundary": true,
      "prompt_requires_impl_md_update": false,
      "prompt_summary": "featureBの実装エントリ・構造・制約・design.md乖離を読み取り専用で調査し未解決疑問と使用率を返却"
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
