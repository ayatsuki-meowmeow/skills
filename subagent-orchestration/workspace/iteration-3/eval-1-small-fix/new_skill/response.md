# プラン

まず読み取り系だけ自分でやる（`src/utils/format.ts` の `formatDate` を Read、既存テストの有無と lint/typecheck コマンドの確認、`git status` / `git diff` は読み取り例外なので直接実行）。これは「数回のツール呼び出しで完結する読み取り」なので調査エージェントは起動しない。次に design.md の存在を確認し無ければ作成、実装フェーズに入る前に impl.md も必ず作成する — この 2 つはドキュメントエージェント（Sonnet）に委譲する。design.md を書く前に 1 点だけ仕様の疑問がある: 依頼は「null の場合は空文字」だが `undefined` を渡した場合も同じ扱いにするか（TS の型が `Date | null` なのか `Date | null | undefined` なのかで実装が変わり、`== null` と `=== null` のどちらを書くかが決まる）。これは選択肢 2〜3 個・トレードオフが 1 行で書ける軽い判断なので AskUserQuestion で 1 往復だけ聞き、1 回で閉じなければ design.md の「未決事項」ルートへ切り替える。回答は口頭で返ってきた場合も含め必ず design.md の「決定事項」に転記してから先へ進む（転記前に実装しない）。impl.md への方針書き込みが済んだら、reviewer != author を担保するため impl.md を書いたエージェントとは別のドキュメントレビューエージェント（Opus）で design.md / impl.md の整合をレビューする。コード修正そのものは単一ファイル・数行・仕様判断なし（判断は design.md に確定済み）・lint / typecheck で検証が閉じるため「委譲しない」側なので、実装エージェントは起動せず自分で直接編集する。修正後に lint / typecheck / 既存テストを回して緑を確認し、impl.md の「実装状況」を更新する（方針に触れないステータス更新なのでドキュメントレビューの再起動が必要かは design-impl-docs スキルの起動契機に照らして判定し、該当すれば再度レビューを回す）。最後に、`git add` / `git commit` は規模を問わず権限境界の問題として例外なくコミットエージェント（Sonnet）に委譲する。ユーザーが「コミットまで進めて」と明示指示しているのでタイミングの根拠はあり、自発コミットにはならない。順序は「読み取り → 仕様確認（AskUserQuestion → design.md 転記）→ ドキュメント作成 → ドキュメントレビュー → 自分で修正 + 検証 → impl.md 更新 → コミット委譲 → 検収・報告」で、依存が一直線なので並列起動はしない（1 体で足りるところは 1 体にする）。ユーザーへの最終報告はエスカレーション（undefined の扱い、およびテスト追加の可否など残った判断事項）を先頭に置き、その後に変更ファイル・コミットハッシュを要約する。

## 委譲プロンプト（役割 / モデル）

### 1. ドキュメントエージェント（Sonnet）

> あなたはドキュメント専門エージェントです。design.md（仕様・要件）と impl.md（実装詳細）の作成・更新のみを担当し、コードは一切変更しません。
>
> コンテキスト:
> - design.md: `docs/formatDate-null-fix/design.md`（存在しなければ新規作成）
> - impl.md: `docs/formatDate-null-fix/impl.md`（存在しなければ新規作成）
> - ドキュメントの構成・記載範囲・粒度は design-impl-docs スキルの「配置」節に従ってください。まず同スキルを読んでから着手すること。
> - 対象コード: `src/utils/format.ts` の `formatDate`。現状 `null` を渡すと TypeError になります。
> - ユーザーが決めた仕様（すでに確定済み。変更・解釈の追加をしないこと）:
>   - `formatDate(null)` は空文字 `""` を返す
>   - `null` 以外の入力に対する既存挙動は一切変えない
>   - `undefined` の扱い: 「<AskUserQuestion でのユーザー回答をここに転記>」
>
> タスク:
> 1. design.md を作成（または既存なら該当セクションを追記）し、上記の確定仕様を「決定事項」に記載する。`undefined` の扱いの決定は根拠つきで残すこと。未決の論点が残っていれば「未決事項」に分けて書く。
> 2. impl.md を作成し、この修正の構成と方針（どのファイルのどの関数を触るか、ガード節を関数先頭に置く方針、既存の分岐に手を入れない方針、検証手段は lint / typecheck / 既存テスト）を書く。実装は未着手なので「実装状況」は未着手として記載する。
> 3. impl.md は「コードを読めばわかること」の書き写しにならないよう、方針と判断の記録に留めること（実装コードそのものを貼らない）。
>
> 成果物: 作成／更新したファイルのパスと、各ファイルに書いたセクションの見出し一覧、および気づいた未解決の疑問。
>
> エスカレーション: 仕様・要件に関する疑問（design.md から答えが出ない選択）が出たら、**自分で判断せず**、疑問と選択肢・各選択肢のトレードオフを成果物として返してください。オーケストレーターがユーザーへエスカレーションします。技術的な記述粒度の判断は自分で決め、理由を impl.md に残して構いません。
>
> 境界: コードファイル（`src/` 以下）を変更しない。git 操作（add / commit 等）を一切しない。design.md / impl.md 以外のファイルを作らない。このタスク範囲外のドキュメント整備をしない。

### 2. ドキュメントレビューエージェント（Opus）

> あなたは design.md と impl.md の整合をレビューする専門エージェントです。impl.md を書いたエージェントとは別個体として、reviewer != author を担保するために起動されています。
>
> コンテキスト:
> - design.md: `docs/formatDate-null-fix/design.md`
> - impl.md: `docs/formatDate-null-fix/impl.md`
> - まず両ファイルを読んでください。レビュー観点の詳細と起動契機の規約は design-impl-docs スキルの「中核ルール」節に従います。
> - 背景: `src/utils/format.ts` の `formatDate` に `null` ガードを入れる小規模なバグ修正。実装はまだ着手していません。
>
> タスク: 以下の観点で design.md と impl.md の整合をレビューし、指摘を返してください。
> - design.md の決定事項が impl.md の「実装状況」に反映されているか（決定済みなのに未着手扱いになっている項目が無いか）
> - impl.md の「技術的判断」が design.md の仕様・制約と矛盾していないか（特に「null 以外の挙動を変えない」制約に反する方針が書かれていないか）
> - design.md の未決事項に該当する内容を impl.md 側で勝手に「実装済み」扱いしていないか
> - design.md の変更履歴と impl.md の記述が同期しているか（旧仕様の記述が残っていないか）
> - impl.md の記述が具体的すぎて「コードを読めばわかること」の書き写しになっていないか、逆に抽象的すぎて実装の現在地が読み取れなくなっていないか
>
> 成果物: 指摘のリスト。各指摘に category_hint（仕様乖離 / 記述漏れ / 記述過剰 / 未決先取り / 履歴不整合 のいずれか）と該当箇所のパス（行番号があれば併記）と要約を付けてください。指摘が無ければ「指摘なし」と明記してください。
>
> エスカレーション: 仕様・要件そのものに疑問が生じた場合（design.md の決定内容自体が妥当か疑わしい等）は、自分で判断せず疑問と選択肢を成果物に含めて返してください。
>
> 境界: design.md / impl.md を**編集しない**（指摘を返すだけ）。コードを読んでも変更しない。git 操作をしない。コードレビュー（実装差分のレビュー）はこのタスクの範囲外。

### 3. コミットエージェント（Sonnet）

> あなたは未コミット変更を staging → commit する専門エージェントです。git の書き込み操作はあなたに集約されています。
>
> コンテキスト:
> - design.md: `docs/formatDate-null-fix/design.md`
> - impl.md: `docs/formatDate-null-fix/impl.md`
> - まず両ファイルを読み、この変更が何のための修正かを把握してください。
> - 変更内容: `src/utils/format.ts` の `formatDate` に null ガードを追加（null は空文字を返す。null 以外の挙動は不変）＋ 上記 design.md / impl.md の追加・更新（＋テストを追加した場合はそのファイル）。
> - ユーザーから「修正できたらコミットまで進めて」という明示指示が出ています。
> - プロジェクトにコミット規約スキル（例: commit-workflow）があれば必ずそれに従ってください。
>
> タスク: `git status` / `git diff` で差分を確認し、規約に従って staging とコミットを行う。分割単位とメッセージ文言はあなたが決めてください。
>
> 成果物: 作成したコミットのハッシュ、分割の内訳（どのコミットにどのファイルが入ったか）、残った未コミット差分の有無。
>
> エスカレーション: 分割単位やメッセージ文言に迷ったら**自己判断で強行せず**、選択肢を成果物として返してオーケストレーターに委ねてください。履歴書き換え（rebase / reset --hard / push --force）が必要そうに見えた場合も、実行せず報告のみにしてください。
>
> 境界: コードの修正・ファイル追加・整形など、コミット以外の変更を一切加えない。`git push` はしない（指示がありません）。既存コミットの書き換えをしない。

## 仕様エスカレーションの扱い

AskUserQuestion で聞くのは 1 点のみ、1 往復上限。

- 質問: `formatDate` に `undefined` が渡された場合の扱い
- 選択肢例: (a) `undefined` も空文字（`== null` でガード。実質 nullish 全般を吸収する） / (b) `null` のみ空文字、`undefined` は現状維持（`=== null` でガード。依頼文に厳密） / (c) 型定義上 `undefined` は到達しないので考慮不要

回答は design.md の「決定事項」に転記してから実装に入る。1 回で閉じなかった場合（回答が新たな論点を生んだ等）は design.md の「未決事項」に疑問・選択肢・トレードオフ・推奨を書き、チャットでは「design.md の該当セクションに判断を記入してください」とだけ伝えて停止する（選択肢やトレードオフをチャットに書かない）。

## テスト方針

- 修正前に `formatDate` の既存テストファイルの有無を直接 Read で確認する（数回のツール呼び出しで済む読み取りなので委譲しない）。
- 既存テストがある場合: `formatDate(null)` が `""` を返す回帰ケースと、`null` 以外の既存ケースが不変であることを確認するケースを同じテストファイルに追加する。単一ファイル・数行・仕様判断なしなので自分で直接編集する。
- 既存テストが無い／テスト基盤自体が無い場合: テスト基盤の導入は今回の依頼範囲を超える判断なので、自分で決めずに最終報告の先頭でユーザーに判断を仰ぐ（AskUserQuestion の 1 往復は `undefined` の扱いに使うため、こちらは報告での提示に回す）。
- 検証は lint / typecheck / 既存テストスイートで閉じる。すべて緑になってからコミットエージェントを起動する。緑にならなければコミットに進まず、原因を報告する。

## 検収と報告

- ドキュメントレビューの指摘は分類して対応方針を決め、方針に関わる指摘であればドキュメントエージェント（新規個体）に修正を委譲する。
- 各サブエージェントは役目単位で使い切り、役目が終わったら継ぎ足さず新規に委譲する（compact はさせない）。成果物と未解決事項は必ず明文化して返させ、引き継ぎは design.md / impl.md 経由で行う。
- ユーザーへの最終報告は、先頭にエスカレーション（`undefined` の扱いの決定内容、テスト基盤が無い場合の判断依頼、レビュー指摘の未対応分）を置き、続けて変更ファイル一覧・検証結果・コミットハッシュを要約する。

```json
{
  "would_delegate": true,
  "delegate_count": 3,
  "direct_edit_by_orchestrator": true,
  "parallel_dispatch": false,
  "delegations": [
    {"role_type": "ドキュメント", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "design.md を確認/作成して確定仕様を決定事項に記録し、実装フェーズ前に impl.md を作成して方針を書く"},
    {"role_type": "ドキュメントレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "impl.md の author とは別個体で design.md と impl.md の整合をレビューし category_hint 付き指摘を返す"},
    {"role_type": "コミット", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "コミット規約スキルに従って staging とコミットを行い、ハッシュと分割内訳を返す"}
  ],
  "docs_flow": {"design_md_checked_or_created": true, "impl_md_created_before_impl_phase": true, "doc_review_by_separate_agent": true},
  "git_writes": {"delegated_to_commit_agent": true, "orchestrator_runs_git_write_directly": false},
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "route": "ask_user_question", "asks_open_ended_qa_in_chat": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
