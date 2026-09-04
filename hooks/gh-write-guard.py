#!/usr/bin/env python3
"""PreToolUse hook: gh CLI の書き込み系操作をブロックする。

── v1 からの設計変更 (2026-09-04) ──────────────────────────────────
v1 は fail-open だった。「書き込みサブコマンドの列挙」に一致したときだけ deny するため、
以下が素通りした:
  - `gh api graphql`。graphql エンドポイントはメソッド指定なしで POST であり、
    mutation でコメント投稿・マージ・ラベル操作が全て通った
  - `gh api <endpoint> -f key=value`。-f/-F/--field/--input のいずれかが付くと
    gh はメソッドを POST に切り替えるが、v1 は --method/-X しか見ていなかった
  - pr create / pr edit / pr close / issue 系 / release create / label など、
    列挙に載っていない書き込みサブコマンド全般
書き込みサブコマンドの列挙は gh のバージョンアップで増え続けるため原理的に閉じない。

v2 は判定を fail-closed に反転する:
  読み取り専用と確認できた gh 操作だけを通し、それ以外は全て deny する。
  (secret-file-guard v2 と同じ方針)

── ブロック手段を exit 2 にした理由 (2026-09-04) ────────────────────
JSON の permissionDecision:"deny" は permissions の allow ルールで上書きされうる。
exit 2 は権限ルールの評価前にツール呼び出しを止めるため、allow ルールでも覆せない。
理由は stderr がそのままモデルに渡る。セキュリティ目的の hard block は exit 2 に統一する。

── この方式の限界 ──────────────────────────────────────────────────
判定できるのはコマンド文字列だけ。スクリプトの中で gh を呼ぶ場合や、
GitHub API を curl/インタプリタから直接叩く場合は検知できない。
"""
import json
import re
import shlex
import sys

# 読み取り専用と確認できた gh 操作。(サブコマンド, サブサブコマンド) で指定する。
# 1 語で完結する操作は (サブコマンド,) の 1 要素タプルで指定する。
# 追加は 1 行で済む。迷うものは載せない (fail-closed なので載せなければ deny)。
READONLY = {
    ("status",),
    ("version",),
    ("help",),
    ("browse",),
    ("auth", "status"),
    ("pr", "view"),
    ("pr", "list"),
    ("pr", "diff"),
    ("pr", "checks"),
    ("pr", "status"),
    ("issue", "view"),
    ("issue", "list"),
    ("issue", "status"),
    ("repo", "view"),
    ("repo", "list"),
    ("run", "view"),
    ("run", "list"),
    ("run", "watch"),
    ("run", "download"),
    ("release", "view"),
    ("release", "list"),
    ("release", "download"),
    ("label", "list"),
    ("workflow", "view"),
    ("workflow", "list"),
    ("cache", "list"),
    ("gist", "view"),
    ("gist", "list"),
    ("ruleset", "view"),
    ("ruleset", "list"),
    ("org", "list"),
    ("project", "view"),
    ("project", "list"),
    ("project", "item-list"),
    ("project", "field-list"),
    ("variable", "list"),
    ("extension", "list"),
    ("alias", "list"),
    ("config", "get"),
    ("config", "list"),
    ("codespace", "list"),
    ("attestation", "verify"),
}

# 第 2 語を問わず全て読み取り専用のサブコマンド
READONLY_ANY_SUB = {"search"}

# 読み取り専用ではないが、user が明示的に許可した書き込み操作 (2026-09-04)。
#
# pr create は GitHub 上に新しいリソースを作る外向きの操作であり、読み取りではない。
# それでも通すのは、PR 作成が user のワークフローの一部であり、既存のリソース
# (コメント欄・PR 本文・マージ状態・ラベル) を書き換えないためである。
# comment / review / edit / merge / close との違いはそこにある。
#
# READONLY と分けているのは、この集合が「安全だから通している」のではなく
# 「判断の上で通している」ことを読み手に示すため。追加は user の判断を要する。
ALLOWED_WRITES = {
    ("pr", "create"),
}

# 値を取る gh のグローバルフラグ。サブコマンド語の抽出時に値ごと読み飛ばす。
FLAGS_WITH_VALUE = {"--repo", "-R", "--hostname"}

# コマンドの区切り。gh の引数列はここで終わる。
SEPARATORS = {"&&", "||", "|", ";", "&", ">", ">>", "<", "2>", "2>&1", "\n"}

# gh api を GET 以外に切り替えるフラグ。1 つでも付いていたら書き込み扱いにする。
API_WRITE_FLAGS = ("-f", "-F", "--field", "--raw-field", "--input")
API_WRITE_METHODS = ("POST", "PATCH", "PUT", "DELETE")

GH_TOKEN_RE = re.compile(r"(^|[^\w./-])gh\b")


def block(reason: str) -> int:
    sys.stderr.write(
        reason
        + "\n\n"
        + "この hook は、読み取り専用と確認できた gh 操作と、user が明示的に許可した書き込み操作"
        + "だけを通す fail-closed 方式です。判定できなかった操作もここでブロックされます。\n"
        + "GitHub への書き込みが必要な場合は、エージェントの判断で回避せず user 自身に実行を依頼してください。\n"
        + "読み取り専用の操作が誤ってブロックされた場合は "
        + "~/skills/hooks/gh-write-guard.py の READONLY に 1 行追加すれば通ります。\n"
        + "書き込み操作を新たに許可する場合は ALLOWED_WRITES に追加しますが、これは user の判断事項です。\n"
    )
    return 2


def gh_segments(tokens: list[str]) -> list[list[str]]:
    """トークン列から gh 呼び出しごとの引数列を切り出す。"""
    segments = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok == "gh" or tok.endswith("/gh"):
            args = []
            i += 1
            while i < n and tokens[i] not in SEPARATORS:
                args.append(tokens[i])
                i += 1
            segments.append(args)
            continue
        i += 1
    return segments


def subcommand_words(args: list[str]) -> list[str]:
    """引数列から先頭 2 語のサブコマンドを取り出す。グローバルフラグは値ごと読み飛ばす。"""
    words = []
    i = 0
    n = len(args)
    while i < n and len(words) < 2:
        a = args[i]
        if a in FLAGS_WITH_VALUE:
            i += 2
            continue
        if a.startswith("-"):
            # --repo=owner/name のような = 記法、および値を取らないフラグ
            i += 1
            continue
        words.append(a)
        i += 1
    return words


def check_api(args: list[str]) -> str:
    """gh api が読み取り専用かどうかを判定する。書き込みなら理由を返す。"""
    words = subcommand_words(args)
    endpoint = words[1] if len(words) > 1 else ""

    if endpoint == "graphql":
        return (
            "gh api graphql は禁止されています。"
            "graphql エンドポイントはメソッド指定が無くても POST であり、"
            "mutation でコメント投稿・マージ・ラベル操作が実行できるためです。"
        )

    for idx, a in enumerate(args):
        if a in API_WRITE_FLAGS or a.split("=", 1)[0] in API_WRITE_FLAGS:
            return (
                f"gh api の書き込みフラグ ({a.split('=', 1)[0]}) は禁止されています。"
                "gh api はこれらのフラグが付くとメソッドを POST に切り替えます。"
            )
        if a in ("--method", "-X") or a.startswith("--method="):
            value = a.split("=", 1)[1] if "=" in a else (args[idx + 1] if idx + 1 < len(args) else "")
            if value.strip("\"'").upper() in API_WRITE_METHODS:
                return f"gh api の書き込みメソッド ({value}) は禁止されています。"

    return ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # 入力が読めない場合はブロックしない (hook 起因で作業を止めない)
        return 0

    command = data.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0

    # gh を含まないコマンドは対象外。ここで抜けることで shlex の失敗が
    # 無関係なコマンドに波及しないようにする。
    if not GH_TOKEN_RE.search(command):
        return 0

    try:
        tokens = shlex.split(command, comments=True)
    except ValueError:
        return block("gh を含むコマンドを解析できませんでした (クオートが閉じていない可能性があります)。")

    for args in gh_segments(tokens):
        words = subcommand_words(args)
        if not words:
            # `gh` 単体はヘルプ表示なので通す
            continue

        sub = words[0]

        if sub == "api":
            reason = check_api(args)
            if reason:
                return block(reason)
            continue

        if sub in READONLY_ANY_SUB:
            continue

        if (sub,) in READONLY:
            continue

        if len(words) > 1 and (sub, words[1]) in READONLY | ALLOWED_WRITES:
            continue

        shown = " ".join(words)
        return block(
            f"`gh {shown}` は許可された操作として登録されていないためブロックされました。"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
