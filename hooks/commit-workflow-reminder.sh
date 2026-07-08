#!/usr/bin/env bash
# PreToolUse hook: git commit の実行直前に commit-workflow スキルを起動させる。
#
# 動作:
#   - Bash ツールのコマンドに "git commit" が含まれる場合のみ反応する
#   - セッション単位のフラグが立っていなければ deny してスキル起動を要求する
#   - フラグが立っていれば allow + additionalContext で規約サマリだけ再掲する
#
# フラグは /tmp/claude-commit-workflow-flags/<session_id> に置く。
# セッションを跨ぐと自動的にリセットされる（/tmp は再起動でクリアされる）。

input=$(cat)

cmd=""
session_id=""
if command -v jq >/dev/null 2>&1; then
  cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
  session_id=$(printf '%s' "$input" | jq -r '.session_id // ""')
else
  cmd=$input
fi

case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

reminder='⚠️ commit-workflow スキルの規約を確認してからコミットすること:\n1. 意味単位ごとに分割（1コミット=1意味単位 / `git add -A`・`git add .` 禁止、ファイルを明示して add）\n2. メッセージ = 英語の1行サマリ + 空行 + 日本語本文\n3. `Co-Authored-By` などのフッター・AIサインを付けない\n4. コミッターは依頼者本人のみ（user.name / user.email を変更しない）\n判断に迷う分割は勝手にまとめず確認を仰ぐ。詳細は commit-workflow スキルを参照。'

# jq が無い / session_id が取れない環境では従来通り allow + context のみで妥協する
if [[ -z "$session_id" ]]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","additionalContext":"%s"}}\n' "$reminder"
  exit 0
fi

flag_dir="/tmp/claude-commit-workflow-flags"
flag_file="${flag_dir}/${session_id}"

if [[ -f "$flag_file" ]]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","additionalContext":"%s"}}\n' "$reminder"
  exit 0
fi

reason='commit-workflow スキル未起動のまま git commit を実行しようとしています。以下を順に実行してください:\n1. Skill ツールで commit-workflow スキルを起動する（引数なしで OK）\n2. スキル起動後、以下のコマンドでセッションフラグを立てる:\n   mkdir -p '"${flag_dir}"' && touch '"${flag_file}"'\n3. その後、改めて git commit を実行する\n\n※ このセッション中はフラグが残るので、以降のコミットで再起動は不要です。'

printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
exit 0
