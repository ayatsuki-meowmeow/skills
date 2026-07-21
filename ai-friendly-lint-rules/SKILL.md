---
name: ai-friendly-lint-rules
description: |
  静的解析用のカスタム lint ルール（ESLint / oxlint / Biome / Ruff / Clippy / RuboCop / PMD / 自作 AST スクリプト等、ツール非依存）を設計するときの規約。AI がエラーメッセージだけを読んでその場で自力修正できる状態を目標に、エラーメッセージの 4 要素・例外パス設計・分類 A〜E に基づく "lint 化 vs skill に残す" 判断・autofix の付け方を統一する。

  TRIGGER when:
  - 新規カスタム lint ルールを設計・実装するとき（ツール種類問わず: ESLint / oxlint / Biome / Ruff / Clippy / RuboCop / PMD / 自作 AST スクリプト等）
  - ルールの `messages` / diagnostic テキスト / 警告文を書く・レビューするとき
  - 既存 lint ルールのエラーメッセージを AI 向けに改善したいとき
  - 「この規約は lint 化すべきか skill に残すべきか」判断を求められたとき
  - autofix を付けるかどうか判断するとき

  SKIP:
  - lint ルールを "動かす" だけの操作（プロジェクト固有の実行手順は別スキルに委譲）
  - Hook / CI / pre-commit / editor 統合の設計（別領域）
  - lint と無関係な設計相談・コード実装
---

# AI-friendly Lint Rules

## 目的

カスタム lint ルールを「AI がエラーメッセージだけを読んで自力で修正できる」形に設計する。skill 経由の説明に頼らず、hook で返した diagnostic 1 発で AI が次に取る行動が決まる状態にする。ツール（ESLint / oxlint / Biome / Ruff / Clippy 等）非依存の設計原則。

## 参照

- ルール本体は `references/rules.md` を参照する。

## 実行手順

1. 作業開始時に `references/rules.md` を読み、対象タスクに該当するセクションへ進む（分類判定 / エラーメッセージ設計 / 例外パス / autofix 判断）。
2. 新規ルールを設計するときは、まず「分類 A〜E」で lint 化に向くかを判定する。E に分類されるものは lint 化せず skill に残す。
3. エラーメッセージを書くときは必ず 4 要素（何が / なぜ / どう直すか / 参考規約名）を満たす。
4. 例外パスは「絶対禁止 / 条件付き許容 / 明示的な逸脱」の 3 段階から選ぶ。
5. autofix は「書き換えが決定的で意味論を変えない」ときのみ付ける。
