#!/usr/bin/env bash
# PreToolUse hook: 秘匿ファイルの閲覧・操作をツール種別を問わずブロックする。
#
# ── v1 → v2 の設計変更 (2026-09-04) ────────────────────────────────
# v1 は fail-open だった。「READERS に列挙したコマンド名」かつ「保護パス一致」の
# 両方が揃ったときだけ deny するため、以下が素通りした:
#   - コマンドを起動するコマンド (sh -c / env / find -exec / timeout など)。
#     先頭語が列挙に無いため detect_secret に到達しない
#   - パス名を引数に取らない読み出し (v1 自身が既知の限界として明記)
# コマンド名の列挙は原理的に閉じない。追加し続けても穴は残る。
#
# v2 は判定を fail-closed に反転した:
#   コマンド文字列に保護パスが現れたら、コマンド名も操作種別も問わず deny する。
#
# ── v2 → v3 の設計変更 (2026-09-04) ────────────────────────────────
# 1. 書き込み内容 (content / new_string) も検査対象にした
#    v2 は Write / Edit については file_path しか見ていなかった。そのため
#    「保護ファイルを読むスクリプトを書き出し、`bash <path>` で実行する」経路が
#    素通りした。実行時のコマンド文字列には保護パスが現れないため、v2 の中核である
#    コマンド文字列検査では原理的に捕まらない。
#    同じ内容を Bash のヒアドキュメントで書いた場合は v2 でもブロックされていたため、
#    ツールによって結果が変わる不整合にもなっていた。v3 で挙動を揃える。
#
# 2. テンプレートファイルを保護対象から外した
#    .env.example / .env.sample / .env.template / .env.dist は秘匿値を持たない前提の
#    雛形であり、セットアップ手順の確認に必要になる。v2 はこれらもブロックしていた。
#    トレードオフ: 「.env.example に実値が書かれていた」ケースは見逃す。
#
# ── 方針 (user 確認済み・2026-09-04) ────────────────────────────────
#   - sandbox の中は自由。sandbox の外では秘匿情報を絶対的に保護する
#   - 「閲覧」だけでなく「操作」も対象。v1 が意図的に通していた mv / ln / cp も止める
#   - 存在確認 (ls / test -f / stat) も一律ブロックする。ただし deny メッセージで
#     「有無は判定していない」ことを明示し、ブロックを「ファイルが無い」と誤読して
#     新規作成に走る事故を防ぐ
#   - 判定に迷う入力はブロックする (誤検知より見逃しを嫌う)
#
# ── ブロック手段を exit 2 にした理由 (2026-09-04) ────────────────────
#   JSON の permissionDecision:"deny" は permissions の allow ルールで上書きされうる。
#   exit 2 は権限ルールの評価前にツール呼び出しを止めるため、allow ルールでも覆せない。
#   理由は stderr がそのままモデルに渡るため、伝達力も落ちない。
#   セキュリティ目的の hard block は exit 2 に統一する。
#
# ── この方式の限界 (v1 から共通・解消していない) ────────────────────
#   判定できるのはツール入力の文字列だけ。既にディスク上にあるスクリプトを実行する場合や、
#   setup スクリプトが内部で .env.local を symlink するような場合は検知できない。
#   これはツール呼び出し単位の hook である以上どうにもならない。ファイル権限や
#   サンドボックス隔離など、別レイヤで担保する必要がある。

input=$(cat)

# パス要素の先頭として現れる場合のみマッチさせる。
# 直前に許可する文字: 行頭 / 空白 / クオート / = / / / : / ( / ; / & / <
BOUNDARY='(^|[[:space:]"'"'"'=/:;&(<])'
# 直後は「識別子の continuation でないこと」で判定する。
# 許可文字を列挙する方式（v1）だと glob (`ls .env*`) やブレース展開 (`{.env,.env.local}`)
# が列挙漏れですり抜けるため、英数字と `_` 以外なら何でもマッチさせる否定形にする。
# これにより `.environment` のような別語は引き続き対象外になる（直後が英字なので）。
TAIL='([^A-Za-z0-9_]|$)'

# 秘匿値を持たない前提のテンプレート。検査前に無害な文字列へ置換して対象から外す。
#
# `.env.example` だけでなく `.env.local.example` のような中間セグメント付きも対象にする。
# 置換方式にしているのは、1 つのコマンドに `.env.example` と `.env.local` が同時に
# 現れた場合でも後者を取りこぼさないようにするため。
strip_templates() {
  printf '%s' "$1" | sed -E 's/\.env(\.[A-Za-z0-9_-]+)*\.(example|sample|template|dist)([^A-Za-z0-9_.]|$)/ENV_TEMPLATE\3/g'
}

# 保護対象パスを含むか判定し、含む場合は $secret_reason に種別を立てる。
#
# 誤検知を避ける設計:
#   `process.env` / `import.meta.env` は「.env の直前が英数字」なので BOUNDARY に
#   合致せず対象外。`--env-file` のようなフラグも `.env` の形を取らないため対象外。
#   `credentials` は単語一致にするとコミットメッセージ等で誤爆するため、
#   直前がスラッシュのパス形 (`.aws/credentials` 等) に限定する。
secret_reason=""
detect_secret() {
  secret_reason=""
  [ -z "$1" ] && return 1
  target=$(strip_templates "$1")
  if printf '%s' "$target" | grep -Eq "${BOUNDARY}\.env(\.[A-Za-z0-9_.-]+)?${TAIL}"; then
    secret_reason=".env / .env.* は保護対象です（CLAUDE.md: 手段を問わず閲覧禁止）。テンプレート (.env.example / .sample / .template / .dist) は対象外です。"
  elif printf '%s' "$target" | grep -Eq "${BOUNDARY}\.envrc${TAIL}"; then
    secret_reason=".envrc は保護対象です（CLAUDE.md: 手段を問わず閲覧禁止）。"
  elif printf '%s' "$target" | grep -Eq "${BOUNDARY}\.ssh/"; then
    secret_reason="~/.ssh 配下は保護対象です（SSH 秘密鍵）。"
  elif printf '%s' "$target" | grep -Eq "${BOUNDARY}\.aws/"; then
    secret_reason="~/.aws 配下は保護対象です（クラウド認証情報）。"
  elif printf '%s' "$target" | grep -Eq "${BOUNDARY}secrets/"; then
    secret_reason="secrets/ 配下は保護対象です。"
  elif printf '%s' "$target" | grep -Eq "${BOUNDARY}\.netrc${TAIL}"; then
    secret_reason=".netrc は保護対象です（マシン認証情報）。"
  elif printf '%s' "$target" | grep -Eq "${BOUNDARY}\.git-credentials${TAIL}"; then
    secret_reason=".git-credentials は保護対象です（git 認証トークン）。"
  elif printf '%s' "$target" | grep -Eq "${BOUNDARY}\.npmrc${TAIL}"; then
    secret_reason=".npmrc は保護対象です（レジストリトークンを含みうる）。プロジェクト直下の .npmrc も同様に扱います。"
  elif printf '%s' "$target" | grep -Eq "${BOUNDARY}id_(rsa|dsa|ecdsa|ed25519)"; then
    secret_reason="SSH 秘密鍵ファイル（id_rsa / id_ed25519 等）は保護対象です。"
  elif printf '%s' "$target" | grep -Eq "\.pem${TAIL}"; then
    secret_reason=".pem ファイルは保護対象です（秘密鍵・証明書）。"
  elif printf '%s' "$target" | grep -Eq "/credentials${TAIL}"; then
    secret_reason="credentials ファイルは保護対象です。"
  fi
  [ -n "$secret_reason" ]
}

# deny メッセージ。
#
# 「有無を判定していない」ことを必ず伝える。ブロックされたことを「ファイルが存在しない」
# と誤読すると、「無いので作成します」という誤った次の一手につながる。
# 判定しているのはツール入力の文字列だけで、ファイルシステムは一切見ていない。
deny() {
  printf '%s\n\n%s\n%s\n%s\n' \
    "$1" \
    "重要: この hook はツール入力の文字列だけを見ており、ファイルシステムを参照していません。対象ファイルが存在するかどうかは判定していません。" \
    "「ブロックされた＝ファイルが無い」と解釈しないこと。新規作成・再生成・セットアップのやり直しに進んではいけません。" \
    "存在確認や内容確認が必要な場合は、user 自身に実行を依頼してください。" >&2
  exit 2
}

deny_content() {
  printf '%s\n\n%s\n%s\n' \
    "書き込もうとした内容に保護対象パスが含まれています。$1" \
    "保護ファイルを読むスクリプトを書き出して実行する経路を塞ぐため、書き込み内容も検査しています。この経路でガードレールを迂回してはいけません。" \
    "保護ファイルの確認が必要な場合は、user 自身に実行を依頼してください。" >&2
  exit 2
}

# jq が無い環境では tool_input を取り出せないため、stdin 全体を検査して安全側に倒す
if ! command -v jq >/dev/null 2>&1; then
  detect_secret "$input" && deny "$secret_reason"
  exit 0
fi

tool=$(printf '%s' "$input" | jq -r '.tool_name // ""')

# この hook 自身のソース。content 検査の対象外にする。
#
# 除外しないと、保護パスを説明したコメントを含むこのファイル自体を書き換えられなくなり、
# hook の保守が不可能になる。
#
# これはセキュリティ上の穴にならない。このファイルへの書き込みを許すかどうかに関わらず、
# 書き込める者は hook 本体を無効化できるからである。除外によって新しい能力は増えない。
# 逆に言えば、この hook は「自分自身の改変」を防いでいない。それは別レイヤの課題である。
SELF_PATHS="
/Users/konoreiji/skills/hooks/secret-file-guard.sh
/Users/konoreiji/.claude/hooks/secret-file-guard.sh
"

is_self() {
  case "$SELF_PATHS" in
    *"
$1
"*) return 0 ;;
  esac
  return 1
}

# 書き込み系ツールの「書き込む内容」を集める。
# old_string は既存ファイルの内容であり、無関係な箇所の編集で巻き込まれるため対象外。
written_content() {
  printf '%s' "$input" | jq -r '
    [ .tool_input.content?
    , .tool_input.new_string?
    , .tool_input.new_source?
    , (.tool_input.edits[]?.new_string)?
    ] | map(select(type == "string")) | join("\n")
  '
}

case "$tool" in
  Bash)
    # v2 の中核。コマンド文字列に保護パスが現れたら、コマンド名を問わず deny する。
    # v1 のような READERS 列挙・セグメント分割・git サブコマンドの別枠判定は行わない。
    # 列挙を持たないので、列挙漏れによるすり抜けが構造的に発生しない。
    cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
    [ -z "$cmd" ] && exit 0
    detect_secret "$cmd" && deny "$secret_reason"
    ;;

  Read | Edit | Write | MultiEdit)
    target=$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""')
    detect_secret "$target" && deny "$secret_reason"
    is_self "$target" || { detect_secret "$(written_content)" && deny_content "$secret_reason"; }
    ;;
  NotebookEdit)
    target=$(printf '%s' "$input" | jq -r '.tool_input.notebook_path // ""')
    detect_secret "$target" && deny "$secret_reason"
    is_self "$target" || { detect_secret "$(written_content)" && deny_content "$secret_reason"; }
    ;;
  Grep | Glob)
    target=$(printf '%s' "$input" | jq -r '.tool_input.path // ""')
    detect_secret "$target" && deny "$secret_reason"
    ;;
esac

exit 0
