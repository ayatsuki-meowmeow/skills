#!/usr/bin/env python3
"""PreToolUse hook: ask for confirmation before any git push.

push はリモートを書き換えるため、実行前に確認を挟む。
`permissions.ask` の `Bash(git push:*)` は**前方一致**なので
`git -C <path> push ...` / `git --git-dir=... push ...` には当たらず、
`defaultMode: "auto"` に落ちて無確認で通る
(2026-09-14 に A/B で実測: `git push ...` は確認が出るが
 `git -C <path> push ...` は無確認で実行された)。グローバル CLAUDE.md が
裸の `cd` を禁じて `git -C <path>` を推奨しているため、規約に従うほどこの穴を通る。
ask ルールでは可変長のオプション列を表現できないので hook 側で補う。

force push の遮断は block-force-push.py の担当 (あちらは exit 2 の deny)。
"""
import json
import re
import sys

# コマンド中の git 本体 (`mygit` は拾わず、`/usr/bin/git` や `&& git` は拾う)
GIT_TOKEN_RE = re.compile(r"(?:^|[^\w.\-])git(?:\s|$)")
# サブコマンドとしての push (`git -C <path> push` のように挟まっても拾う)
PUSH_TOKEN_RE = re.compile(r"(?:^|\s)push(?:\s|$)")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # 入力が読めない場合は確認を挟まない (hook 起因で作業を止めない)
        return 0

    command = data.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0

    if not GIT_TOKEN_RE.search(command) or not PUSH_TOKEN_RE.search(command):
        return 0

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                "git push はリモートを書き換えるため確認します。"
                "push 先のブランチと、積まれているコミットが意図どおりか確かめてください。"
            ),
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
