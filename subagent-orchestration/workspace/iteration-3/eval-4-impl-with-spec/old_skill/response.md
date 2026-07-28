# プラン

私（オーケストレーター）はコードもドキュメントも一切自分で書かず、対話・タスク分解・委譲・検収・エスカレーションだけを担当します。まず調査エージェント（opus）に `docs/features/badges/design.md` と `docs/features/badges/impl.md` を読ませ、「エンドポイントの仕様として確定している事項」「impl.md に方針が書かれている範囲」「design.md から答えが出ない仕様上の疑問」「関連する既存ファイル・既存エンドポイントの構造と制約」を結論だけ返させます（コード変更なし・読み取りのみ）。ここで design.md 由来の仕様疑問が出た場合、または impl.md の方針が `/api/users/:id/badges` の実装に足りない（構成・技術的判断・実装ステップ・コミット分割案が upfront に固まっていない）場合は、実装フェーズには入りません。仕様疑問は選択肢・トレードオフ・推奨を私が design.md の「未決事項」に追記し、チャットでは「design.md の未決事項に判断を記入してください」とだけ伝えて停止します（選択肢やトレードオフをチャットに並べる・「〜で合っていますか」と聞き返すことはしません）。ユーザーが design.md に記入したら読み直して決定事項へ転記し、作業を再開します。impl.md の方針が不足している場合はドキュメントエージェント（opus — 構成・技術的判断を固める判断タスクなので、迷ったら Opus に倒す基準を適用）に upfront で追記させ、書き込みが発生した直後に **author とは別の** ドキュメントレビューエージェント（opus）を即座に走らせます（後回し・自己レビューは禁止）。impl.md の方針が固まった状態を確認してから、実装エージェント（sonnet — design.md と impl.md で仕様と方針が固まっており思考の余地が小さいため）に `/api/users/:id/badges` の実装を委譲し、完了時に impl.md の該当セクションを更新させます。実装完了後は、impl.md 更新分に対するドキュメントレビュー（opus、実装エージェントとは別の新規エージェント）と、コード差分に対するコードレビュー（opus）を依存関係がないので同一ターンで並列起動します。指摘が出たら実装エージェントへ差し戻し、再度 impl.md 更新 → ドキュメントレビューのセットを回します。git の書き込み操作（`git add` / `git commit` 等）は今回のユーザー依頼に含まれておらず、呼び出し側ワークフローのコミット規約も与えられていないため、私からは一切実行せず自発的コミットもしません。ユーザーから「コミットして」と明示指示があった時点でコミットエージェントに委譲します（読み取り系の `git status` / `git diff` は検収材料として私が直接実行します）。最終報告は、エスカレーション（design.md 判断待ち項目）を先頭に置き、その後に変更ファイル一覧・レビュー結果・残課題を要約します。

## 委譲プロンプト（役割 / モデル）

### 1. 調査エージェント（調査 / opus）

> あなたは調査専門エージェントです。コードは一切変更しないでください。
>
> **コンテキスト:** まず `docs/features/badges/design.md`（仕様・要件の source of truth）と `docs/features/badges/impl.md`（実装詳細）を読んでください。今回の対象は `/api/users/:id/badges` エンドポイントの実装です。
>
> **タスク:** 以下を成果物として返してください。
> 1. `/api/users/:id/badges` について design.md で確定している仕様（リクエスト / レスポンス形式、認証・認可、エラー時の挙動、ページネーション有無など）の要約
> 2. impl.md に既に書かれている実装方針の範囲。特に「構成」「技術的判断」「実装ステップ」「コミット分割案」がこのエンドポイントについて upfront に固まっているか、足りない項目はどれかを明示する
> 3. 実装に関係する既存ファイルのパスと現状の構造（ルーティング定義、ハンドラ、データアクセス層、既存の類似エンドポイント、型定義、テストの置き場所）と制約
> 4. design.md から答えが出ない仕様上の疑問のリスト（疑問 / 取り得る選択肢 / 各選択肢のトレードオフ / あなたの推奨）
>
> **エスカレーション指示:** 仕様・要件に関わる疑問は**自分で判断せず**、上記 4 の形式で疑問と選択肢として返してください。「たぶんこうだろう」で仕様を埋めることは禁止です。仕様に影響しない技術的な調査上の判断は自分で行って構いません。
>
> **境界:** コード・ドキュメントの変更、git 操作は一切行わないでください。タスク範囲外の調査に広げないでください。
>
> **コンテキスト管理:** compact は行わないでください。成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。使用率が 50% に近づいたら、そこまでの成果と未完了リストを明文化して停止してください。

### 2. ドキュメントエージェント（ドキュメント / opus）※ impl.md の方針が不足している場合のみ起動

> あなたはドキュメント専門エージェントです。コードは一切変更しないでください。
>
> **コンテキスト:** `docs/features/badges/design.md`（仕様・要件）と `docs/features/badges/impl.md`（実装詳細）を読んでください。前任の調査エージェントの成果物は以下です:
> （調査エージェントの成果物をそのまま貼付）
>
> **タスク:** `/api/users/:id/badges` の実装に着手できる状態まで `docs/features/badges/impl.md` の方針を upfront に固めて追記してください。埋めるべきは「構成（追加・変更するファイルと責務）」「技術的判断（採用する方式とその理由）」「実装ステップ（順序）」「コミット分割案」です。design.md の仕様と矛盾しないこと、design.md の未決事項に該当する内容を勝手に確定させないことを厳守してください。成果物は「更新したセクションと追記内容の要約」です。
>
> **エスカレーション指示:** 仕様・要件に関わる疑問（design.md から答えが出ない選択）が出たら、自分で決めずに「疑問 / 選択肢 / トレードオフ / 推奨」の形で成果物に含めて返してください。仕様に影響しない内部設計・ライブラリの使い方の判断は自分で行い、理由を impl.md に記録してください。
>
> **境界:** コードの変更、git 操作、design.md の仕様の書き換えはしないでください（未決事項の追記も私が行います）。impl.md には「コードを読めばわかること」の書き写しを増やさず、逆に抽象的すぎて実装の現在地が読み取れない記述にもしないでください。
>
> **コンテキスト管理:** compact は行わないでください。成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して停止してください。

### 3. ドキュメントレビューエージェント（ドキュメントレビュー / opus）※ impl.md 書き込み直後に即起動、author とは別エージェント

> あなたはドキュメントレビュー専門エージェントです。あなたは impl.md を書いた author ではありません（author != reviewer を担保するための起用です）。コードもコミットも触らないでください。
>
> **コンテキスト:** `docs/features/badges/design.md` と `docs/features/badges/impl.md` を読んでください。直前に impl.md に `/api/users/:id/badges` の実装方針（構成 / 技術的判断 / 実装ステップ / コミット分割案）が追記されています。
>
> **タスク:** design.md と impl.md の整合をレビューしてください。観点:
> - design.md の決定事項が impl.md の「実装状況」に反映されているか（決定済みなのに未着手扱いの項目が無いか）
> - impl.md の「技術的判断」が design.md の仕様・制約と矛盾していないか
> - design.md の未決事項に該当する内容を impl.md 側で勝手に「実装済み」扱いしていないか
> - design.md の変更履歴と impl.md の記述が同期しているか（旧仕様の記述が残っていないか）
> - impl.md の記述が具体的すぎて「コードを読めばわかること」の書き写しになっていないか、逆に抽象的すぎて実装の現在地が読み取れなくなっていないか
>
> 成果物は「指摘のリスト」で、各指摘に category_hint（仕様乖離 / 記述漏れ / 記述過剰 / 未決先取り / 履歴不整合 のいずれか）＋ 該当箇所のパス ＋ 要約を付けてください。
>
> **エスカレーション指示:** 仕様・要件に関わる疑問は自分で判断せず、疑問と選択肢として返してください。
>
> **境界:** ドキュメントの修正自体は行わないでください（指摘のみ）。コード変更・git 操作は禁止です。
>
> **コンテキスト管理:** compact は行わないでください。成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して停止してください。

### 4. 実装エージェント（実装 / sonnet）

> あなたは実装専門エージェントです。
>
> **コンテキスト:** まず `docs/features/badges/design.md`（仕様・要件。ここに厳密に従うこと）と `docs/features/badges/impl.md`（実装方針。構成・技術的判断・実装ステップが固まっています）を読んでください。前段の調査結果は以下です:
> （調査エージェントの成果物をそのまま貼付）
>
> **タスク:** impl.md の方針に沿って `/api/users/:id/badges` エンドポイントを実装してください。実装ステップの順序も impl.md に従ってください。完了時に `docs/features/badges/impl.md` の該当セクション（構成・実装状況）を更新してください。成果物は「変更ファイル一覧と変更概要、impl.md の更新箇所、未解決の疑問」です。
>
> **エスカレーション指示:** design.md から答えが出ない仕様・要件の疑問（レスポンス形式の細部、認可の扱い、エラーコード、境界値の挙動など）は**自分で決めないでください**。「疑問 / 選択肢 / 各選択肢のトレードオフ / 推奨」の形で成果物に含めて返し、その部分の実装は止めてください。仕様に影響しない内部設計・ライブラリの使い方は自分で判断し、理由を impl.md に記録してください。迷ったらエスカレーションに倒してください。
>
> **境界:** impl.md に書かれた範囲外の変更（無関係なリファクタリング、整形、依存パッケージの更新、design.md の書き換え）はしないでください。**コミットはしないでください** — `git add` / `git commit` などの git 書き込み操作は禁止です。
>
> **コンテキスト管理:** compact は行わないでください。成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら、そこまでの成果と未完了リストを明文化して停止してください（続きは別エージェントが引き継ぎます）。

### 5. ドキュメントレビューエージェント（ドキュメントレビュー / opus）※ 実装後の impl.md 更新分に対して、実装エージェントとは別の新規エージェント

> あなたはドキュメントレビュー専門エージェントです。あなたは impl.md を更新した実装エージェントではありません（author != reviewer の担保）。コードもコミットも触らないでください。
>
> **コンテキスト:** `docs/features/badges/design.md` と `docs/features/badges/impl.md` を読んでください。`/api/users/:id/badges` の実装完了に伴い impl.md の構成・実装状況が更新されています。実装エージェントの成果物は以下です:
> （実装エージェントの成果物をそのまま貼付）
>
> **タスク:** design.md と impl.md の整合をレビューしてください。観点は上記 3 と同一（決定事項の反映漏れ / 技術的判断と仕様の矛盾 / 未決事項の先取り / 履歴の同期 / 記述の粒度）です。成果物は「指摘のリスト（各指摘に category_hint: 仕様乖離 / 記述漏れ / 記述過剰 / 未決先取り / 履歴不整合）＋ 該当箇所のパス ＋ 要約」です。
>
> **エスカレーション指示:** 仕様・要件に関わる疑問は自分で判断せず、疑問と選択肢として返してください。
>
> **境界:** ドキュメントの修正は行わない（指摘のみ）。コード変更・git 操作は禁止です。
>
> **コンテキスト管理:** compact は行わないでください。成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して停止してください。

### 6. コードレビューエージェント（コードレビュー / opus）※ 上記 5 と同一ターンで並列起動

> あなたはコードレビュー専門エージェントです。プロジェクトに code-review-agent スキルがあればそれに従ってください。
>
> **コンテキスト:** `docs/features/badges/design.md`（仕様）と `docs/features/badges/impl.md`（実装方針・実装状況）を読んでください。レビュー対象は `/api/users/:id/badges` 実装の差分です。実装エージェントの成果物は以下です:
> （実装エージェントの成果物をそのまま貼付）
>
> **タスク:** 実装差分をレビューし、指摘リスト（該当ファイル:行 ＋ 内容 ＋ 重大度）を返してください。観点には必ず以下を含めてください。
> - **design.md の仕様との乖離**（レスポンス形式・認可・エラー挙動が仕様どおりか）
> - **impl.md の実装状況との整合**（impl.md の方針・構成どおりに実装されているか、実装状況の記述と実物がずれていないか）
>
> **エスカレーション指示:** 仕様・要件に関わる疑問（design.md から答えが出ない選択）は自分で判断せず、疑問と選択肢として返してください。
>
> **境界:** コードを修正しないでください（指摘のみ）。git 操作は禁止です。
>
> **コンテキスト管理:** compact は行わないでください。成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して停止してください。

## 補足: 起動しない委譲

- **コミットエージェント:** 起動しません。今回のユーザー依頼は実装のみで、コミットの明示指示がなく、呼び出し側ワークフロー（implement-review-loop 等）のコミット契機も与えられていないため、規約にもユーザー指示にも根拠のない自発的コミットは禁止です。ユーザーから明示指示があった時点で委譲します。
- **私が直接実行するもの:** `git status` / `git diff` / `git log` などの読み取り系のみ（検収材料の収集）。書き込み系は一切実行しません。

## 補足: 検収と報告

- 各サブエージェントの成果物末尾のコンテキスト使用率申告を確認し、50% を超えた／近づいたエージェントは続投させず、成果物と未完了リストを明文化させて新規エージェントに引き継ぎます（引き継ぎは会話履歴のコピーではなく design.md / impl.md と成果物経由）。
- レビュー指摘が出たら実装エージェントに差し戻し、impl.md の更新が発生するたびに別エージェントのドキュメントレビューをセットで再実行します。
- 最終報告は「エスカレーション（design.md 判断待ち）」を先頭に置き、以降に変更ファイル一覧・レビュー結果・残課題を要約します。

```json
{
  "would_delegate": true,
  "delegate_count": 6,
  "direct_edit_by_orchestrator": false,
  "parallel_dispatch": true,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "design.md/impl.md と既存構造を読み、確定仕様・impl.md の方針充足度・仕様疑問を結論だけ返す"},
    {"role_type": "ドキュメント", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "impl.md に構成・技術的判断・実装ステップ・コミット分割案を upfront で追記（不足時のみ起動）"},
    {"role_type": "ドキュメントレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "upfront の impl.md 書き込み直後に author 以外が design.md との整合をレビュー"},
    {"role_type": "実装", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "impl.md の方針に沿って /api/users/:id/badges を実装し impl.md の該当セクションを更新（コミット禁止）"},
    {"role_type": "ドキュメントレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "実装後の impl.md 更新分を実装エージェント以外がレビューし category_hint 付き指摘を返す"},
    {"role_type": "コードレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "実装差分を design.md 仕様との乖離・impl.md 実装状況との整合を観点にレビュー"}
  ],
  "docs_flow": {"design_md_checked_or_created": true, "impl_md_created_before_impl_phase": true, "doc_review_by_separate_agent": true},
  "git_writes": {"delegated_to_commit_agent": false, "orchestrator_runs_git_write_directly": false},
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "route": "design_md", "asks_open_ended_qa_in_chat": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
