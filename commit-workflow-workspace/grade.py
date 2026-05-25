#!/usr/bin/env python3
"""Grading script for commit-workflow skill evals.

各 run ディレクトリ (with_skill / without_skill) に対して、
git log を解析してアサーションを評価し grading.json を出力する。

Usage:
    python grade.py <iteration_dir>
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPECTED_AUTHOR_NAME = "Reiji Kono"
EXPECTED_AUTHOR_EMAIL = "reiji.kono@aprender.jp"
INITIAL_COMMIT_SUBJECT = "initial commit"


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


def commits_after_initial(repo: Path) -> list[dict[str, Any]]:
    """initial commit より後に作られたコミットのリストを返す。"""
    raw = git(
        repo,
        "log",
        "--all",
        "--reverse",
        "--pretty=format:===COMMIT===%n%H%n%an <%ae>%n%cn <%ce>%n%B%n===END===",
    )
    commits: list[dict[str, Any]] = []
    for block in raw.split("===COMMIT===")[1:]:
        chunk = block.split("===END===")[0].strip("\n")
        lines = chunk.split("\n")
        sha = lines[0]
        author = lines[1]
        committer = lines[2]
        message = "\n".join(lines[3:]).rstrip("\n")
        subject = message.split("\n", 1)[0]
        if subject == INITIAL_COMMIT_SUBJECT:
            continue
        commits.append(
            {
                "sha": sha,
                "author": author,
                "committer": committer,
                "message": message,
                "subject": subject,
            }
        )
    return commits


def has_japanese(text: str) -> bool:
    return bool(re.search(r"[぀-ヿ一-鿿]", text))


def is_ascii(text: str) -> bool:
    return all(ord(c) < 128 for c in text)


def categorize_path(path: str) -> str:
    if path.startswith("src/services/") or path.startswith("src/types/"):
        return "business"
    if path.startswith("src/components/"):
        return "ui"
    if path.startswith("src/utils/"):
        return "util"
    return "other"


def files_in_commit(repo: Path, sha: str) -> list[str]:
    raw = git(repo, "show", "--no-renames", "--name-only", "--pretty=format:", sha)
    return [line.strip() for line in raw.strip().split("\n") if line.strip()]


def evaluate_run(repo: Path, assertions: list[dict[str, str]]) -> list[dict[str, Any]]:
    commits = commits_after_initial(repo)
    status = git(repo, "status", "--porcelain").strip()

    results: list[dict[str, Any]] = []

    def add(text: str, passed: bool, evidence: str) -> None:
        results.append({"text": text, "passed": passed, "evidence": evidence})

    by_name = {a["name"]: a["description"] for a in assertions}

    def desc(name: str) -> str:
        return by_name.get(name, name)

    # has_new_commit
    add(desc("has_new_commit"), len(commits) >= 1, f"new commits = {len(commits)}")

    # multiple_commits (optional)
    if "multiple_commits" in by_name:
        add(
            desc("multiple_commits"),
            len(commits) >= 2,
            f"new commits = {len(commits)}",
        )

    # working_tree_clean
    add(
        desc("working_tree_clean"),
        status == "",
        f"git status --porcelain output: {status!r}",
    )

    if not commits:
        for name in (
            "subject_is_ascii",
            "has_blank_line_after_subject",
            "body_has_japanese",
            "no_co_authored_by",
            "author_is_user",
        ):
            if name in by_name:
                add(desc(name), False, "no new commits to evaluate")
        if "semantic_units_separated" in by_name:
            add(desc("semantic_units_separated"), False, "no new commits to evaluate")
        return results

    # subject_is_ascii
    failed_subjects = [c["subject"] for c in commits if not is_ascii(c["subject"])]
    add(
        desc("subject_is_ascii"),
        len(failed_subjects) == 0,
        "non-ASCII subjects: " + (str(failed_subjects) if failed_subjects else "(none)"),
    )

    # has_blank_line_after_subject
    bad_blank: list[str] = []
    for c in commits:
        lines = c["message"].split("\n")
        if len(lines) < 3:
            bad_blank.append(c["subject"])
            continue
        if lines[1].strip() != "":
            bad_blank.append(c["subject"])
    add(
        desc("has_blank_line_after_subject"),
        len(bad_blank) == 0,
        "commits without blank line after subject: " + (str(bad_blank) if bad_blank else "(none)"),
    )

    # body_has_japanese
    no_jp: list[str] = []
    for c in commits:
        lines = c["message"].split("\n", 2)
        body = lines[2] if len(lines) >= 3 else ""
        if not has_japanese(body):
            no_jp.append(c["subject"])
    add(
        desc("body_has_japanese"),
        len(no_jp) == 0,
        "commits without Japanese in body: " + (str(no_jp) if no_jp else "(none)"),
    )

    # no_co_authored_by
    has_co = [c["subject"] for c in commits if "Co-Authored-By" in c["message"] or "Co-authored-by" in c["message"]]
    add(
        desc("no_co_authored_by"),
        len(has_co) == 0,
        "commits with Co-Authored-By: " + (str(has_co) if has_co else "(none)"),
    )

    # author_is_user
    expected = f"{EXPECTED_AUTHOR_NAME} <{EXPECTED_AUTHOR_EMAIL}>"
    bad_author: list[str] = []
    for c in commits:
        if c["author"] != expected or c["committer"] != expected:
            bad_author.append(f"{c['subject']!r}: author={c['author']}, committer={c['committer']}")
    add(
        desc("author_is_user"),
        len(bad_author) == 0,
        "commits with unexpected author/committer: " + (str(bad_author) if bad_author else "(none)"),
    )

    # semantic_units_separated (optional)
    if "semantic_units_separated" in by_name:
        violations: list[str] = []
        for c in commits:
            files = files_in_commit(repo, c["sha"])
            categories = {categorize_path(f) for f in files if categorize_path(f) != "other"}
            if len(categories) > 1:
                violations.append(f"{c['subject']!r} mixes {sorted(categories)}")
        add(
            desc("semantic_units_separated"),
            len(violations) == 0,
            "violations: " + (str(violations) if violations else "(none)"),
        )

    return results


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: grade.py <iteration_dir>", file=sys.stderr)
        sys.exit(1)
    iteration = Path(sys.argv[1])
    if not iteration.is_dir():
        print(f"Not a directory: {iteration}", file=sys.stderr)
        sys.exit(1)

    for eval_dir in sorted(iteration.iterdir()):
        if not eval_dir.is_dir() or not eval_dir.name.startswith("eval-"):
            continue
        meta_file = eval_dir / "eval_metadata.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text())
        assertions = meta.get("assertions", [])

        for run_name in ("with_skill", "without_skill"):
            run_dir = eval_dir / run_name
            repo = run_dir / "repo"
            if not repo.is_dir():
                print(f"skip (no repo): {repo}")
                continue
            results = evaluate_run(repo, assertions)
            passed = sum(1 for r in results if r["passed"])
            total = len(results)
            failed = total - passed
            pass_rate = passed / total if total > 0 else 0.0

            grading_payload = {
                "summary": {
                    "pass_rate": pass_rate,
                    "passed": passed,
                    "failed": failed,
                    "total": total,
                },
                "expectations": results,
            }

            # 後方互換: run_dir 直下にも残す
            (run_dir / "grading.json").write_text(
                json.dumps(grading_payload, ensure_ascii=False, indent=2)
            )

            # aggregate_benchmark が期待する run-1/ レイアウトに合わせる
            sub_run_dir = run_dir / "run-1"
            sub_run_dir.mkdir(exist_ok=True)
            (sub_run_dir / "grading.json").write_text(
                json.dumps(grading_payload, ensure_ascii=False, indent=2)
            )

            # timing.json があれば run-1/ にコピー
            timing_src = run_dir / "timing.json"
            if timing_src.exists():
                (sub_run_dir / "timing.json").write_text(timing_src.read_text())

            print(f"{eval_dir.name}/{run_name}: {passed}/{total} passed")


if __name__ == "__main__":
    main()
