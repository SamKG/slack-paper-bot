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

4. **Run the Bot:**
   Run the bot periodically (e.g., via a daily cron job):
   ```bash
   uv run main.py
   ```
   The bot keeps track of already seen papers in `state.toml`. If you want to test the Slack notification with an existing paper, you can manually remove a publication ID from `state.toml`.

## Notes
- Google Scholar aggressively blocks scrapers. If you are polling too often (or checking hundreds of authors), you may get IP blocked or hit CAPTCHAs. This bot uses the `scholarly` library. It's recommended to run this script only once a day or a few times a week.
