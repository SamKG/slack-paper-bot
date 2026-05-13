# Slack Paper Bot

This bot monitors Google Scholar profiles and sends a Slack notification when a new paper is found.

## Setup

1. **Install dependencies and run via `uv`:**
   Ensure you have [uv](https://github.com/astral-sh/uv) installed. You can run the bot directly which will handle the dependencies automatically:
   ```bash
   uv run main.py
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and fill in your Slack Webhook URL.
   ```bash
   cp .env.example .env
   ```
   *You can get a Slack Webhook URL by creating a Slack App in your workspace and enabling "Incoming Webhooks".*

3. **Configure Authors:**
   Run the script once to generate `authors.toml`:
   ```bash
   uv run main.py
   ```
   Edit `authors.toml` and replace the example with the Scholar IDs of the people you want to track.
   The Scholar ID is the `user=` parameter in a Google Scholar profile URL. (e.g. `https://scholar.google.com/citations?user=QC61PIYAAAAJ` -> `QC61PIYAAAAJ`)

4. **Run the Bot (Locally):**
   Run the bot periodically (e.g., via a daily cron job):
   ```bash
   uv run main.py
   ```
   The bot keeps track of already seen papers in `state.toml`. If you want to test the Slack notification with an existing paper, you can manually remove a publication ID from `state.toml`.

## GitHub Actions Automated Run
This repository includes a GitHub Actions workflow that runs the script automatically every day. 

To enable this:
1. Go to your repository on GitHub.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Set the name to `SLACK_WEBHOOK_URL` and the value to your Slack Webhook URL.
5. **(Highly Recommended)** Create another secret named `SCRAPER_API_KEY`. Google Scholar aggressively blocks data-center IP addresses (like GitHub Actions). The `scholarly` library has native support for [ScraperAPI](https://www.scraperapi.com/), which offers 5,000 free requests per month. Create a free account, get an API key, and save it as `SCRAPER_API_KEY` in your GitHub secrets.
6. Make sure `authors.toml` is committed to the repository with the list of people you want to track.
7. The action will automatically run once a day, post to Slack, and commit the updated `state.toml` file back to the repository so you don't get duplicate notifications.

## Notes
- Google Scholar aggressively blocks scrapers. If you are polling too often (or checking hundreds of authors), you may get IP blocked or hit CAPTCHAs. This bot uses the `scholarly` library. It's recommended to run this script only once a day or a few times a week.
