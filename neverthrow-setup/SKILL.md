---
name: neverthrow-setup
description: |
  Use this skill when a user wants to introduce or bootstrap neverthrow into a TypeScript project.
  Key triggers: asking to add/install/setup neverthrow, wanting to create AppError discriminated
  union types from scratch, creating AppResult/AppResultAsync type aliases, building fromFetch or
  fromDb helper functions, or configuring eslint-plugin-neverthrow. Also trigger when the user
  asks "where do I start with neverthrow" or describes their stack (e.g., uses Prisma, fetch) and
  wants neverthrow wired in. This is a first-time setup skill — skip only when neverthrow is
  already fully configured and the user wants help implementing specific features or reviewing
  existing code (use neverthrow-coding-rules skill instead).
---

# neverthrow Setup

## 目的

TypeScript プロジェクトに neverthrow を初導入する際の、パッケージ導入・`AppError` 判別共用体・`E` 必須の型エイリアス・`fromXxx` ヘルパー・eslint 設定を一括でセットアップする。

## 参照

- セットアップ手順本体は `references/rules.md` を参照する。

## 実行手順

1. 作業開始時に `references/rules.md` を読み、5 ステップ（インストール → AppError → 型エイリアス → fromXxx → eslint）の全体像を把握する。
2. ユーザーのパッケージマネージャ・エラー種別・外部境界（fetch / DB / 外部 SDK 等）をヒアリングしてから生成する。
3. `references/rules.md` の各ステップに沿って、ファイル作成・コマンド案内を順に行う。
4. セットアップ完了後の運用は `neverthrow-coding-rules` スキルに引き継がれる旨をユーザーに伝える。
