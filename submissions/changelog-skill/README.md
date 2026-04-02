# generate-changelog

Auto-generate a structured `CHANGELOG.md` from your git history in seconds.

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

## Usage

```bash
# Auto-detect last tag, write to CHANGELOG.md
bash changelog.sh

# Since a specific tag
bash changelog.sh v1.2.0

# Custom output file
bash changelog.sh v1.2.0 RELEASES.md
```

## What it does

- Fetches all commits since the last git tag (or all commits if no tags exist)
- Auto-categorizes into **Added / Fixed / Changed / Removed / Other**
- Uses conventional commit prefixes when present (`feat:`, `fix:`, `chore:` etc.)
- Prepends new section to existing `CHANGELOG.md` — history is never lost
- Works on any git repo, zero dependencies

## Categorization Rules

| Prefix | Section |
|---|---|
| `feat`, `add`, `new`, `implement`, `create` | ✨ Added |
| `fix`, `bug`, `patch`, `resolve`, `hotfix` | 🐛 Fixed |
| `remove`, `delete`, `drop`, `deprecate`, `revert` | 🗑️ Removed |
| `update`, `change`, `refactor`, `improve`, `bump`, `chore`, `perf`, `docs`, `ci` | 🔄 Changed |
| Everything else | 📝 Other |

## Sample Output

```markdown
# Changelog

## [Unreleased] — since `v1.2.0` (2026-04-02)

### ✨ Added
- New image upscaling endpoint with 4x super-resolution
- Discord bot with sales automation and memory

### 🐛 Fixed
- Pinterest board selector failing on mobile viewport
- YouTube auth token refresh loop on expired sessions

### 🔄 Changed
- Upgraded Playwright to 1.52 for Chrome 145 compatibility
- Refactored brand_cron to bypass godmode for all platforms

### 🗑️ Removed
- Legacy cookie-injection method for Instagram posting
```
