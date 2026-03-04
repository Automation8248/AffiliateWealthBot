import os
import random
import requests
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import vertexai
from vertexai.generative_models import GenerativeModel

# --- CONFIGURATION FROM GITHUB SECRETS ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") 
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GCP_JSON = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")

COOLDOWN_DAYS = 5
HISTORY_FILE = "history.json"
LINKS_FILE = "links.txt"

# --- VERTEX AI SETUP (Using your uploaded JSON data) ---
def setup_vertex():
    if GCP_JSON:
        try:
            with open("gcp_key.json", "w") as f:
                f.write(GCP_JSON)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
            # Project ID from your JSON
            vertexai.init(project="careful-broker-484223-t0", location="us-central1")
            return GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            print(f"Vertex AI Init Error: {e}")
    return None

model = setup_vertex()

# --- 100+ USER AGENTS TO PREVENT BLOCKING ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36",
    # ... (Note: Add remaining 94+ agents here from standard lists)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # (Simplified for display - ensures variety of devices & browsers)
] + [f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36" for _ in range(90)]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
            except: return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def shorten_title(long_title):
    print("Gemini (Vertex AI) se title short kar rahe hain...")
    if not model: return long_title[:50]
    prompt = f"Rewrite this Amazon product title to be catchy and short for a Pinterest pin (maximum 6 words). Just give the title, no quotes: {long_title}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip().replace('"', '')
    except Exception as e:
        print(f"AI Error: {e}")
        return long_title[:50]

def process_and_post():
    # Link selection from links.txt
    if not os.path.exists(LINKS_FILE): return
    with open(LINKS_FILE, "r") as f:
        all_links = [l.strip() for l in f.readlines() if l.strip()]
    
    history = load_history()
    now = datetime.now()
    available = [l for l in all_links if l not in history or (now - datetime.fromisoformat(history[l])) >= timedelta(days=COOLDOWN_DAYS)]
    
    if not available:
        print("Sabe links cooldown par hain.")
        return

    affiliate_link = random.choice(available)
    print(f"Processing: {affiliate_link}")

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    try:
        # Handles amzn.to redirects automatically
        res = requests.get(affiliate_link, headers=headers, timeout=15, allow_redirects=True)
        soup = BeautifulSoup(res.content, "html.parser")
        
        title_node = soup.find("span", {"id": "productTitle"})
        if not title_node: #
            print("❌ Amazon block (Captcha). Code safely skipping.")
            return

        raw_title = title_node.get_text(strip=True)
        img_url = soup.find("img", {"id": "landingImage"})['src']
        
        bullets = soup.find("div", {"id": "feature-bullets"})
        description = " ".join([li.get_text(strip=True) for li in bullets.find_all("li")]) if bullets else ""

        final_title = shorten_title(raw_title)

        # 1. Telegram Post
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            t_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            caption = f"🔥 **{final_title}**\n\n🛒 **Buy Here:** {affiliate_link}"
            requests.post(t_url, data={"chat_id": TELEGRAM_CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "Markdown"})

        # 2. Webhook Post
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"title": final_title, "image_url": img_url, "link": affiliate_link, "desc": description[:200]})

        history[affiliate_link] = now.isoformat()
        save_history(history)
        print("✅ Done!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    process_and_post()
