import os
import logging
import requests
import toml
from scholarly import scholarly
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
STATE_FILE = "state.json"
AUTHORS_FILE = "authors.toml"

def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def load_toml(filepath, default):
    if not os.path.exists(filepath):
        return default
    with open(filepath, 'r') as f:
        return toml.load(f)

def save_toml(filepath, data):
    with open(filepath, 'w') as f:
        toml.dump(data, f)

def send_slack_message(author_name, publication):
    if not SLACK_WEBHOOK_URL:
        logging.warning("SLACK_WEBHOOK_URL not set. Skipping Slack notification.")
        return

    title = publication.get('bib', {}).get('title', 'Unknown Title')
    pub_url = publication.get('pub_url', '')
    
    # Sometimes pub_url is missing, we can construct a search url or just use the title
    if not pub_url:
        query = title.replace(' ', '+')
        pub_url = f"https://scholar.google.com/scholar?q={query}"

    message = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🎉 *New Paper Alert!* 🎉\n*Author:* {author_name}\n*Title:* <{pub_url}|{title}>"
                }
            }
        ]
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message)
        response.raise_for_status()
        logging.info(f"Successfully sent Slack message for '{title}'")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Slack message: {e}")

def main():
    if not os.path.exists(AUTHORS_FILE):
        default_authors = {
            "QC61PIYAAAAJ": "Albert Einstein" # Example Scholar ID
        }
        save_toml(AUTHORS_FILE, default_authors)
        logging.info(f"Created default {AUTHORS_FILE}. Please update it with real author IDs.")
        return

    authors = load_toml(AUTHORS_FILE, {})
    state = load_json(STATE_FILE, {})

    for author_id, author_name in authors.items():
        logging.info(f"Checking author: {author_name} ({author_id})")
        
        try:
            author = scholarly.search_author_id(author_id)
            author = scholarly.fill(author, sections=['publications'])
            
            if author_id not in state:
                state[author_id] = []
                
            seen_pubs = state[author_id]
            new_pubs = []
            
            for pub in author.get('publications', []):
                pub_id = pub.get('author_pub_id')
                if pub_id and pub_id not in seen_pubs:
                    try:
                        pub = scholarly.fill(pub)
                    except Exception as e:
                        logging.warning(f"Could not fill pub details for {pub_id}: {e}")
                    
                    new_pubs.append(pub)
                    seen_pubs.append(pub_id)
            
            if new_pubs:
                logging.info(f"Found {len(new_pubs)} new publications for {author_name}")
                for pub in new_pubs:
                    send_slack_message(author_name, pub)
            else:
                logging.info(f"No new publications for {author_name}")
                
        except Exception as e:
            logging.error(f"Error processing author {author_name} ({author_id}): {e}")

    save_json(STATE_FILE, state)

if __name__ == "__main__":
    main()

    main()
