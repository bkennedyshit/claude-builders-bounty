#!/usr/bin/env bash
# generate-changelog: auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh [since-tag] [output-file]
# If no tag provided, uses the last git tag. If no tags exist, uses all commits.

set -euo pipefail

SINCE_TAG="${1:-}"
OUTPUT="${2:-CHANGELOG.md}"
DATE=$(date +%Y-%m-%d)

# Detect since tag
if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -n "$SINCE_TAG" ]; then
  RANGE="${SINCE_TAG}..HEAD"
  HEADER="## [Unreleased] — since \`${SINCE_TAG}\` (${DATE})"
else
  RANGE="HEAD"
  HEADER="## [Unreleased] — ${DATE}"
fi

echo "📋 Generating changelog ${SINCE_TAG:+from $SINCE_TAG }to HEAD..."

# Fetch all commit messages in range
COMMITS=$(git log "$RANGE" --pretty=format:"%s" --no-merges 2>/dev/null || git log --pretty=format:"%s" --no-merges)

if [ -z "$COMMITS" ]; then
  echo "⚠️  No commits found."
  exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r msg; do
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  # Strip conventional commit prefixes for display
  clean=$(echo "$msg" | sed -E 's/^(feat|fix|chore|refactor|docs|style|test|perf|ci|build|revert)(\([^)]*\))?!?:\s*//')

  if echo "$lower" | grep -qE '^(feat|add|new|implement|create|introduce|support)'; then
    ADDED="${ADDED}- ${clean}\n"
  elif echo "$lower" | grep -qE '^(fix|bug|patch|correct|resolve|close|hotfix)'; then
    FIXED="${FIXED}- ${clean}\n"
  elif echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|revert)'; then
    REMOVED="${REMOVED}- ${clean}\n"
  elif echo "$lower" | grep -qE '^(update|change|refactor|improve|bump|upgrade|migrate|rename|move|replace|chore|perf|style|docs|ci|build|test)'; then
    CHANGED="${CHANGED}- ${clean}\n"
  else
    OTHER="${OTHER}- ${clean}\n"
  fi
done <<< "$COMMITS"

# Build changelog content
{
  # Prepend to existing CHANGELOG if it exists
  echo "# Changelog"
  echo ""
  echo "$HEADER"
  echo ""

  if [ -n "$ADDED" ]; then
    echo "### ✨ Added"
    printf "%b" "$ADDED"
    echo ""
  fi

  if [ -n "$FIXED" ]; then
    echo "### 🐛 Fixed"
    printf "%b" "$FIXED"
    echo ""
  fi

  if [ -n "$CHANGED" ]; then
    echo "### 🔄 Changed"
    printf "%b" "$CHANGED"
    echo ""
  fi

  if [ -n "$REMOVED" ]; then
    echo "### 🗑️ Removed"
    printf "%b" "$REMOVED"
    echo ""
  fi

  if [ -n "$OTHER" ]; then
    echo "### 📝 Other"
    printf "%b" "$OTHER"
    echo ""
  fi

  # Append previous changelog content (skip existing "# Changelog" header)
  if [ -f "$OUTPUT" ]; then
    tail -n +2 "$OUTPUT"
  fi

} > "${OUTPUT}.tmp"

mv "${OUTPUT}.tmp" "$OUTPUT"
echo "✅ Changelog written to $OUTPUT"
