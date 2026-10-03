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

── プロジェクトごとの追加許可 (2026-10-03) ─────────────────────────
グローバルの ALLOWED_WRITES は厳しいままにし、許可を広げたいプロジェクトだけ
$CLAUDE_PROJECT_DIR/.claude/gh-write-allow.json を置く。中身は次の形式:
  {"allowed_writes": ["issue comment", "issue close"]}
各要素は「サブコマンド サブサブコマンド」の 2 語。ALLOWED_WRITES に足して判定する。
ファイルが壊れている場合は追加許可を全て無視する (fail-closed)。

gh api の書き込みは 2 語では表せないため、api_writes にメソッドとエンドポイントで書く:
  {"api_writes": [{"method": "POST",
                   "path": "repos/<owner>/<repo>/pulls/{number}/comments/{number}/replies"}]}
path は前方一致ではなく全体一致。{number} は数字だけの 1 セグメントに一致する。
{owner}/{repo} のような gh 側のプレースホルダは書けない (実行時のカレントリポジトリ次第で
宛先が変わり、コマンド文字列から宛先を確定できないため)。graphql も書けない。
未知のフラグや --hostname が付いた gh api 呼び出しは、一致を判定しきれないため許可しない。

── この方式の限界 ──────────────────────────────────────────────────
判定できるのはコマンド文字列だけ。スクリプトの中で gh を呼ぶ場合や、
GitHub API を curl/インタプリタから直接叩く場合は検知できない。
"""
import json
import os
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
# issue create も同じ理由で通す (2026-10-03)。既存のリソースを書き換えたり
# 消したりせず、誤って作った場合も削除して戻せる。
#
# READONLY と分けているのは、この集合が「安全だから通している」のではなく
# 「判断の上で通している」ことを読み手に示すため。追加は user の判断を要する。
ALLOWED_WRITES = {
    ("pr", "create"),
    ("issue", "create"),
}

# 値を取る gh のグローバルフラグ。サブコマンド語の抽出時に値ごと読み飛ばす。
FLAGS_WITH_VALUE = {"--repo", "-R", "--hostname"}

# コマンドの区切り。gh の引数列はここで終わる。
SEPARATORS = {"&&", "||", "|", ";", "&", ">", ">>", "<", "2>", "2>&1", "\n"}

# gh api を GET 以外に切り替えるフラグ。1 つでも付いていたら書き込み扱いにする。
API_WRITE_FLAGS = ("-f", "-F", "--field", "--raw-field", "--input")
API_WRITE_METHODS = ("POST", "PATCH", "PUT", "DELETE")

GH_TOKEN_RE = re.compile(r"(^|[^\w./-])gh\b")

# プロジェクトごとの追加許可リスト。$CLAUDE_PROJECT_DIR からの相対パス。
PROJECT_ALLOW_FILE = os.path.join(".claude", "gh-write-allow.json")


# api_writes の path で使えるプレースホルダ。数字 1 つ以上の 1 セグメントに一致する。
API_PATH_NUMBER = "{number}"
# api_writes の path のプレースホルダ以外のセグメント。{owner} などは書けない。
API_PATH_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")

# gh api の引数解析用。ここに無いフラグが付いた呼び出しは追加許可の対象にしない。
API_VALUE_FLAGS = {
    "-X", "--method", "-f", "--raw-field", "-F", "--field", "-H", "--header",
    "--input", "-q", "--jq", "-t", "--template", "--cache", "-p", "--preview",
}
API_BOOL_FLAGS = {"--paginate", "--slurp", "-i", "--include", "--silent", "--verbose"}

# (メソッド, エンドポイントの正規表現) のリスト
ApiWrites = list[tuple[str, re.Pattern[str]]]


def compile_api_path(path: str) -> re.Pattern[str] | None:
    """api_writes の path を正規表現にする。書式が不正なら None を返す。"""
    segments = path.strip("/").split("/")
    if segments[0] == "graphql":
        # graphql は mutation で何でもできるため、プロジェクト単位でも許可しない
        return None
    parts = []
    for seg in segments:
        if seg == API_PATH_NUMBER:
            parts.append(r"\d+")
        elif API_PATH_SEGMENT_RE.match(seg):
            parts.append(re.escape(seg))
        else:
            return None
    return re.compile("^" + "/".join(parts) + "$")


def load_project_allow() -> tuple[set[tuple[str, ...]], ApiWrites, str]:
    """プロジェクトの追加許可を読む。(サブコマンド許可, gh api 許可, 読み込みエラー) を返す。

    ファイルが無ければ空。壊れていれば空とエラー内容を返す。
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return set(), [], ""
    path = os.path.join(project_dir, PROJECT_ALLOW_FILE)
    if not os.path.isfile(path):
        return set(), [], ""

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        return set(), [], f"{path} を読み込めないため、追加許可を無視しました ({e})。"

    if not isinstance(data, dict):
        return set(), [], f"{path} の中身がオブジェクトでないため、追加許可を無視しました。"
    entries = data.get("allowed_writes", [])
    api_entries = data.get("api_writes", [])
    if not isinstance(entries, list) or not isinstance(api_entries, list):
        return set(), [], f"{path} の allowed_writes / api_writes が配列でないため、追加許可を無視しました。"

    writes = set()
    for entry in entries:
        words = tuple(entry.split()) if isinstance(entry, str) else ()
        if len(words) != 2 or words[0] == "api":
            return set(), [], (
                f"{path} の allowed_writes の要素 {entry!r} が「サブコマンド サブサブコマンド」の 2 語でない"
                "(または gh api) ため、追加許可を全て無視しました。"
            )
        writes.add(words)

    api_writes: ApiWrites = []
    for entry in api_entries:
        method = entry.get("method") if isinstance(entry, dict) else None
        api_path = entry.get("path") if isinstance(entry, dict) else None
        pattern = compile_api_path(api_path) if isinstance(api_path, str) else None
        if not isinstance(method, str) or method.upper() not in API_WRITE_METHODS or pattern is None:
            return set(), [], (
                f"{path} の api_writes の要素 {entry!r} が不正なため、追加許可を全て無視しました。"
                f" method は {'/'.join(API_WRITE_METHODS)} のいずれか、path は英数字と ._- の"
                f"セグメントか {API_PATH_NUMBER} だけで書いてください。"
            )
        api_writes.append((method.upper(), pattern))

    return writes, api_writes, ""


def block(reason: str, project_error: str = "") -> int:
    if project_error:
        reason += "\n" + project_error
    sys.stderr.write(
        reason
        + "\n\n"
        + "この hook は、読み取り専用と確認できた gh 操作と、user が明示的に許可した書き込み操作"
        + "だけを通す fail-closed 方式です。判定できなかった操作もここでブロックされます。\n"
        + "GitHub への書き込みが必要な場合は、エージェントの判断で回避せず user 自身に実行を依頼してください。\n"
        + "読み取り専用の操作が誤ってブロックされた場合は "
        + "~/skills/hooks/gh-write-guard.py の READONLY に 1 行追加すれば通ります。\n"
        + "書き込み操作を新たに許可する場合は ALLOWED_WRITES、またはプロジェクトの "
        + PROJECT_ALLOW_FILE
        + " に追加しますが、これは user の判断事項です。\n"
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


def api_request(args: list[str]) -> tuple[str, str] | None:
    """gh api の (メソッド, エンドポイント) を取り出す。

    解析しきれない呼び出し (未知のフラグ・--hostname・エンドポイントが 1 つでない) は
    None を返す。追加許可の照合にだけ使うため、判定できないものは許可しない側に倒す。
    """
    i = args.index("api") + 1 if "api" in args else len(args)
    if any(a == "--hostname" or a.startswith("--hostname=") for a in args[:i]):
        return None

    method = ""
    has_body = False
    positionals = []
    n = len(args)
    while i < n:
        a = args[i]
        name, eq, inline = a.partition("=") if a.startswith("--") else (a, "", "")
        if name in API_VALUE_FLAGS:
            value = inline if eq else (args[i + 1] if i + 1 < n else None)
            if value is None:
                return None
            if name in ("-X", "--method"):
                method = value.upper()
            elif name in ("-f", "--raw-field", "-F", "--field", "--input"):
                has_body = True
            i += 1 if eq else 2
            continue
        if a in API_BOOL_FLAGS:
            i += 1
            continue
        if a.startswith("-"):
            return None
        positionals.append(a)
        i += 1

    if len(positionals) != 1:
        return None
    if not method:
        method = "POST" if has_body else "GET"
    return method, positionals[0].lstrip("/")


def api_write_allowed(args: list[str], api_writes: ApiWrites) -> bool:
    """gh api の書き込みがプロジェクトの api_writes に一致するか。"""
    request = api_request(args)
    if request is None:
        return False
    method, endpoint = request
    return any(method == m and pattern.match(endpoint) for m, pattern in api_writes)


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

    project_writes, project_api_writes, project_error = load_project_allow()
    allowed = READONLY | ALLOWED_WRITES | project_writes

    for args in gh_segments(tokens):
        words = subcommand_words(args)
        if not words:
            # `gh` 単体はヘルプ表示なので通す
            continue

        sub = words[0]

        if sub == "api":
            reason = check_api(args)
            if reason and not api_write_allowed(args, project_api_writes):
                return block(reason, project_error)
            continue

        if sub in READONLY_ANY_SUB:
            continue

        if (sub,) in READONLY:
            continue

        if len(words) > 1 and (sub, words[1]) in allowed:
            continue

        shown = " ".join(words)
        return block(
            f"`gh {shown}` は許可された操作として登録されていないためブロックされました。",
            project_error,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
