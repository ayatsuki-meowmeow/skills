#!/usr/bin/env bash
# PreToolUse hook: 秘密ファイルの「閲覧」をツール種別を問わずブロックする。
#
# 背景:
#   permissions.deny の Read(**/.env) 等は Read ツールにしか効かないため、
#   Bash 経由（cat / sed / grep 等）では素通りしてしまう。
#   --dangerously-skip-permissions 下では確認プロンプトも出ないため、
#   このギャップを hook で埋める。
#
# 保護対象のパス:
#   - .env / .env.*（.env.local, .env.production, .env.example なども全て）
#   - .envrc
#   - .ssh/ 配下 / .aws/ 配下
#   - secrets/ 配下
#
# 判定方針:
#   Bash            → 「読み取り系コマンドが保護対象パスを引数に取る」場合のみブロック。
#                     mv / ln / echo などファイル内容を読まない操作は通す。
#                     入力リダイレクト（< path）はコマンド名を問わずブロック。
#   Read/Edit/Write → file_path が保護対象なら常にブロック。引数がパスそのもので
#   Grep/Glob/NotebookEdit  誤検知の余地がないため、こちらは緩めない。
#
# 誤検知を避ける設計:
#   `process.env` や `import.meta.env` は「.env の直前が英数字」なので対象外。
#   `vercel env pull` のようにファイル名を含まないコマンドも対象外。

input=$(cat)

# パス要素の先頭として現れる場合のみマッチさせる。
# 直前に許可する文字: 行頭 / 空白 / クオート / = / / / : / ( / ; / & / <
BOUNDARY='(^|[[:space:]"'"'"'=/:;&(<])'
# 直後に許可する文字: 行末 / 空白 / クオート / ; / | / & / ) / > / <
TAIL='([[:space:]"'"'"';|&)><]|$)'

# 保護対象パスを含むか判定し、含む場合は $secret_reason に理由を立てる
secret_reason=""
detect_secret() {
  secret_reason=""
  [ -z "$1" ] && return 1
  if printf '%s' "$1" | grep -Eq "${BOUNDARY}\.env(\.[A-Za-z0-9_.-]+)?${TAIL}"; then
    secret_reason=".env / .env.* の閲覧は禁止されています（CLAUDE.md: 手段を問わず閲覧禁止）。内容の確認が必要な場合は、ユーザー自身に実行を依頼してください。"
  elif printf '%s' "$1" | grep -Eq "${BOUNDARY}\.envrc${TAIL}"; then
    secret_reason=".envrc の閲覧は禁止されています（CLAUDE.md: 手段を問わず閲覧禁止）。"
  elif printf '%s' "$1" | grep -Eq "${BOUNDARY}\.ssh/"; then
    secret_reason="~/.ssh 配下の閲覧は禁止されています（SSH 秘密鍵）。"
  elif printf '%s' "$1" | grep -Eq "${BOUNDARY}\.aws/"; then
    secret_reason="~/.aws 配下の閲覧は禁止されています（クラウド認証情報）。"
  elif printf '%s' "$1" | grep -Eq "${BOUNDARY}secrets/"; then
    secret_reason="secrets/ 配下の閲覧は禁止されています。"
  fi
  [ -n "$secret_reason" ]
}

# ファイル内容を読み出せるコマンド群。
# 表示系・コピー系・エンコード系・エディタ・インタプリタを含める。
READERS='cat|bat|batcat|less|more|head|tail|tac|rev|nl|sed|awk|grep|egrep|fgrep|zgrep|rg|ag|ack|strings|xxd|od|hexdump|cut|paste|tr|sort|uniq|fold|column|base64|base32|uuencode|openssl|shasum|md5|md5sum|sha1sum|sha256sum|dd|cp|scp|rsync|install|tee|source|\.|eval|exec|vim|vi|view|nvim|nano|emacs|ed|ex|open|code|pbcopy|python|python2|python3|node|deno|bun|ruby|perl|php|jq|yq|dotenv|xargs'

deny() {
  if command -v jq >/dev/null 2>&1; then
    jq -nc --arg r "$1" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $r
      }
    }'
    exit 0
  else
    printf '%s\n' "$1" >&2
    exit 2
  fi
}

# jq が無い環境では判定精度が落ちるため、stdin 全体を検査して安全側に倒す
if ! command -v jq >/dev/null 2>&1; then
  detect_secret "$input" && deny "$secret_reason"
  exit 0
fi

tool=$(printf '%s' "$input" | jq -r '.tool_name // ""')

case "$tool" in
  Bash)
    cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
    [ -z "$cmd" ] && exit 0

    verdict=""
    # ; | & 改行 でセグメントに分割し、各セグメントを個別に判定する。
    # サブシェルでの変数消失を避けるため、プロセス置換ではなくヒアストリングで回す。
    while IFS= read -r seg; do
      [ -z "$seg" ] && continue
      [ -n "$verdict" ] && continue

      # 入力リダイレクトは、コマンド名を問わず内容が読まれるためブロック
      redirect=$(printf '%s' "$seg" | grep -Eo '<[[:space:]]*[^[:space:];|&<>]+' || :)
      if [ -n "$redirect" ] && detect_secret "$redirect"; then
        verdict=$secret_reason
        continue
      fi

      # 先頭コマンド名を取得（VAR=value 形式の環境変数プレフィックスは読み飛ばす）
      name=$(printf '%s' "$seg" | awk '{
        for (i = 1; i <= NF; i++) {
          if ($i !~ /=/) { print $i; exit }
        }
      }')
      [ -z "$name" ] && continue
      name=${name##*/}                              # パス付き指定（/bin/cat）に対応
      name=$(printf '%s' "$name" | tr -d '"'"'"'`') # クオートを除去

      if printf '%s' "$name" | grep -Eq "^(${READERS})$"; then
        if detect_secret "$seg"; then
          verdict=$secret_reason
        fi
      fi
    done <<EOF
$(printf '%s' "$cmd" | tr ';|&\n' '\n\n\n\n')
EOF

    [ -n "$verdict" ] && deny "$verdict"
    ;;

  Read | Edit | Write | MultiEdit)
    target=$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""')
    detect_secret "$target" && deny "$secret_reason"
    ;;
  NotebookEdit)
    target=$(printf '%s' "$input" | jq -r '.tool_input.notebook_path // ""')
    detect_secret "$target" && deny "$secret_reason"
    ;;
  Grep | Glob)
    target=$(printf '%s' "$input" | jq -r '.tool_input.path // ""')
    detect_secret "$target" && deny "$secret_reason"
    ;;
esac

exit 0
