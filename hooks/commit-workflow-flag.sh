#!/usr/bin/env bash
# PostToolUse hook: commit-workflow スキルが実際に起動したことを記録する。
#
# ── 存在理由 (2026-09-04) ────────────────────────────────────────────
# commit-workflow-reminder.sh v1 は、deny メッセージの中でエージェント自身に
# 「スキルを起動してからフラグを touch しろ」と指示していた。つまりゲートの通過が
# エージェントの自己申告に依存しており、スキルを起動せず touch だけすれば
# 恒久的に素通りできた。機構ではなく honor system になっていた。
#
# この hook はフラグをエージェントの外側から立てる。Skill ツールの呼び出しを
# ハーネスが検知して発火するため、エージェントは「起動していないのに起動したことにする」
# ことができない。
#
# PreToolUse ではなく PostToolUse を使う理由:
#   PreToolUse は呼び出しの直前に発火するため、スキルのロードが失敗した場合にも
#   フラグが立ってしまう。PostToolUse ならスキルが実際にロードされた後に発火する。
#
# フラグは /tmp/claude-commit-workflow-flags/<session_id> に置く。
# セッションを跨ぐと自動的にリセットされる (/tmp は再起動でクリアされる)。

input=$(cat)

command -v jq >/dev/null 2>&1 || exit 0

tool=$(printf '%s' "$input" | jq -r '.tool_name // ""')
[ "$tool" = "Skill" ] || exit 0

skill=$(printf '%s' "$input" | jq -r '.tool_input.skill // ""')
case "$skill" in
  commit-workflow|*:commit-workflow) ;;
  *) exit 0 ;;
esac

session_id=$(printf '%s' "$input" | jq -r '.session_id // ""')
[ -n "$session_id" ] || exit 0

# session_id にパス区切りが混ざる想定は無いが、念のため基底名だけを使う
session_id=$(basename "$session_id")
[ -n "$session_id" ] || exit 0

flag_dir="/tmp/claude-commit-workflow-flags"
mkdir -p "$flag_dir" 2>/dev/null || exit 0
touch "${flag_dir}/${session_id}" 2>/dev/null || exit 0

exit 0
