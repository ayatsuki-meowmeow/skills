# プラン: `formatDate` の null ハンドリング修正

小さい修正でも subagent-orchestration の規約に従い、直接編集せずサブエージェントに委譲します。まず `docs/format/design.md` と `impl.md` の有無を確認し、なければ作成します。ユーザー指示は「null → 空文字」と明確ですが、周辺仕様（`undefined` の扱い、`Invalid Date` の扱い、既存の他呼び出し元への影響）は曖昧なため、これらは調査結果を踏まえて design.md の「未決事項」に選択肢と推奨を書き、ユーザーに design.md 上で決定を仰ぎます（チャットで直接質問はしません）。

進め方は 3 段構え。(1) 調査エージェント（Opus）に `src/utils/format.ts` の現状と呼び出し元・既存テストを洗い出させ、未解決の仕様疑問を列挙させます。(2) design.md への未決事項追記が必要ならドキュメントエージェント（Opus）に委譲、決定後に (3) 実装エージェント（Sonnet）が修正 + Vitest/Jest でのユニットテスト（null、undefined、通常の Date、Invalid Date、境界値）を追加し、impl.md を更新します。最後に (4) レビューエージェント（Opus）で design.md との整合と回帰リスクをチェック。各委譲プロンプトには「コンテキスト使用率 50% で停止し、成果物末尾に使用率を自己申告」を含めます。

## 委譲プロンプト本文（抜粋）

**調査エージェント（Opus, 単発起動）:**

```
あなたはコードベース調査の専門エージェントです。まず docs/format/design.md と impl.md を読んでください（無ければその旨報告）。
タスク:
  1) src/utils/format.ts の formatDate の現在のシグネチャ・実装・throw 経路を要約
  2) formatDate を参照している呼び出し元を全て列挙し、null/undefined を渡している箇所があるか確認
  3) 既存テスト（*.test.ts / *.spec.ts）で formatDate を扱っているファイルを列挙
  4) 未解決の仕様疑問（undefined / Invalid Date / 空文字入力の扱いなど）を「疑問 / 選択肢 / 各選択肢のトレードオフ / 推奨」形式で列挙
成果物: 上記 1〜4 のサマリ。コード変更はしない。
末尾に自身のコンテキスト使用率（概算）を必ず記載。50% に近づいたら停止し未完了リストを返すこと。
```

**実装エージェント（Sonnet, 決定後に起動）:**

```
あなたは実装の専門エージェントです。まず docs/format/design.md と impl.md を読み、決定事項に従うこと。
タスク: src/utils/format.ts の formatDate を修正し、null（および design.md で決まった他の無効値）に対して空文字 "" を返すようにする。
併せて対応するユニットテスト（null ケース＋ design.md で決めた無効値ケース＋既存正常系の非退行）を追加。
完了後は impl.md の該当セクション（formatDate の状態・テスト状況）を更新すること。
design.md から答えが出ない仕様の選択に直面したら、実装で勝手に決めず疑問と選択肢を成果物として返して停止すること。
成果物: 変更ファイル一覧、diff 概要、テスト実行結果、未解決の疑問（あれば）。
末尾に自身のコンテキスト使用率（概算）を必ず記載。
境界: formatDate 以外のリファクタや無関係な整形は行わない。
```

**レビューエージェント（Opus, 実装後）:**

```
あなたはコードレビュー専門エージェントです。docs/format/design.md と impl.md を読んだうえで、直近の diff を対象に:
  - design.md の仕様との乖離
  - 呼び出し元での挙動変化（null 前提の分岐が二重化していないか）
  - テストが null/undefined/Invalid Date/正常系をカバーしているか
を確認。指摘は箇条書きで返す。末尾にコンテキスト使用率を記載。
```

## テスト方針（実装エージェントに渡す指示の要点）

- 正常系: 有効な `Date` オブジェクト / ISO 文字列で期待フォーマットになること（既存テストがあれば非退行）
- 異常系: `null` → `""`、`undefined` → design.md 決定に従う、`Invalid Date` → design.md 決定に従う
- 型: シグネチャを `Date | null | ...` に更新した場合、呼び出し元の型チェックも通ること
- 実行: プロジェクトのテストランナー（Vitest / Jest 等）で `pnpm test src/utils/format` 相当を実施し結果を成果物に含める

```json
{
  "would_delegate": true,
  "delegate_count": 3,
  "parallel_dispatch": false,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "formatDate の現状・呼び出し元・既存テストを列挙し、undefined/Invalid Date 等の仕様疑問を選択肢付きで返させる"},
    {"role_type": "実装", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "design.md の決定に従い formatDate を修正しテスト追加、impl.md 更新、範囲外リファクタ禁止"},
    {"role_type": "レビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": false, "prompt_requires_impl_md_update": false, "prompt_summary": "diff を design.md 仕様と照合、呼び出し元影響とテスト網羅性を確認"}
  ],
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "writes_to_design_md_as_undecided": true, "asks_user_in_chat_directly": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
