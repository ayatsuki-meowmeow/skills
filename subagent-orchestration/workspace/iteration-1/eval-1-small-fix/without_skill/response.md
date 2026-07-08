## プラン

まず `src/utils/format.ts` を Read で開いて、`formatDate` の現状のシグネチャと実装、および周囲のユーティリティの書き方（引数型、返り値、null/undefined の扱いの既存パターン）を確認します。次に Grep で `formatDate(` の呼び出し箇所を列挙して、null 実引数がどこから流れ込んでいるか・呼び出し側が空文字返却を許容できるかをざっと確認します（呼び出し側の型が `Date` に絞られているなら型定義側から先に緩める必要があるため）。テスト状況を把握するため、`src/utils/format.test.ts` などのテストファイルの有無も Glob で確認します。

修正方針としては、関数の先頭で `if (value == null) return "";` の早期 return を入れて null と undefined の両方をハンドリングし、シグネチャを `Date | null | undefined` に広げます。`undefined` を意図的に除外したい場合は既存の型付けに合わせます（Read の結果次第で判断）。この規模（数行）の変更なのでサブエージェントには委譲せず、メインの Claude Code で直接 Edit します。

テスト方針は、`formatDate.test.ts` に (1) 正常系: `Date` を渡すと既存フォーマットの文字列が返る、(2) `null` を渡すと空文字 `""` が返り TypeError を投げない、(3) `undefined` を渡すと空文字 `""` が返る（シグネチャに含める場合）、の 3 ケースを追加します。既存テストがなければ新規に vitest/jest（プロジェクトで使われている方）で作成し、実行して緑を確認します。

仕様として曖昧なのは「undefined も同じ扱いにするか」「空文字ではなく `"-"` などプレースホルダを返すべきか」の 2 点です。これらはユーザーに直接確認してから実装に入ります（勝手に決めない）。

```json
{
  "would_delegate": false,
  "delegate_count": 0,
  "parallel_dispatch": false,
  "delegations": [],
  "spec_ambiguity_handling": {
    "recognized_ambiguity": true,
    "writes_to_design_md_as_undecided": false,
    "asks_user_in_chat_directly": true,
    "decides_alone": false
  },
  "final_report_style": {
    "escalation_at_top": true
  }
}
```
