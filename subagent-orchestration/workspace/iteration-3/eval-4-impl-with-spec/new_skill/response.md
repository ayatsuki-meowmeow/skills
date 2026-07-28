# プラン

まず私（オーケストレーター）自身が `docs/features/badges/design.md` と `docs/features/badges/impl.md` を読む（既知パスの数回の読み取りは委譲対象外）。ここでの目的は 2 つで、(a) impl.md に実装着手できるレベルの方針が書かれているかの確認、(b) `/api/users/:id/badges` の仕様に design.md から答えの出ない疑問（他ユーザーのバッジ参照可否＝認可、未取得バッジを含めるか、ページネーション・ソート順、404 と空配列の切り分けなど）が残っていないかの確認。impl.md が無い、または方針が空なら**実装フェーズに入る前に**ドキュメントエージェント（Opus）に impl.md 作成を委譲し、その直後に別エージェントでドキュメントレビューを回す。仕様に疑問が見つかった場合は、発生源が私であってもサブエージェントであってもエスカレーションプロトコルに乗せ、後続の実装・レビューに影響する論点（認可・ページネーション等）は design.md の「未決事項」に疑問／選択肢／トレードオフ／推奨を書き、チャットでは「design.md の該当セクションに判断を記入してください」とだけ伝えて停止する（選択肢の中身はチャットに書かない）。選択肢が 2〜4 個でトレードオフが 1 行に収まる軽い判断だけは AskUserQuestion を 1 往復だけ使い、閉じなければ design.md ルートに切り替える。いずれのルートでもユーザーの決定を design.md の「決定事項」に転記してから作業を再開し、口頭合意のまま実装に入らない。仕様が確定したら実装を Sonnet の実装エージェント 1 体に委譲する（複数ファイルに波及し仕様解釈を伴うので直接編集の境界を超える。方針は impl.md に固まっているので Sonnet）。調査エージェントは、impl.md が既存のルーティング・データ取得層の構造まで書けていて実装エージェントが自力で辿れる限り起動しない（委譲プロンプトを書くコストが作業を上回る／中間出力が少ない）。impl.md を読んで既存構造がまったく参照できず広範囲の探索が必要と判明した場合のみ、調査エージェント（Opus）を実装の前段に 1 体挟む。実装エージェントの成果（変更ファイル一覧・impl.md 更新・未解決の疑問）を受け取ったら、依存関係のないレビュー 2 件を同一ターンで並列起動する: 実装エージェントが更新した impl.md に対するドキュメントレビュー（reviewer != author を担保するため実装エージェントとは別の新規エージェント、Opus）と、コード差分に対するコードレビュー（Opus）。両者の指摘を私が検収し、仕様乖離に当たるものは修正を新規の実装エージェントに委譲、仕様そのものへの疑問に化けた指摘は再度エスカレーションプロトコルに戻す。git の書き込み操作は一切自分で実行しない。かつ今回はユーザーからコミット指示が無く、呼び出し側ワークフローの規約もないため、コミットエージェントも起動しない（「実装が終わったのでついでにコミット」は禁止）。ユーザーから `commit して` の指示が来た時点でコミットエージェントに委譲する。最後に、エスカレーション事項を先頭に置いた要約をユーザーに報告する。

## 委譲プロンプト（役割 / モデル）

### 1. 実装エージェント（実装 / sonnet）

> あなたは Web API 実装の専門エージェントです。
>
> **コンテキスト**: まず `docs/features/badges/design.md`（仕様・要件の source of truth）と `docs/features/badges/impl.md`（実装方針・構成・実装状況）を読んでください。実装方針は impl.md に記載済みです。design.md の「決定事項」に書かれている内容が仕様であり、それに厳密に従ってください。
>
> **タスク**: `/api/users/:id/badges` エンドポイントを、design.md の仕様と impl.md の方針に沿って実装してください。完了時に `impl.md` の該当セクション（構成・実装状況、および実装中に行った技術的判断とその理由）を更新してください。impl.md には「コードを読めばわかること」の書き写しではなく、方針と現在地が読み取れる粒度で書いてください。
>
> **成果物**: 変更したファイルの一覧（絶対パス）と各変更の概要、impl.md のどのセクションをどう更新したか、そして未解決の疑問のリスト。最終成果物と未完了項目は必ず明文化して返してください。
>
> **エスカレーション**: design.md から答えが出ない仕様・要件の疑問（例: 他ユーザーのバッジを参照できるのか、未取得バッジを含めるのか、ページネーションやソート順、対象ユーザーが存在しない場合に 404 か空配列か）は、**自分で判断せずに**「疑問 / 取りうる選択肢 / 各選択肢のトレードオフ」の形で成果物に含めて返してください。仮の実装で埋めたり「たぶんこうだろう」で進めたりしないこと。仕様に影響しない内部設計・ライブラリの使い方といった技術的判断は自分で決めてよく、その理由を impl.md に記録してください。
>
> **境界**: design.md / impl.md に書かれたタスク範囲外の変更（無関係なリファクタリング、整形、依存パッケージの更新、テスト方針の変更）は一切行わないでください。`git add` / `git commit` などの git 書き込み操作は禁止です。コンテキストが厳しくなったら compact せず、そこまでの成果と未完了リストを明文化して返してください。

### 2. ドキュメントレビューエージェント（ドキュメントレビュー / opus）

> あなたは design.md と impl.md の整合をレビューする専門エージェントです。impl.md を書いたのは別のエージェントで、あなたは reviewer として起動されています。
>
> **コンテキスト**: `docs/features/badges/design.md` と `docs/features/badges/impl.md` を読んでください。直前に `/api/users/:id/badges` の実装に伴って impl.md が更新されています（実装エージェントの成果物: 変更ファイル一覧と impl.md 更新概要を本プロンプト末尾に添付）。
>
> **タスク**: 以下の観点で design.md と impl.md の整合をレビューしてください。
> - design.md の決定事項が impl.md の「実装状況」に反映されているか（決定済みなのに未着手扱いになっている項目が無いか）
> - impl.md の「技術的判断」が design.md の仕様・制約と矛盾していないか
> - design.md の未決事項に該当する内容を impl.md 側で勝手に「実装済み」扱いしていないか
> - design.md の変更履歴と impl.md の記述が同期しているか（旧仕様の記述が impl.md に残っていないか）
> - impl.md の記述が具体的すぎて「コードを読めばわかること」の書き写しになっていないか、逆に抽象的すぎて実装の現在地が読み取れなくなっていないか
>
> **成果物**: 指摘のリスト。各指摘に `category_hint`（仕様乖離 / 記述漏れ / 記述過剰 / 未決先取り / 履歴不整合 のいずれか）、該当箇所のパス、要約を付けてください。分類の確定と記録は呼び元で行うので、あなたは指摘と category_hint までを返してください。
>
> **エスカレーション**: レビュー中に「そもそも仕様がどちらとも読める」という論点に当たったら、自分で正解を決めずに疑問と選択肢の形で返してください。
>
> **境界**: コードは読んでよいが変更しないこと。design.md / impl.md も**あなたは書き換えないこと**（指摘を返すだけ）。git 操作は一切行わないこと。

### 3. コードレビューエージェント（コードレビュー / opus）

> あなたは実装差分に対するコードレビューの専門エージェントです。実装したのは別のエージェントで、あなたは reviewer として起動されています。プロジェクトに code-review-agent skill があればその規約に従ってください。
>
> **コンテキスト**: `docs/features/badges/design.md`（仕様）と `docs/features/badges/impl.md`（実装方針・実装状況）を読んでから、`/api/users/:id/badges` 実装の差分をレビューしてください（変更ファイル一覧を本プロンプト末尾に添付）。
>
> **タスク**: 差分をレビューし、指摘を返してください。以下は必ず観点に含めてください。
> - **design.md の仕様との乖離**（レスポンス形状、認可・エラー時の挙動、境界条件が仕様どおりか）
> - **impl.md の実装状況との整合**（impl.md の記述と実際のコードがずれていないか）
> あわせて、エラーハンドリング、入力値の扱い、既存コードの規約との一貫性も見てください。
>
> **成果物**: 指摘のリスト（該当ファイルパスと行、深刻度、根拠）。仕様に照らして問題ないと確認できた点も一言で添えてください。
>
> **エスカレーション**: 「仕様がどちらとも読めるため良否を判定できない」ものは、指摘として断定せず疑問と選択肢の形で返してください。
>
> **境界**: コードを修正しないこと（修正は別の実装エージェントに委譲します）。design.md / impl.md を書き換えないこと。git 操作は一切行わないこと。

### 条件付き: 調査エージェント（調査 / opus）— impl.md から既存構造が辿れない場合のみ起動

> あなたはコードベース調査の専門エージェントです。
>
> **コンテキスト**: `docs/features/badges/design.md` と `docs/features/badges/impl.md` を読んでください。impl.md には既存のルーティング・データアクセス層の構造が十分に書かれていないため、実装エージェントに渡す前提情報を集める必要があります。
>
> **タスク**: `/api/users/:id/badges` を追加するために必要な既存構造を調べてください。既存の `/api/users/:id` 系ルートの定義場所と登録方法、認証・認可ミドルウェアの適用パターン、バッジ関連のモデル / クエリ層、レスポンス整形とエラー応答の共通処理、テストの配置と書き方。
>
> **成果物**: 関連ファイルパス、現状の構造の要約、実装時に守るべき制約の一覧。**結論だけを簡潔に**返してください（調査ログの貼り付けは不要）。
>
> **エスカレーション**: 仕様・要件に関する疑問（design.md から答えが出ないもの）は自分で判断せず、疑問と選択肢の形で返してください。
>
> **境界**: コードは一切変更しないこと。design.md / impl.md も更新しないこと。git 操作は行わないこと。

## 補足: 起動しないもの

- **コミットエージェント**: 今回はユーザーからコミット指示がなく、呼び出し側ワークフローの規約もないため起動しない。git 書き込みが必要になった時点で必ずコミットエージェントに委譲し、私自身は `git status` / `git diff` / `git log` の読み取りのみ行う。
- **多重レビューの重ね掛け**: 同じコード差分を同じ観点で複数エージェントに見せることはしない。ドキュメントレビューとコードレビューは観点が独立しているため並列 2 体に留める。
- **自分の判断のダブルチェック用エージェント**: 起動しない。

```json
{
  "would_delegate": true,
  "delegate_count": 3,
  "direct_edit_by_orchestrator": false,
  "parallel_dispatch": true,
  "delegations": [
    {"role_type": "実装", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "design.md の仕様と impl.md の方針に沿って /api/users/:id/badges を実装し impl.md を更新、コミットはしない"},
    {"role_type": "ドキュメントレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "実装エージェントとは別エージェントで design.md と impl.md の整合を 5 観点レビューし category_hint 付き指摘を返す"},
    {"role_type": "コードレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "実装差分を design.md 仕様との乖離・impl.md との整合を含む観点でレビューし指摘のみ返す"}
  ],
  "docs_flow": {"design_md_checked_or_created": true, "impl_md_created_before_impl_phase": true, "doc_review_by_separate_agent": true},
  "git_writes": {"delegated_to_commit_agent": false, "orchestrator_runs_git_write_directly": false},
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "route": "design_md", "asks_open_ended_qa_in_chat": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
