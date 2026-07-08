# 実装プラン: ユーザープロフィール画面へのバッジ表示機能

まずリポジトリの構造を把握するため、`ls` と `Read` でプロジェクトルートと `package.json` を確認し、フレームワーク（Next.js / React Native / その他）とプロフィール画面の該当ファイルを特定します。次に `Grep` で `profile` / `Profile` / `user` 関連のコンポーネントとルーティングを検索し、既存のユーザーデータ取得ロジック（API クライアント、型定義、状態管理）を洗い出します。バッジのデータソース（DB スキーマ／API レスポンス）が既存にあるかも確認します。

その上で、以下のコンポーネントを実装します: (1) `Badge` 表示用コンポーネント（アイコン + ラベル + 説明ツールチップ）、(2) `BadgeList` プロフィール画面に配置するコンテナ、(3) ユーザー型定義への `badges` フィールド追加、(4) バッジ取得用の API 呼び出し追加。既存の UI パターン（Tailwind / CSS Modules 等）に合わせてスタイルを揃え、空状態（バッジ 0 個）のフォールバック表示も入れます。

サブエージェントは使わず、Read / Grep / Edit の直接操作でメインコンテキスト内で完結させます。理由は、影響範囲が profile 画面周辺の数ファイルに収まる見込みで、調査と実装を分離するオーバーヘッドの方が大きいためです。実装後、既存のテストがあれば実行し、型チェック（`tsc --noEmit` 相当）を通してから完了報告します。

バッジのアイコン画像は仮のプレースホルダー（絵文字または既存のアイコンライブラリ）を使い、実際のバッジ種別（達成バッジ／ロールバッジ／ランクバッジ等）は既存データに合わせて汎用的に扱えるスキーマにしておきます。

```json
{
  "would_delegate": false,
  "delegate_count": 0,
  "parallel_dispatch": false,
  "delegations": [],
  "spec_ambiguity_handling": {
    "recognized_ambiguity": false,
    "writes_to_design_md_as_undecided": false,
    "asks_user_in_chat_directly": false,
    "decides_alone": true
  },
  "final_report_style": {
    "escalation_at_top": false
  }
}
```
