# Claude Code PR Review Agent

CLI tool that fetches a GitHub PR diff and generates a structured Markdown review using Claude.

## Install

```bash
pip install anthropic  # optional, uses urllib by default
export ANTHROPIC_API_KEY=your_key
export GITHUB_TOKEN=your_token  # optional, increases rate limit
```

## Usage

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --post   # posts to GitHub
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Format

```markdown
## 📋 Summary
[2-3 sentence summary]

## ⚠️ Identified Risks
- risk 1

## 💡 Improvement Suggestions  
- suggestion 1

## 🎯 Confidence Score
High — straightforward refactor with good test coverage
```
