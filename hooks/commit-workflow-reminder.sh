#!/usr/bin/env bash
# PreToolUse hook: commit-workflow スキルを起動せずに git commit することを防ぐ。
#
# 動作:
#   - Bash ツールのコマンドに "git commit" が含まれる場合のみ反応する
#   - セッションフラグが立っていなければ exit 2 でブロックし、スキル起動を要求する
#   - フラグが立っていれば規約サマリだけ additionalContext で再掲して通す
#
# フラグは commit-workflow-flag.sh (PostToolUse:Skill) が立てる。この hook は
# フラグを読むだけで、立て方をエージェントに指示しない。
#
# ── v1 からの設計変更 (2026-09-04) ──────────────────────────────────
# 1. 自己申告フラグをやめた
#    v1 は deny メッセージの中でエージェント自身に `touch` を指示していたため、
#    スキルを起動せず touch だけすればゲートを素通りできた。フラグを立てる責務を
#    commit-workflow-flag.sh に移し、ハーネス側の Skill 呼び出し検知に紐付けた。
#
# 2. permissionDecision:"allow" を返すのをやめた
#    v1 はフラグが立っているとき allow を返していた。リマインダが権限を付与しており、
#    "git commit" を含むだけの任意のコマンドに承認が付く形になっていた。
#    通す場合は何も決定せず additionalContext だけを返す (権限判断はエンジンに委ねる)。
#
# 3. ブロックを exit 2 に変更
#    JSON の permissionDecision:"deny" は permissions の allow ルールで上書きされうる。
#    exit 2 は権限ルールの評価前に止まるため覆せない。stderr がそのまま理由として渡る。

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

emit_reminder() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}\n' "$reminder"
  exit 0
}

# jq が無い / session_id が取れない環境ではフラグを判定できない。
# ゲートを掛けると恒久的にコミット不能になるため、リマインダのみで妥協する。
if [ -z "$session_id" ]; then
  emit_reminder
fi

flag_file="/tmp/claude-commit-workflow-flags/$(basename "$session_id")"

if [ -f "$flag_file" ]; then
  emit_reminder
fi

cat >&2 <<'REASON'
commit-workflow スキルを起動しないまま git commit を実行しようとしています。

Skill ツールで commit-workflow スキルを起動してから（引数なしで可）、改めて git commit を実行してください。
スキルが起動すると PostToolUse hook がセッションフラグを立てるため、以降このセッション中は再起動不要です。

フラグを手動で作成してこのゲートを回避してはいけません。ゲートの目的はコミット規約を実際に読ませることであり、
フラグはその結果を記録しているに過ぎません。
REASON
exit 2
