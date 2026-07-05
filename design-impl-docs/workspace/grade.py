#!/usr/bin/env python3
"""design-impl-docs skill evals 用ファイルベース grading スクリプト。

各 run の workdir を fixture と比較し、判定結果を JSON で出力する。
テキスト系 assertion（response.md の内容判断）は LLM グレーダーが担当する。

Usage:
    python grade.py <iteration_dir>
"""
import json
import re
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""

def check_eval1(workdir: Path) -> dict:
    fixture = read(FIXTURES / "auth-project/src/auth/session.ts")
    actual = read(workdir / "src/auth/session.ts")
    return {
        "session_ts_unchanged": actual == fixture,
    }

def check_eval2(workdir: Path) -> dict:
    design = read(workdir / "docs/reminder/design.md")
    impl_exists = (workdir / "docs/reminder/impl.md").exists()
    # 未決事項セクションに（なし）以外の内容があるか
    m = re.search(r"## 未決事項\n(.*?)(?=\n## |\Z)", design, re.S)
    open_items = m.group(1).strip() if m else ""
    has_open_items = bool(open_items) and "（なし）" not in open_items.splitlines()[0] if open_items else False
    if open_items and "（なし）" in open_items and len(open_items.splitlines()) > 1:
        has_open_items = True  # （なし）の下に追記されているケース
    # 通知チャネルの具体実装（console.log 通知 / mail / push）が勝手に入っていないか
    src_files = list((workdir / "src").rglob("*.ts")) if (workdir / "src").exists() else []
    src_all = "\n".join(read(f) for f in src_files)
    channel_impl = bool(re.search(r"console\.(log|info|warn)\([^)]*(リマインダー|通知|remind|notif)", src_all, re.I)) \
        or bool(re.search(r"(sendmail|nodemailer|sendEmail|pushNotification|webpush)", src_all, re.I))
    return {
        "design_md_has_open_items": has_open_items,
        "impl_md_created": impl_exists,
        "no_notification_channel_impl": not channel_impl,
    }

def check_eval3(workdir: Path) -> dict:
    serialize = read(workdir / "src/csv/serialize.ts")
    fixture_impl = read(FIXTURES / "csv-project/docs/csv-export/impl.md")
    impl = read(workdir / "docs/csv-export/impl.md")
    # escapeField がダブルクォートに対応したか（" の検知と "" への置換）
    quote_detect = ('includes(\'"\')' in serialize) or ('includes("\\"")' in serialize) \
        or bool(re.search(r'/\[[^\]]*"[^\]]*\]/', serialize)) \
        or bool(re.search(r'\.includes\(.?["\']\\?"', serialize))
    quote_escape = ('replace' in serialize and '""' in serialize) or ("''\"\"''" in serialize)
    # CRLF 連結（exportCsv まで進んだ場合）
    crlf = "\\r\\n" in serialize
    return {
        "escape_field_handles_quotes": quote_detect and quote_escape,
        "crlf_used": crlf,
        "impl_md_updated": impl != "" and impl != fixture_impl,
    }

CHECKS = {
    "eval-1-design-update": check_eval1,
    "eval-2-spec-gap-escalation": check_eval2,
    "eval-3-session-resume": check_eval3,
}

def main():
    if len(sys.argv) < 2:
        print("Usage: grade.py <iteration_dir>", file=sys.stderr)
        sys.exit(1)
    iteration = Path(sys.argv[1])
    if not iteration.is_dir():
        print(f"Not a directory: {iteration}", file=sys.stderr)
        sys.exit(1)

    results = {}
    for ev, fn in CHECKS.items():
        for cond in ("with_skill", "without_skill"):
            workdir = iteration / ev / cond / "workdir"
            if workdir.exists():
                results[f"{ev}/{cond}"] = fn(workdir)
    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    print()

if __name__ == "__main__":
    main()
