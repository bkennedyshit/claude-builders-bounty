# n8n Weekly GitHub Dev Summary (Claude)

Automated n8n workflow that generates a narrative weekly summary of GitHub repo activity using Claude API.

## Setup (5 steps)

1. **Import workflow** — in n8n: Workflows → Import → paste `weekly-dev-summary.json`

2. **Set credentials** — in n8n Credentials, create:
   - `GitHub Token` (httpHeaderAuth) → Header: `Authorization`, Value: `token YOUR_GITHUB_TOKEN`
   - `Anthropic API Key` (httpHeaderAuth) → Header: `x-api-key`, Value: `YOUR_ANTHROPIC_KEY`
   - `SMTP` → your email server details

3. **Set variables** — in n8n Variables:
   - `GITHUB_REPO` → `owner/repo` (e.g. `anthropics/anthropic-sdk-python`)
   - `DISCORD_WEBHOOK_URL` → your Discord webhook URL
   - `FROM_EMAIL` / `TO_EMAIL` → email addresses
   - `LANGUAGE` → `EN` or `FR`

4. **Activate** — toggle the workflow ON

5. **Test** — click "Execute Workflow" to run immediately

## Schedule

Runs every Friday at 5:00 PM. Edit the Cron node to change timing.

## Delivery

Sends to both Discord webhook AND email simultaneously. Remove either node if only one is needed.
