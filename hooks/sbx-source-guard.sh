#!/usr/bin/env bash
# PreToolUse hook: サンドボックスへの資材の持ち込み元を許可リストに限定する。
#
# ── 目的 ────────────────────────────────────────────────────────────
# サンドボックスの中には「見られていいもの・壊れていいもの」だけを持ち込む。
# 業務リポジトリをそのまま clone 元にすると、gitignore された秘匿ファイル
# (認証情報を含む設定ファイル等) が箱に入る。持ち込み元をミラーなどの
# 「秘匿ファイルを構造的に持たないコピー」に限定することで、秘匿値が渡らない
# ことを構造的に保証する。
#
# ── 設定 ────────────────────────────────────────────────────────────
# 許可する clone 元は環境変数で与える。マシンごとに違うため、このリポジトリには
# 実装だけを置き、パスは各マシンの設定に持たせる。
#
#   SBX_CLONE_SOURCE_ALLOWLIST  必須。許可する clone 元の絶対パスを ":" 区切りで指定。
#                               未設定なら この hook は何もしない (exit 0)。
#   SBX_CLONE_SOURCE_HINT       任意。deny メッセージの末尾に追記する補足文。
#                               正しいコマンド例などをマシン固有で出したい場合に使う。
#
# 設定込みの具体版を使いたい場合は、各マシンの ~/.claude/hooks に置く。
# このファイルは汎用実装であり、固有のパスやプロジェクト名を含めない。
#
# ── 対象 ────────────────────────────────────────────────────────────
# `sbx create` のみ。start / stop / run / ports / rm は資材を持ち込まないため通す。
#
# ── ブロック手段を exit 2 にした理由 ────────────────────────────────
# JSON の permissionDecision:"deny" は permissions の allow ルールで上書きされうる。
# exit 2 は権限ルールの評価前に止まるため覆せない。stderr がそのまま理由として渡る。
#
# ── この方式の限界 ──────────────────────────────────────────────────
# 塞いでいるのは `sbx create` の clone 元だけ。docker cp / rsync / 箱の中からの
# git clone といった別経路は検知できない。「箱の外から中への正規経路」を
# 許可リストに固定するためのものであり、資材流入の全経路を塞ぐものではない。
# また判定はコマンド文字列の部分一致であり、許可パスが引数以外の位置に
# 現れた場合も通してしまう。

[ -n "${SBX_CLONE_SOURCE_ALLOWLIST:-}" ] || exit 0

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

# clone 元が許可リストのいずれかなら通す。それ以外は誤検知側に倒して止める。
saved_ifs=$IFS
IFS=':'
for allowed in $SBX_CLONE_SOURCE_ALLOWLIST; do
  [ -n "$allowed" ] || continue
  case "$cmd" in
  *"$allowed"*)
    IFS=$saved_ifs
    exit 0
    ;;
  esac
done
IFS=$saved_ifs

{
  printf '%s\n' "サンドボックスへの持ち込み元が許可リストに含まれていません。"
  printf '%s\n' "業務リポジトリをそのまま clone 元にすると、gitignore された秘匿ファイルが箱に入ります。秘匿ファイルを構造的に持たないコピーを clone 元にしてください。"
  printf '\n%s\n' "許可されている clone 元:"
  IFS=':'
  for allowed in $SBX_CLONE_SOURCE_ALLOWLIST; do
    [ -n "$allowed" ] && printf '  %s\n' "$allowed"
  done
  IFS=$saved_ifs
  [ -n "${SBX_CLONE_SOURCE_HINT:-}" ] && printf '\n%s\n' "$SBX_CLONE_SOURCE_HINT"
  printf '\n%s\n' "注意: この hook はコマンド文字列だけを見ており、ファイルシステムを参照していません。許可パスが存在するかどうかは判定していません。"
} >&2
exit 2
