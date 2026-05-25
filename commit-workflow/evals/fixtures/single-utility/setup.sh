#!/usr/bin/env bash
# Usage: setup.sh <target_dir>
# テスト対象の git リポジトリ状態を <target_dir> に構築する。
# シナリオ: 日付フォーマットのユーティリティ関数1つと、そのユニットテスト1つを追加した状態。
set -euo pipefail

TARGET="${1:?target dir required}"
mkdir -p "$TARGET"
cd "$TARGET"

git init -q -b main
git config user.email "reiji.kono@aprender.jp"
git config user.name "Reiji Kono"

mkdir -p src/utils
cat > README.md <<'EOF'
# sample-app
EOF
cat > package.json <<'EOF'
{ "name": "sample-app", "version": "0.0.1" }
EOF

git add README.md package.json
git -c commit.gpgsign=false commit -q -m "initial commit"

cat > src/utils/format-date.ts <<'EOF'
export function formatDateISO(date: Date): string {
  return date.toISOString().slice(0, 10)
}

export function formatDateLocal(date: Date): string {
  return date.toLocaleDateString("ja-JP")
}
EOF

mkdir -p src/utils
cat > src/utils/format-date.test.ts <<'EOF'
import { formatDateISO, formatDateLocal } from "./format-date"

test("formatDateISO returns yyyy-mm-dd", () => {
  expect(formatDateISO(new Date("2026-05-25T10:00:00Z"))).toBe("2026-05-25")
})

test("formatDateLocal returns JP locale string", () => {
  expect(formatDateLocal(new Date("2026-05-25T10:00:00Z"))).toMatch(/2026/)
})
EOF
