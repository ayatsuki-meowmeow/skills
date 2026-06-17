#!/usr/bin/env bash
# PreToolUse hook: git commit の実行直前に commit-workflow スキルの規約をリマインドする。
#
# 動作:
#   - Bash ツールのコマンドに "git commit" が含まれる場合のみ反応する
#   - ツール実行はブロックしない（permissionDecision: allow）
#   - additionalContext で規約サマリを Claude のコンテキストへ注入する
#
# jq があればコマンド文字列を正確に抽出し、無ければ stdin 全体を対象に部分一致判定する
# （誤検知してもリマインドが出るだけで実害はない）。

input=$(cat)

if command -v jq >/dev/null 2>&1; then
  cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
else
  cmd=$input
fi

case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

# additionalContext は1行 JSON 文字列。改行は \n でエンコードしてある。
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","additionalContext":"⚠️ commit-workflow スキルの規約を確認してからコミットすること:\n1. 意味単位ごとに分割（1コミット=1意味単位 / `git add -A`・`git add .` 禁止、ファイルを明示して add）\n2. メッセージ = 英語の1行サマリ + 空行 + 日本語本文\n3. `Co-Authored-By` などのフッター・AIサインを付けない\n4. コミッターは依頼者本人のみ（user.name / user.email を変更しない）\n判断に迷う分割は勝手にまとめず確認を仰ぐ。詳細は commit-workflow スキルを参照。"}}
JSON

exit 0
