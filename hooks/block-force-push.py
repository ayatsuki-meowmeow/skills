#!/usr/bin/env python3
"""PreToolUse hook: block force push on Bash commands.

force push はリモートの履歴を巻き戻すため、push 済みのコミットや他の人の作業を
消しうる。プロジェクトの事情に関係なく破壊的なので、user スコープで一律に止める。

`permissions.deny` の `Bash(git push --force:*)` は**前方一致**なので
`git -C <path> push --force` / `git --git-dir=... push -f` には当たらない
(2026-09-14 に A/B で実測: `git push ...` は確認が出るが
 `git -C <path> push ...` は無確認で実行された)。グローバル CLAUDE.md が
裸の `cd` を禁じて `git -C <path>` を推奨しているため、規約に従うほどこの穴を通る。

JSON の permissionDecision:"deny" ではなく exit 2 を使うのは、前者が permissions の
allow ルールで上書きされうるため (no-verify-guard.sh と同じ方針)。
"""
import json
import re
import sys

# コマンド中の git 本体 (`mygit` は拾わず、`/usr/bin/git` や `&& git` は拾う)
GIT_TOKEN_RE = re.compile(r"(?:^|[^\w.\-])git(?:\s|$)")
# サブコマンドとしての push (`git -C <path> push` のように挟まっても拾う)
PUSH_TOKEN_RE = re.compile(r"(?:^|\s)push(?:\s|$)")
FORCE_FLAG_RE = re.compile(r"--force(?:-with-lease|-if-includes)?\b")
SHORT_FORCE_RE = re.compile(r"(?:^|\s)-f(?=\s|$)")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = data.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0

    # git と push を独立に検出する (1 本の正規表現だと -C 形を取り逃がす)
    if not GIT_TOKEN_RE.search(command) or not PUSH_TOKEN_RE.search(command):
        return 0

    if not (FORCE_FLAG_RE.search(command) or SHORT_FORCE_RE.search(command)):
        return 0

    sys.stderr.write(
        "force push は禁止です。リモートの履歴を巻き戻すため、push 済みのコミットや\n"
        "他の人の作業を消す可能性があります。\n"
        "やり直したい場合は履歴を書き換えず、新しいコミットを積んで対処してください。\n"
        "どうしても force push が必要な場合は依頼者に判断を仰いでください。\n"
    )
    return 2

if __name__ == "__main__":
    sys.exit(main())
