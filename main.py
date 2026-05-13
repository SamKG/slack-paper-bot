import os
import logging
import requests
import toml
from scholarly import scholarly, ProxyGenerator
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
STATE_FILE = "state.toml"
AUTHORS_FILE = "authors.toml"

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

    bib = publication.get('bib', {})
    title = bib.get('title', 'Unknown Title')
    pub_url = publication.get('pub_url', '')
    authors_list = bib.get('author', 'Unknown Authors')
    abstract = bib.get('abstract', bib.get('description', 'No summary available.'))
    
    # Truncate abstract if it's too long for Slack block limits
    if len(abstract) > 1000:
        abstract = abstract[:997] + "..."
    
    # Sometimes pub_url is missing, we can construct a search url
    if not pub_url:
        query = title.replace(' ', '+')
        pub_url = f"https://scholar.google.com/scholar?q={query}"

    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎉 New Paper Alert! 🎉",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Title:* <{pub_url}|{title}>\n*Tracked Author:* {author_name}\n*Authors:* {authors_list}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n>{abstract}"
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

def setup_proxy():
    scraper_api_key = os.getenv("SCRAPER_API_KEY")
    pg = ProxyGenerator()
    
    if scraper_api_key:
        logging.info("Setting up ScraperAPI proxy...")
        success = pg.ScraperAPI(scraper_api_key)
        if success:
            scholarly.use_proxy(pg)
            return
        else:
            logging.warning("Failed to setup ScraperAPI. Falling back...")

    logging.info("Setting up Free Proxies... (This might be slow or fail)")
    try:
        pg.FreeProxies()
        scholarly.use_proxy(pg)
    except Exception as e:
        logging.warning(f"Could not setup free proxies: {e}. Proceeding without proxy, but may get blocked.")

def get_pub_year(pub):
    year_str = pub.get('bib', {}).get('pub_year', '0')
    try:
        return int(year_str)
    except ValueError:
        return 0

def main():
    if not os.path.exists(AUTHORS_FILE):
        default_authors = {
            "QC61PIYAAAAJ": "Albert Einstein" # Example Scholar ID
        }
        save_toml(AUTHORS_FILE, default_authors)
        logging.info(f"Created default {AUTHORS_FILE}. Please update it with real author IDs.")
        return

    authors = load_toml(AUTHORS_FILE, {})
    state = load_toml(STATE_FILE, {})

    setup_proxy()

    for author_id, author_name in authors.items():
        logging.info(f"Checking author: {author_name} ({author_id})")
        
        try:
            author = scholarly.search_author_id(author_id)
            author = scholarly.fill(author, sections=['publications'])
            
            is_new_author = author_id not in state
            if is_new_author:
                state[author_id] = []
            seen_pubs = state[author_id]
            
            # Sort publications so the newest ones are first
            pubs = sorted(author.get('publications', []), key=get_pub_year, reverse=True)
            
            if is_new_author and pubs:
                logging.info(f"New author {author_name} found. Announcing newest paper and tracking the rest silently.")
                most_recent = pubs[0]
                try:
                    most_recent = scholarly.fill(most_recent)
                except Exception as e:
                    logging.warning(f"Could not fill pub details: {e}")
                
                send_slack_message(author_name, most_recent)
                
                # Mark ALL currently visible papers as seen so we don't announce them tomorrow
                for p in pubs:
                    pid = p.get('author_pub_id')
                    if pid:
                        seen_pubs.append(pid)
                        
            elif not is_new_author:
                new_paper_found = False
                for pub in pubs:
                    pub_id = pub.get('author_pub_id')
                    if pub_id and pub_id not in seen_pubs:
                        logging.info(f"Found new paper for {author_name}: {pub.get('bib', {}).get('title')}")
                        
                        try:
                            # Fill ONLY this single paper to avoid being rate-limited
                            pub = scholarly.fill(pub)
                        except Exception as e:
                            logging.warning(f"Could not fill pub details for {pub_id}: {e}")
                        
                        send_slack_message(author_name, pub)
                        seen_pubs.append(pub_id)
                        new_paper_found = True
                        break # Process only ONE new paper per run to save requests
                
                if not new_paper_found:
                    logging.info(f"No new recent publications for {author_name}")
                    
        except Exception as e:
            logging.error(f"Error processing author {author_name} ({author_id}): {e}")

    save_toml(STATE_FILE, state)

if __name__ == "__main__":
    main()
