# プラン

規模が小さい修正でも直接実装はせず、全ての作業を専門サブエージェントに委譲する（オーケストレーターがやるのは分解・委譲・検収・エスカレーション・報告だけ。`git status` / `git diff` / `git log` などの読み取り系 git だけは意思決定材料として自分で叩く）。まず (A) 調査エージェント（Opus）に `src/utils/format.ts` の `formatDate` の現状シグネチャ・呼び出し元・既存テストを洗わせ、同一ターンで (B) ドキュメントエージェント（Opus）に design.md の存在確認と無ければ作成を委譲する（この 2 つは依存関係がないので並列起動）。design.md 作成時点で仕様の穴が 1 つある — 依頼は「null なら空文字」だが `undefined` と invalid Date（`new Date("xxx")`）の扱いが決まっておらず、`formatDate` の引数型が `Date` なら型変更の是非も仕様判断になる。これはサブエージェントにもオーケストレーター自身にも判断させず、選択肢・トレードオフ・推奨を design.md の「未決事項」に書かせ、チャットでは「design.md の未決事項に判断を記入してください」とだけ伝えて停止する（選択肢やトレードオフはチャットに一切並べない）。ユーザーが design.md に記入したら決定を読み取って「決定事項」へ転記し、作業を再開する。再開後は実装フェーズに入る前に必ず impl.md を upfront 作成する — 構成・技術的判断・実装ステップ・コミット分割案までドキュメントエージェント（Sonnet）に固めさせ、書き込みが発生した直後に**別エージェント**のドキュメントレビュー（Opus）をセットで走らせる（author != reviewer、後回し・自己レビューは禁止）。指摘が解消してから実装エージェント（Sonnet: 方針が impl.md まで落ちているので思考の余地が小さい）に委譲し、完了時に impl.md の実装状況を更新させる。その更新分についても再び別エージェントのドキュメントレビュー（Opus）をセットで走らせ、並行してコードレビューエージェント（Opus）に「design.md の仕様との乖離」「impl.md との整合」観点でレビューさせる。コミットは今回ユーザーが「コミットまで進めて」と明示しているので根拠あり — ただしオーケストレーター自身は `git add` / `git commit` を打たず、コミットエージェント（Sonnet）に委譲し、分割単位・メッセージ文言はそちらに決めさせる（迷えばユーザーへエスカレーション）。最後にコミットハッシュと残差分の有無を検収し、エスカレーション事項を先頭に置いた要約をユーザーに報告する。各委譲プロンプトには共通要素（役割 / コンテキスト＝design.md・impl.md のパスと「まず読め」/ タスク / エスカレーション指示 / 境界）と、コンテキスト使用率の自己申告・50% 接近時の停止規約を必ず含める。50% 申告が出たら成果物と未完了リストを明文化させて新規エージェントへ引き継ぐ。

## 委譲プロンプト（役割 / モデル）

### 1. 調査エージェント（Opus） — (A)、(B) と同一ターンで並列起動

> あなたはコードベース調査の専門エージェントです。コードは一切変更しないでください。
>
> コンテキスト: このタスクの仕様書は `docs/design.md`、実装詳細は `docs/impl.md` です。存在すれば作業前に必ず両方読んでください（この時点では未作成の可能性があります）。
>
> タスク: `src/utils/format.ts` の `formatDate` について以下を調べ、要約だけを返してください。
> 1. `formatDate` の現在のシグネチャ（引数の型、戻り値の型）と実装本体
> 2. `null` を渡したときに TypeError が発生する具体的な箇所（どの行のどのプロパティ/メソッドアクセスか）
> 3. `formatDate` の全呼び出し元のファイルパスと、そこで渡している値の型（`null` / `undefined` が流れ込む経路があるか）
> 4. 既存のテストファイルの有無とパス、`formatDate` に対する既存ケースの一覧
> 5. 同ファイル内の他の format 関数が null をどう扱っているか（既存の慣習）
>
> 成果物: 「関連ファイルパス・現状の構造・制約の要約」。コードの全文貼り付けはせず、判断に必要な要約に絞ってください。
>
> エスカレーション指示: 仕様・要件に関わる疑問（`undefined` や invalid Date をどう扱うべきか等、コードを読んでも答えが出ない選択）が出た場合、自分で判断せず「疑問 + 選択肢」の形で成果物に含めて返してください。オーケストレーターがユーザーへエスカレーションします。
>
> 境界: コード・ドキュメント・git のいずれも変更しないこと。調査範囲を `formatDate` とその呼び出し元・テストに限定し、無関係なリファクタリング提案をしないこと。
>
> コンテキスト管理: 成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。使用率が 50% に近づいたら、そこまでの成果と未完了リストを明文化して作業を止めてください（compact はしないこと）。

### 2. ドキュメントエージェント / design.md（Opus） — (B)、(A) と同一ターンで並列起動

> あなたは design.md / impl.md を管理するドキュメント専門エージェントです。コードは一切変更しないでください。
>
> コンテキスト: 仕様書は `docs/design.md`、実装詳細は `docs/impl.md` です。まず両方の存在を確認し、あれば読んでください。ドキュメントの書式・セクション構成は design-impl-docs スキルの規約に従ってください。
>
> タスク:
> 1. `docs/design.md` が無ければ作成する。ユーザーの依頼「`src/utils/format.ts` の `formatDate` に `null` を渡すと TypeError が出る。`null` の場合は空文字を返す。`null` 以外の入力の挙動は変えない」を仕様・要件として記述する。
> 2. 「未決事項」セクションに以下の疑問を、疑問 / 選択肢 / 各選択肢のトレードオフ / 推奨 の形で追記する。
>    - 疑問: `null` 以外の欠損値・不正値の扱いをどうするか
>    - 観点: (a) `undefined` を渡された場合も空文字にするか、従来通り TypeError のままにするか (b) invalid Date（`new Date("xxx")` 等）は今回の対象外とするか (c) 引数型が `Date` の場合、`Date | null` に広げるか（呼び出し元の型チェックに影響する）
>    - 各選択肢のトレードオフと推奨を必ず併記する
>
> 成果物: 作成/更新したファイルのパスと、追記した未決事項の見出し一覧のみ。判断内容の要約はチャット報告用に整形しないでください（design.md が source of truth です）。
>
> エスカレーション指示: 仕様を自分で決めないでください。答えの出ない選択は「未決事項」に選択肢と推奨を書くところまでで止め、決定は書き込まないこと。
>
> 境界: コード・git のいずれも変更しない。design.md の記述はユーザー依頼の範囲に限定し、依頼に無い機能要件を追加しないこと。
>
> コンテキスト管理: 成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して止めてください（compact 禁止）。

**この時点でユーザーへエスカレーション（停止）**。チャットでの発話は「`docs/design.md` の未決事項に『null 以外の欠損値・不正値の扱い』を追記しました。判断を記入してください」のみ。選択肢・トレードオフ・推奨はチャットに書かない。記入後、design.md を読み直して決定を検出し、未決事項 → 決定事項の転記（docs スキル規約に従う）を済ませてから以下を再開する。

### 3. ドキュメントエージェント / impl.md upfront 作成（Sonnet）

> あなたは impl.md を管理するドキュメント専門エージェントです。コードは一切変更しないでください。
>
> コンテキスト: 仕様書は `docs/design.md`、実装詳細は `docs/impl.md` です。まず `docs/design.md` を必ず読み、「決定事項」に転記済みの決定（`null` の扱い、`undefined` / invalid Date / 引数型の扱い）を確認してください。調査エージェントの成果物は以下です（オーケストレーターが要約を貼付）: <調査結果の要約>
>
> タスク: 実装フェーズに入る前の `docs/impl.md` を作成（既にあれば該当セクションを更新）する。含めるもの:
> 1. 対象ファイルと構成（`src/utils/format.ts` の `formatDate`、および必要ならテストファイル）
> 2. 技術的判断とその理由（早期 return か型ガードか、既存の他 format 関数の慣習に合わせるか）
> 3. 実装ステップ（何を何の順で変えるか）
> 4. コミット分割案（意味単位での分割方針）
> 5. 実装状況（この時点では全て未着手）
>
> 記述粒度: 「コードを読めばわかること」の書き写しにならないよう、かつ実装の現在地が読み取れる程度に保つこと。
>
> 成果物: 更新したパスと、追加したセクションの見出し一覧。
>
> エスカレーション指示: design.md から答えが出ない仕様の疑問は自分で決めず、疑問と選択肢を成果物として返すこと（オーケストレーターがユーザーへエスカレーションします）。仕様に影響しない内部設計の判断は自分で決め、理由を impl.md に記録してよい。
>
> 境界: コード・git のいずれも変更しない。design.md の未決事項に該当する内容を impl.md 側で勝手に確定させないこと。依頼範囲外の改善提案を書かないこと。
>
> コンテキスト管理: 成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して止めてください（compact 禁止）。

### 4. ドキュメントレビューエージェント（Opus） — 3 の直後に必ずセットで起動（author != reviewer）

> あなたは design.md と impl.md の整合をレビューする専門エージェントです。コードもコミットも触らず、ドキュメントの書き換えもしないでください（指摘を返すだけ）。
>
> コンテキスト: `docs/design.md` と `docs/impl.md` を必ず両方読んでください。impl.md は別のエージェントが upfront 作成したものです。
>
> タスク: 以下の観点でレビューする。
> - design.md の決定事項が impl.md の「実装状況」に反映されているか（決定済みなのに未着手扱いになっている項目が無いか）
> - impl.md の「技術的判断」が design.md の仕様・制約と矛盾していないか
> - design.md の未決事項に該当する内容を impl.md 側で勝手に「実装済み」扱いしていないか
> - design.md の変更履歴と impl.md の記述が同期しているか（旧仕様の記述が残っていないか）
> - impl.md の記述が具体的すぎて「コードを読めばわかること」の書き写しになっていないか、逆に抽象的すぎて実装の現在地が読み取れなくなっていないか
>
> 成果物: 指摘のリスト。各指摘に `category_hint`（仕様乖離 / 記述漏れ / 記述過剰 / 未決先取り / 履歴不整合 のいずれか）と該当箇所のパス・要約を付けること。指摘ゼロならその旨を明記。
>
> エスカレーション指示: 仕様そのものへの疑問（design.md で決まっていない事項）を見つけたら、自分で結論を出さず疑問と選択肢を成果物に含めて返すこと。
>
> 境界: ファイルを書き換えない。コードレビューはしない（今回はコード未変更）。
>
> コンテキスト管理: 成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して止めてください（compact 禁止）。

### 5. 実装エージェント（Sonnet）

> あなたは実装専門エージェントです。design.md の仕様に厳密に従ってください。
>
> コンテキスト: 仕様書は `docs/design.md`、実装詳細は `docs/impl.md` です。作業前に必ず両方読み、design.md の「決定事項」と impl.md の「技術的判断」「実装ステップ」に従ってください。
>
> タスク: `src/utils/format.ts` の `formatDate` を修正し、`null` を渡した場合に TypeError ではなく空文字を返すようにする。`null` 以外の入力の挙動は一切変えないこと（`undefined` / invalid Date の扱いは design.md の決定事項に従う）。impl.md のコミット分割案に沿って変更を作り、完了時に `docs/impl.md` の「実装状況」セクションを更新すること。
>
> 成果物: 「変更ファイル一覧と変更概要、未解決の疑問」。
>
> エスカレーション指示: design.md から答えが出ない仕様の疑問（例: 想定外の呼び出し元が見つかり挙動が変わりうる）は自分で判断せず、疑問と選択肢を成果物として返して作業を止めること。仕様に影響しない内部設計の判断は自分で行い、理由を impl.md に記録すること。
>
> 境界: `formatDate` の `null` 対応以外の変更は一切しないこと（周辺コードの整形・リネーム・他関数の改善・依存更新・未使用コード削除は禁止）。コミットはしないこと（`git add` / `git commit` を実行しない）。
>
> コンテキスト管理: 成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して止めてください（compact 禁止）。

### 6. コードレビューエージェント（Opus） — 7 と同一ターンで並列起動

> あなたはコードレビュー専門エージェントです。実装差分に対するレビューを行い、コードは変更しないでください。詳細な進め方は code-review-agent スキルに従ってください。
>
> コンテキスト: 仕様書は `docs/design.md`、実装詳細は `docs/impl.md` です。まず両方読んでから差分を見てください。レビュー対象は `src/utils/format.ts` の `formatDate` の `null` 対応差分（およびテスト差分があればそれも）です。
>
> タスク: 以下を必ず観点に含めてレビューする。
> - design.md の仕様との乖離（`null` → 空文字、`null` 以外の挙動不変が守られているか）
> - impl.md の「実装状況」との整合
> - `undefined` / invalid Date の扱いが design.md の決定と一致しているか
> - 型定義の変更が呼び出し元に与える影響
>
> 成果物: 指摘のリスト（該当箇所のパス・行、深刻度、要約）。指摘ゼロならその旨を明記。
>
> エスカレーション指示: 仕様レベルの疑問は自分で結論を出さず、疑問と選択肢を成果物に含めて返すこと。
>
> 境界: コード・ドキュメント・git のいずれも変更しない（修正提案は文章で返すのみ）。レビュー範囲を今回の差分に限定し、既存コードの無関係な改善提案をしないこと。
>
> コンテキスト管理: 成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して止めてください（compact 禁止）。

### 7. ドキュメントレビューエージェント（Opus） — 5 の impl.md 更新分に対して必ずセットで起動、6 と並列

> あなたは design.md と impl.md の整合をレビューする専門エージェントです。コードもコミットも触らず、ドキュメントの書き換えもしないでください（指摘を返すだけ）。実装エージェントが更新した `docs/impl.md` のレビューであり、あなたはその author ではありません。
>
> コンテキスト: `docs/design.md` と `docs/impl.md` を必ず両方読んでください。実装エージェントの成果物（変更ファイル一覧と変更概要）は以下です: <実装成果物の要約>
>
> タスク: 以下の観点でレビューする。
> - design.md の決定事項が impl.md の「実装状況」に反映されているか（`null` → 空文字対応が完了として記載されているか）
> - impl.md の「技術的判断」が design.md の仕様・制約と矛盾していないか
> - design.md の未決事項に該当する内容を impl.md 側で勝手に「実装済み」扱いしていないか
> - design.md の変更履歴と impl.md の記述が同期しているか（旧仕様の記述が残っていないか）
> - impl.md の記述が具体的すぎて「コードを読めばわかること」の書き写しになっていないか、逆に抽象的すぎて実装の現在地が読み取れなくなっていないか
>
> 成果物: 指摘のリスト。各指摘に `category_hint`（仕様乖離 / 記述漏れ / 記述過剰 / 未決先取り / 履歴不整合 のいずれか）と該当箇所のパス・要約を付けること。
>
> エスカレーション指示: 仕様そのものへの疑問は自分で結論を出さず、疑問と選択肢を成果物に含めて返すこと。
>
> 境界: ファイルを書き換えない。コードレビューはしない（コードの中身の良否は別のコードレビューエージェントが担当）。
>
> コンテキスト管理: 成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して止めてください（compact 禁止）。

### 8. コミットエージェント（Sonnet） — 6 / 7 の指摘が解消してから

> あなたは未コミット変更を staging → commit する専門エージェントです。
>
> コンテキスト: 仕様書は `docs/design.md`、実装詳細は `docs/impl.md` です。まず両方読み、impl.md の「コミット分割案」を確認してください。プロジェクトにコミット規約スキル（例: commit-workflow）があればそれに厳密に従ってください。ユーザーは今回「修正できたらコミットまで進めてください」と明示的にコミットを指示しています。
>
> タスク: `formatDate` の `null` 対応差分（および impl.md / design.md の更新分）を impl.md の分割案に沿って staging し、コミットする。分割単位とメッセージ文言はあなたが決めてください。
>
> 成果物: 「作成したコミットのハッシュ・分割の内訳・残った未コミット差分の有無」。
>
> エスカレーション指示: 分割単位やメッセージ文言に迷った場合、自己判断で強行せず疑問と選択肢を成果物として返して止めること（オーケストレーターがユーザーへエスカレーションします）。想定外の未コミット差分（今回の修正と無関係なファイル）を見つけた場合も、勝手に含めず・勝手に捨てず、報告して止めること。
>
> 境界: 範囲外の変更（コード修正・ファイル追加・整形）は一切加えないこと。`git push` / `git rebase` / `git reset` などの履歴書き換え・リモート操作は行わないこと（ユーザー確認が別途必要）。
>
> コンテキスト管理: 成果物の末尾に自身のコンテキスト使用率（概算でよい）を必ず記載してください。50% に近づいたら成果物と未完了リストを明文化して止めてください（compact 禁止）。

## テスト方針

テストの追加是非も仕様判断に寄るため、`docs/design.md` の記述（および未決事項への回答）に従う。design.md でテスト追加が要件に含まれた場合は impl.md の実装ステップに「`formatDate(null)` が空文字を返すケース」「既存の非 null ケースが不変であることのリグレッションケース」を明記し、実装エージェントの担当範囲に含める（調査エージェントが特定した既存テストファイルに追記する形）。design.md でテスト不要と決まった場合は追加せず、実装エージェントには「テストを増やさない」ことを境界として明示する。いずれの場合も検収時に既存テストスイートの結果をコミット前に確認し、実行できていない場合はその事実をユーザー報告に明記する。

## 検収とユーザー報告

コードレビュー / ドキュメントレビューの指摘は、implement-review-loop 側の分類ステップに合流させて処理する。ユーザーへの最終報告は、エスカレーション事項（design.md の未決事項への判断待ち、コミットエージェントが止まった場合の判断待ち）を**先頭**に置き、その後にコミットハッシュ・変更概要・残差分の有無を要約する。エスカレーション内容そのもの（選択肢・トレードオフ）はチャットに書かず、design.md へのポインタのみを示す。

```json
{
  "would_delegate": true,
  "delegate_count": 8,
  "direct_edit_by_orchestrator": false,
  "parallel_dispatch": true,
  "delegations": [
    {"role_type": "調査", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "formatDate の現状実装・TypeError 発生箇所・呼び出し元・既存テストを調査させる"},
    {"role_type": "ドキュメント", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "design.md を確認/作成し、undefined・invalid Date・引数型の扱いを未決事項として選択肢+推奨付きで追記させる"},
    {"role_type": "ドキュメント", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "実装フェーズ前に impl.md を upfront 作成（構成・技術的判断・実装ステップ・コミット分割案）"},
    {"role_type": "ドキュメントレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "upfront 作成した impl.md を author とは別エージェントで即レビュー（category_hint 付き指摘）"},
    {"role_type": "実装", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": true, "prompt_summary": "formatDate の null → 空文字修正を実施し impl.md の実装状況を更新（コミットはしない）"},
    {"role_type": "コードレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "実装差分を design.md 仕様乖離・impl.md 整合の観点でレビュー"},
    {"role_type": "ドキュメントレビュー", "model": "opus", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "実装エージェントによる impl.md 更新分を別エージェントでレビュー"},
    {"role_type": "コミット", "model": "sonnet", "prompt_mentions_design_md": true, "prompt_mentions_impl_md": true, "prompt_mentions_context_self_report": true, "prompt_mentions_escalation_boundary": true, "prompt_requires_impl_md_update": false, "prompt_summary": "impl.md のコミット分割案に沿って staging→commit、分割・文言に迷えばエスカレーション"}
  ],
  "docs_flow": {"design_md_checked_or_created": true, "impl_md_created_before_impl_phase": true, "doc_review_by_separate_agent": true},
  "git_writes": {"delegated_to_commit_agent": true, "orchestrator_runs_git_write_directly": false},
  "spec_ambiguity_handling": {"recognized_ambiguity": true, "route": "design_md", "asks_open_ended_qa_in_chat": false, "decides_alone": false},
  "final_report_style": {"escalation_at_top": true}
}
```
