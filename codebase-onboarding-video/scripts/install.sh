#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_ROOT="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
TARGET="$TARGET_ROOT/codebase-onboarding-video"
mkdir -p "$TARGET_ROOT"
if [[ "$HERE" == "$TARGET" ]]; then
  echo "已位於安裝路徑：$TARGET"
  exit 0
fi
if [[ -e "$TARGET" ]]; then
  echo "目標已存在：$TARGET；請先備份或移除舊版再安裝。" >&2
  exit 1
fi
cp -R "$HERE" "$TARGET"
echo "已安裝：$TARGET"
echo "重新啟動 Codex 並開啟任意專案，即可要求使用 codebase-onboarding-video。"
