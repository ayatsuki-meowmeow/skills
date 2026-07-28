# プラン

まず自分（オーケストレーター）は対話と意思決定だけを持ち、コードベースの読解は一切自分で抱えない。認証周りの調査は複数ファイル・複数モジュールにまたがり中間出力（grep 結果・差分読解ログ）が大量に出るため「委譲する」側の典型で、観点が実際に独立している 2 系統 — (A) 認証フロー本体（middleware / route handler / セッション・トークン管理 / provider 連携）と (B) 認証状態の消費側（Server/Client Components・API route の認可チェック・型・テスト） — に分け、同一ターンで調査エージェント 2 体を並列起動する（いずれも読解と構造判断が主なので Opus）。着手前に自分の読み取りで `docs/auth/design.md` と `docs/auth/impl.md` の有無を確認する（ここは既知パスの単発参照なので委譲しない）。同時に、依頼文の「リファクタしやすいポイント」は評価軸が未確定という仕様レベルの疑問なので、自己判断で決めずエスカレーションに乗せる。軸の候補は 2〜4 個でトレードオフが 1 行で書ける軽い判断なので AskUserQuestion を 1 往復だけ使い（1 回で閉じなければ design.md ルートに切り替える）、得られた決定は design.md の「決定事項」に必ず記録してから優先度付けに入る。design.md が存在しない場合はその作成と決定事項の記載をドキュメントエージェント（Opus、design.md 執筆は思考寄りのため）に委譲する。現状把握そのものは軸の回答に依存しないので、AskUserQuestion の裏で調査 2 体は先に走らせる。調査成果（ファイルパス・現状構造・制約の要約）を受け取ったら、リファクタ候補の優先度付けと報告はオーケストレーター自身が行う（判断業務であり、検証のための再委譲はしない）。今回は実装フェーズに入らないので impl.md は作成せず、`impl.md` への書き込みが発生しないためドキュメントレビューも起動しない。実装依頼に進む段階になったら、その時点で実装フェーズ前に impl.md を作成し、書き込みとセットで別エージェントによるドキュメントレビューを回す。git は `git log` / `git diff` などの読み取りのみ必要に応じて自分で実行し、書き込み系は今回発生しない（発生する場合も例外なくコミットエージェントに委譲する。ユーザー指示のない自発的コミットはしない）。最終報告はエスカレーション事項を先頭に置き、要約のみをユーザーに返す。

## 委譲プロンプト（役割 / モデル）

### 1. 調査エージェント A — 認証フロー本体（model: opus）

> あなたは Next.js プロジェクトの認証実装を読み解く調査専門エージェントです。
>
> **コンテキスト**
> まず `docs/auth/design.md` と `docs/auth/impl.md` を読んでください（存在しない場合はその旨を成果物に明記し、推測で埋めないこと）。本タスクは既存実装の現状把握であり、仕様変更は含みません。
>
> **タスク**
> 認証フローの「本体」に絞って現状を調査してください。対象範囲:
> - middleware / proxy でのリクエスト遮断・リダイレクト処理
> - ログイン / ログアウト / コールバックの route handler・Server Action
> - セッション・トークンの生成・保存・検証（Cookie 設定、有効期限、リフレッシュ）
> - 認証プロバイダ / ライブラリの利用箇所とバージョン、設定ファイルと環境変数の参照点
>
> 成果物として次を返してください:
> 1. 関連ファイルパスの一覧（役割を 1 行で添える）
> 2. 現状の構造 — 認証リクエストが通る経路を上流から下流へ順に
> 3. 制約の要約 — 外部サービス依存、Runtime 制約（Edge / Node）、暗黙の前提、重複・分散している責務
> 4. 未解決の疑問
>
> **エスカレーション指示**
> 仕様・要件に関わる疑問（「この挙動は意図的か / バグか」「どちらの認証経路が正か」など、既存コードから答えが確定しないもの）は自分で判断せず、疑問と選択肢・トレードオフを成果物として返してください。技術的な読解上の判断（どのファイルから追うか等）は自分で決めて構いません。
>
> **境界**
> - コードは一切変更しない。ファイル作成・修正・整形もしない
> - git 書き込み操作（add / commit / rebase / reset / push）は行わない
> - 調査範囲外（下記エージェント B の担当範囲: コンポーネント側・API route の認可チェック・テスト）には踏み込まない。境界上のファイルは「B 側の担当と思われる」と注記して列挙するだけにとどめる
> - 改善案の実装はしない。気づいた改善余地は「観察」として列挙するだけにする
> - compact が必要な状態になったら続行せず、そこまでの成果と未完了リストを明文化して返す

### 2. 調査エージェント B — 認証状態の消費側（model: opus）

> あなたは Next.js プロジェクトの認証実装を読み解く調査専門エージェントです。
>
> **コンテキスト**
> まず `docs/auth/design.md` と `docs/auth/impl.md` を読んでください（存在しない場合はその旨を成果物に明記し、推測で埋めないこと）。本タスクは既存実装の現状把握であり、仕様変更は含みません。
>
> **タスク**
> 認証状態を「消費する側」に絞って現状を調査してください。対象範囲:
> - Server Components / Client Components が認証状態を取得している経路（Context / hooks / props / server 側関数）
> - API route・Server Action 内の認可チェック（権限判定、ロール、リソース所有者チェック）の実装箇所と重複状況
> - 認証・認可に関わる型定義（ユーザー型、セッション型、権限型）とその分散状況
> - 未認証時の UI 分岐・エラーハンドリング・リダイレクトの扱い
> - 認証周りの既存テストの有無と網羅範囲
>
> 成果物として次を返してください:
> 1. 関連ファイルパスの一覧（役割を 1 行で添える）
> 2. 現状の構造 — 認証状態がどこで取得され、どこで認可判定に使われているか
> 3. 制約の要約 — 同じ認可判定が何箇所に散っているか、型の重複、テストで守られていない箇所
> 4. 未解決の疑問
>
> **エスカレーション指示**
> 仕様・要件に関わる疑問（「この権限判定の抜けは意図的か」「どのロール定義が正か」など、既存コードから答えが確定しないもの）は自分で判断せず、疑問と選択肢・トレードオフを成果物として返してください。技術的な読解上の判断は自分で決めて構いません。
>
> **境界**
> - コードは一切変更しない。ファイル作成・修正・整形もしない
> - git 書き込み操作（add / commit / rebase / reset / push）は行わない
> - 調査範囲外（エージェント A の担当範囲: middleware・セッション/トークン管理・provider 連携）には踏み込まない。境界上のファイルは注記して列挙するだけにとどめる
> - 改善案の実装はしない。気づいた改善余地は「観察」として列挙するだけにする
> - compact が必要な状態になったら続行せず、そこまでの成果と未完了リストを明文化して返す

### 3. ドキュメントエージェント — design.md 作成・決定事項の記録（model: opus。design.md が存在しない場合、または AskUserQuestion の回答が出た時点で起動）

> あなたは design.md を整備するドキュメント専門エージェントです。
>
> **コンテキスト**
> 対象パスは `docs/auth/design.md`（存在しなければ新規作成）と `docs/auth/impl.md`（今回は参照のみ。実装フェーズに入っていないため更新対象外）。まず両パスの有無を確認し、既存があれば読んでから差分だけを足してください。ドキュメントの構成・記載範囲は design-impl-docs スキルの規約に従います。
>
> **タスク**
> 1. 今回のタスク「Next.js プロジェクトの認証実装の現状調査とリファクタ候補の抽出」を design.md に記載する
> 2. ユーザーが AskUserQuestion で選んだ「リファクタの主眼（例: 責務分離 / テスト容易性 / 認証ライブラリ移行の下準備 / セキュリティ境界の明確化）」を **「決定事項」** セクションに、決定内容と選択理由つきで転記する
> 3. 調査で判明した制約のうち、仕様・要件レベルのものだけを design.md に反映する（実装詳細は書かない）
>
> 成果物は「更新したファイルパスと、追記したセクションの要約」。
>
> **エスカレーション指示**
> 記載内容に仕様上の判断が必要になった場合（決定事項の解釈が一意に定まらない、既存 design.md の記述と矛盾する等）は、自分で埋めずに疑問と選択肢を成果物として返してください。
>
> **境界**
> - コードは一切変更しない
> - impl.md は更新しない（実装フェーズに入っていないため）
> - git 書き込み操作は行わない
> - 未決の論点を「決定事項」に先取りして書かない。未決のものは「未決事項」に置く

## 補足: 今回やらないこと

- **impl.md の作成**: 今回は調査と報告までで実装フェーズに入らないため作成しない。ユーザーがリファクタ実装に進む判断をした時点で、実装フェーズ前に必ず impl.md を作成する。
- **ドキュメントレビュー**: `impl.md` への書き込みが発生しないため起動しない。実装フェーズで impl.md に構成・技術的判断を書き込む際は、書いたエージェントとは別のエージェント（reviewer != author）でドキュメントレビューをセットで回す。
- **コミットエージェント**: 今回は git 書き込みが発生しない。発生する場合は規模を問わずコミットエージェントに委譲し、オーケストレーター自身は Bash から git 書き込みを叩かない。
- **成果の再検証目的の追加起動**: しない。調査 2 体の成果の検収と優先度付けはオーケストレーターが直接行う。

```json
{
  "would_delegate": true,
  "delegate_count": 3,
  "direct_edit_by_orchestrator": false,
  "parallel_dispatch": true,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "middleware・セッション/トークン管理・provider 連携など認証フロー本体の現状構造と制約を調査"},
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "コンポーネント・API route の認可チェック・型・テストなど認証状態の消費側を調査"},
    {"role_type": "ドキュメント", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": false, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "design.md を作成し、リファクタの主眼に関するユーザー決定を決定事項へ転記"}
  ],
  "docs_flow": {"design_md_checked_or_created": true, "impl_md_created_before_impl_phase": false, "doc_review_by_separate_agent": false},
  "git_writes": {"delegated_to_commit_agent": false, "orchestrator_runs_git_write_directly": false},
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "route": "ask_user_question", "asks_open_ended_qa_in_chat": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
