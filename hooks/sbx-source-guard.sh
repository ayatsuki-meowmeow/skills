#!/usr/bin/env bash
# PreToolUse hook: サンドボックスへの資材持ち込み元をミラーに限定する。
#
# 方針 (user 確認済み・2026-09-04):
#   sandbox の中には「見られていいもの・壊れていいもの」だけを持ち込む。
#   koshu 本体を clone 元にすると .env.local などの秘匿ファイルが箱に入るため、
#   持ち込み元は koshu-mirror に限定する。ミラーは koshu の clone なので
#   .env を構造的に持たない (memory: offload-mirror-architecture)。
#
# これまでこの制限は implementation-offload スキルの規約でしか担保されておらず、
# 機構としては存在しなかった。規約は読み飛ばされうるので hook に落とす。
#
# 対象は `sbx create` のみ。start / stop / run / ports / rm は資材を持ち込まないため通す。
#
# ── ブロック手段を exit 2 にした理由 (2026-09-04) ────────────────────
#   JSON の permissionDecision:"deny" は permissions の allow ルールで上書きされうる。
#   exit 2 は権限ルールの評価前に止まるため覆せない。stderr がそのまま理由として渡る。
#
# ── この方式の限界 ──────────────────────────────────────────────────
#   塞いでいるのは `sbx create` の clone 元だけ。docker cp / rsync / 箱の中からの
#   git clone といった別経路は検知できない。「箱の外から中への正規経路」を
#   ミラーに固定するためのものであり、資材流入の全経路を塞ぐものではない。

MIRROR_PATH="/Users/konoreiji/koshu-mirror"

input=$(cat)

if command -v jq >/dev/null 2>&1; then
  cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
else
  cmd=$input
fi

[ -z "$cmd" ] && exit 0

# sbx の create 以外は対象外
printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_./-])sbx([[:space:]]|$)' || exit 0
printf '%s' "$cmd" | grep -Eq '(^|[[:space:]])create([[:space:]]|$)' || exit 0

# clone 元がミラーなら通す。それ以外は誤検知側に倒して止める。
case "$cmd" in
  *"$MIRROR_PATH"*) exit 0 ;;
esac

cat >&2 <<EOF
サンドボックスへの持ち込み元は ${MIRROR_PATH} に限定されています。
koshu 本体を clone 元にすると .env.local などの秘匿ファイルが箱に入ります。ミラーは koshu の clone なので .env を持たず、秘匿値が渡らないことが構造的に保証されます。

正しい形:
  sbx create --clone claude ${MIRROR_PATH} --name {サンドボックス名}

注意: この hook はコマンド文字列だけを見ており、ファイルシステムを参照していません。ミラーが存在するかどうかは判定していません。
EOF
exit 2
