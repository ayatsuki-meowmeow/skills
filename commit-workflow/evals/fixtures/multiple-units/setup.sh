#!/usr/bin/env bash
# Usage: setup.sh <target_dir>
# シナリオ: ビジネスロジック / UI / ユーティリティ の3意味単位が同時に変更された状態。
set -euo pipefail

TARGET="${1:?target dir required}"
mkdir -p "$TARGET"
cd "$TARGET"

git init -q -b main
git config user.email "reiji.kono@aprender.jp"
git config user.name "Reiji Kono"

cat > README.md <<'EOF'
# sample-app
EOF
cat > package.json <<'EOF'
{ "name": "sample-app", "version": "0.0.1" }
EOF
git add README.md package.json
git -c commit.gpgsign=false commit -q -m "initial commit"

# ビジネスロジック層
mkdir -p src/services
cat > src/services/user-service.ts <<'EOF'
import type { User } from "../types/user"

export class UserService {
  async findById(id: string): Promise<User | null> {
    return null
  }
  async register(email: string, password: string): Promise<User> {
    return { id: "1", email }
  }
}
EOF

mkdir -p src/types
cat > src/types/user.ts <<'EOF'
export type User = {
  id: string
  email: string
}
EOF

# UI 層
mkdir -p src/components
cat > src/components/UserCard.tsx <<'EOF'
import type { User } from "../types/user"

export function UserCard({ user }: { user: User }) {
  return <div className="user-card">{user.email}</div>
}
EOF

# ユーティリティ層
mkdir -p src/utils
cat > src/utils/email-validator.ts <<'EOF'
export function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}
EOF
