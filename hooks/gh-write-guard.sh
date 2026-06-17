#!/usr/bin/env bash
# PreToolUse hook: GitHub への書き込み系操作（コメント・マージ）をブロックする。
#
# ブロック対象:
#   - gh pr comment / gh issue comment / gh pr review              (コメント書き込み)
#   - gh pr merge                                                  (PR マージ)
#   - gh api ... --method (POST|PATCH|PUT|DELETE) / -X (...)       (API 経由の書き込み)
#
# jq があればコマンド文字列を正確に抽出し、無ければ stdin 全体に対して部分一致判定する。
# 誤検知側に倒すことで、抜け穴より安全を優先する。

input=$(cat)

if command -v jq >/dev/null 2>&1; then
  cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
else
  cmd=$input
fi

# 空コマンドはスルー
[ -z "$cmd" ] && exit 0

reason=""

# gh CLI のサブコマンドベース判定（前後に空白 / 行頭 / 引用符を許容）
if printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_-])gh[[:space:]]+pr[[:space:]]+comment([[:space:]]|$)'; then
  reason="gh pr comment は禁止されています（GitHub への書き込み操作）。"
elif printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_-])gh[[:space:]]+issue[[:space:]]+comment([[:space:]]|$)'; then
  reason="gh issue comment は禁止されています（GitHub への書き込み操作）。"
elif printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_-])gh[[:space:]]+pr[[:space:]]+review([[:space:]]|$)'; then
  reason="gh pr review は禁止されています（コメント書き込みを含むため）。"
elif printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_-])gh[[:space:]]+pr[[:space:]]+merge([[:space:]]|$)'; then
  reason="gh pr merge は禁止されています（PR マージ操作）。"
elif printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_-])gh[[:space:]]+api([[:space:]]|$)'; then
  # gh api 経由の書き込みメソッド（--method / -X いずれの記法も対象）
  if printf '%s' "$cmd" | grep -Eq '(--method|-X)[[:space:]=]+["'"'"']?(POST|PATCH|PUT|DELETE)'; then
    reason="gh api 経由の書き込みメソッド (POST/PATCH/PUT/DELETE) は禁止されています。"
  fi
fi

if [ -n "$reason" ]; then
  # permissionDecision: deny でツール実行をブロックし、reason をモデルに渡す
  jq -nc --arg r "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $r
    }
  }'
  exit 0
fi

exit 0
