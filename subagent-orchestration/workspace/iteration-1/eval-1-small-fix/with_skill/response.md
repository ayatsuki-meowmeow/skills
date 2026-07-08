## プラン

まず `docs/format/design.md` と `docs/format/impl.md` の有無を確認し、なければ「`formatDate` の入力仕様と null/undefined/無効値の扱い」を骨子とする最小限のドラフトを作成します（作成自体も実装エージェントに委譲可）。次に本件は小さいバグ修正ですが、規模を問わず委譲する規約に従い、**実装エージェント（Sonnet）を 1 つ**起動して `src/utils/format.ts` の `formatDate` を「引数が `null` の場合は空文字を返す」形に修正し、あわせてテスト方針（null / 通常の Date / 通常の文字列の 3 ケース、既存テストの回帰）を成果物として返させます。実装中に「`undefined` や `NaN` を含む Date、パース不能な文字列も空文字にするのか、それとも従来通り例外にするのか」という **仕様の空白** が出た場合、サブエージェントには自分で決めさせず、疑問と選択肢を成果物に含めさせ、私が design.md の「未決事項」に転記してからユーザーへ確認します。境界として「今回のスコープ外（他関数のシグネチャ変更・型再設計・関係ないリファクタ）は触らない」ことと、「完了後に impl.md の該当箇所を更新する」ことを委譲プロンプトに明示します。並列化するタスクは無いため単一委譲、モデルは仕様が固まっている定型修正なので Sonnet を選びます。委譲プロンプトの末尾で自身のコンテキスト使用率（概算 %）を必ず自己申告させ、50% に近づいたら成果物と未完了リストを明文化して停止するよう指示します。最終報告ではエスカレーション事項（undefined/NaN の扱い等）を先頭に置き、ユーザーの判断を仰いでから作業を再開します。

### 実装エージェントへの委譲プロンプト（本文）

```
あなたは実装の専門エージェントです（TypeScript）。

# コンテキスト
- 対象: /absolute/path/to/repo/src/utils/format.ts の formatDate 関数
- 症状: null を渡すと TypeError が発生する
- 仕様/実装ドキュメント:
  - docs/format/design.md（仕様・要件。無ければ最小ドラフトを作成して差分を返す）
  - docs/format/impl.md（実装詳細。作業後に必ず更新する）
- まずこの 2 ファイルと src/utils/format.ts、関連テスト（例: src/utils/__tests__/format.test.ts）を読むこと。

# タスク
1. formatDate に対して「引数が null の場合は空文字 '' を返す」を実装する。
2. テスト方針を提示し、最低限のユニットテストを追加する:
   - null → ''（回帰防止）
   - 有効な Date → 既存フォーマット
   - 既存のケース（文字列入力など）が壊れていないこと
3. impl.md の formatDate セクションを更新する（挙動・null ハンドリング理由）。

# エスカレーション指示（重要）
- design.md から答えが出ない仕様の空白に直面したら、自分で決めない。以下は仕様の空白として必ず疑問リストに返すこと:
  - undefined を渡された場合は空文字か、それとも例外か
  - Invalid Date（NaN 内部値）を渡された場合の扱い
  - パース不能な文字列を渡された場合の扱い
- 上記に触れる修正は、私（オーケストレーター）から追加指示があるまで保留し、null のみ対応で止めてよい。

# 境界（やらないこと）
- 他関数のシグネチャ変更、型定義の再設計、関係ないリファクタ、依存追加
- 既存テストの挙動変更（回帰確認のみ）

# 成果物として返すもの
- 変更ファイル一覧と diff サマリ
- 追加/変更したテストと実行結果
- 未解決の疑問（あれば、選択肢とトレードオフ付き）
- 末尾に「自身のコンテキスト使用率: 約 XX%」を必ず記載。50% に近づいたら成果物と未完了リストを明文化して停止すること。
```

```json
{
  "would_delegate": true,
  "delegate_count": 1,
  "parallel_dispatch": false,
  "delegations": [
    {
      "role_type": "実装",
      "model": "sonnet",
      "prompt_mentions_design_md": true,
      "prompt_mentions_impl_md": true,
      "prompt_mentions_context_self_report": true,
      "prompt_mentions_escalation_boundary": true,
      "prompt_requires_impl_md_update": true,
      "prompt_summary": "formatDate の null 引数を空文字返却に修正し、null/有効Date/既存ケースのテストを追加、impl.md 更新。undefined/NaN/パース不能文字列の扱いは未決事項として返す。境界とコンテキスト自己申告付き。"
    }
  ],
  "spec_ambiguity_handling": {
    "recognized_ambiguity": true,
    "writes_to_design_md_as_undecided": true,
    "asks_user_in_chat_directly": false,
    "decides_alone": false
  },
  "final_report_style": {
    "escalation_at_top": true
  }
}
```
