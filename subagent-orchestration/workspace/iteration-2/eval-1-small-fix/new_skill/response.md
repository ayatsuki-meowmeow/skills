# プラン

小さな bug fix ですが、規約に従い直接実装せず、サブエージェントに委譲します。まず `src/utils/format.ts` の現状把握と仕様の抜け（`undefined` や `Invalid Date` の扱い、既存テスト構成、`design.md` / `impl.md` の有無）を調査エージェント（Opus）に投げます。ここで未決事項（例: `null` は空文字だが `undefined` はどうするか、`Invalid Date` は空文字か例外か）が返ってきたら、それを `design.md` の「未決事項」セクションに転記した上で、ユーザーには「`design.md` の該当セクションを見て決定してほしい」とだけ伝えます。決定が返ってきたら「決定事項」に移し、その内容で実装エージェント（Sonnet）に修正・テスト追加・`impl.md` 更新を委譲します。並列化のメリットはなく、調査→仕様確定→実装の直列で進めます。最後にオーケストレーター側で検収し、エスカレーション事項があれば報告の先頭に置いて要約します。

## 委譲プロンプト（調査エージェント / Opus）

> あなたは調査専門のサブエージェントです。まず `docs/design.md` と `docs/impl.md`（無ければその旨も報告）を読み、以下を調査してください。
> 1. `src/utils/format.ts` の `formatDate` の現状シグネチャ・実装・呼び出し箇所
> 2. 既存のユニットテスト（`src/utils/format.test.ts` など）の場所とテストランナー構成
> 3. `null` 以外の異常系入力（`undefined` / `Invalid Date` / 空文字 / 数値 / 過去の実装での fallback）の扱いに関する仕様上の未決事項の洗い出し
>
> 成果物: 関連ファイルパス、現状の構造の要約、仕様上の未決事項（疑問 / 選択肢 / 各選択肢のトレードオフ / 推奨）。コードは変更しないでください。仕様に関わる判断は自分で下さず、必ず選択肢の形で返してください。境界: 他ファイルの改変・リファクタ禁止。成果物末尾に自身のコンテキスト使用率（概算）を必ず記載し、50% に近づいたらそこまでの成果と未完了リストを明文化して停止してください。

## 委譲プロンプト（実装エージェント / Sonnet、仕様確定後）

> あなたは実装専門のサブエージェントです。まず `docs/design.md` の「決定事項」と `docs/impl.md` を読んでから作業してください。前任者の調査成果物は `<path>` にあります。
>
> タスク: `src/utils/format.ts` の `formatDate` を、`design.md` の決定事項に従い改修する（`null` の場合は空文字を返す。その他の異常系の扱いも決定事項通り）。同時に対応するユニットテストを追加し、完了時に `impl.md` の「実装状況」を更新してください。
>
> 成果物: 変更ファイル一覧、変更概要、テスト実行結果、未解決の疑問。仕様の追加疑問が出た場合は判断せず、疑問と選択肢の形で返してください（`design.md` に反映して再委譲します）。境界: `formatDate` と対応するテスト以外の改変禁止、他関数のリファクタ・依存更新禁止。成果物末尾に自身のコンテキスト使用率（概算）を必ず記載してください。

## テスト方針

実装エージェントに以下のケースを最低限カバーさせます（`design.md` の決定に応じて追加）:

- `null` を渡すと空文字を返す（今回の修正の受け入れ基準）
- 通常の `Date` オブジェクトが従来通りフォーマットされる（回帰防止）
- `undefined` / `Invalid Date` は `design.md` の決定に従う（例: 空文字 or 例外）
- 呼び出し側のフォーマットが崩れていないことを既存テストで確認

```json
{
  "would_delegate": true,
  "delegate_count": 2,
  "parallel_dispatch": false,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "formatDateの現状・既存テスト・null以外の異常系(undefined/Invalid Date)の仕様未決事項を洗い出し、選択肢の形で返させる"},
    {"role_type": "実装", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "design.md決定事項に従いformatDateをnull対応に改修、テスト追加、impl.md更新。範囲外変更禁止"}
  ],
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "writes_to_design_md_as_undecided": true, "asks_user_in_chat_directly": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
