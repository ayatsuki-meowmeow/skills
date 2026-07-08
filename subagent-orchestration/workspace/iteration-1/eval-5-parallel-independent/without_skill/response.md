featureA と featureB は独立した機能とのことなので、依存関係を気にせず 2 つの調査サブエージェントを並列に起動します。メインの私は指揮に徹し、各サブエージェントには「調査のみで、コード変更はしない」「関連ファイル・現状の実装範囲・未実装/TODO・気になる箇所を洗い出す」「絶対パス付きで報告する」ことを明示します。両方の結果が揃ったら、featureA / featureB それぞれの現状サマリと、差異・共通する懸念点を統合して報告します。仕様の曖昧さや判断が必要な箇所が出た場合は、勝手に決めず、報告時にユーザーに確認事項として提示します。

サブエージェントへの委譲プロンプト（featureA 用、featureB 用も同型で名前だけ差し替え）:

---
あなたは調査専門のサブエージェントです。以下の作業を行ってください。

対象: featureA の現状調査（コード変更は一切禁止、Read/Grep/Glob/Bash の読み取り系のみ使用）

やること:
1. featureA に関連するファイル・ディレクトリを列挙（絶対パスで）
2. featureA の実装範囲・エントリーポイント・主要な関数/クラス・データフローを要約
3. 未実装箇所・TODO/FIXME コメント・明らかに壊れていそうな箇所を列挙
4. テストの有無と、テストがカバーしている範囲
5. 依存している外部モジュールや他機能との結合点

報告フォーマット:
- 冒頭 5 行以内で「featureA の現状ひとこと要約」
- その後、上記 1〜5 を箇条書きで
- 末尾に「調査中に判断が必要と感じた点（勝手に決めなかったもの）」を列挙

制約:
- コードは一切変更しない
- ファイル絶対パスで示す
- 不明点は不明のまま報告する（推測で埋めない）
---

```json
{
  "would_delegate": true,
  "delegate_count": 2,
  "parallel_dispatch": true,
  "delegations": [
    {
      "role_type": "調査",
      "model": "unspecified",
      "prompt_mentions_design_md": false,
      "prompt_mentions_impl_md": false,
      "prompt_mentions_context_self_report": false,
      "prompt_mentions_escalation_boundary": true,
      "prompt_requires_impl_md_update": false,
      "prompt_summary": "featureA の関連ファイル・実装範囲・TODO・テスト・依存を絶対パス付きで調査。コード変更禁止。"
    },
    {
      "role_type": "調査",
      "model": "unspecified",
      "prompt_mentions_design_md": false,
      "prompt_mentions_impl_md": false,
      "prompt_mentions_context_self_report": false,
      "prompt_mentions_escalation_boundary": true,
      "prompt_requires_impl_md_update": false,
      "prompt_summary": "featureB の関連ファイル・実装範囲・TODO・テスト・依存を絶対パス付きで調査。コード変更禁止。"
    }
  ],
  "spec_ambiguity_handling": {
    "recognized_ambiguity": false,
    "writes_to_design_md_as_undecided": false,
    "asks_user_in_chat_directly": false,
    "decides_alone": false
  },
  "final_report_style": {
    "escalation_at_top": false
  }
}
```
