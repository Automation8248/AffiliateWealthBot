import os
import random
import time
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import cloudscraper

# --- CONFIGURATION ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") 
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

COOLDOWN_DAYS = 5
HISTORY_FILE = "history.json"
LINKS_FILE = "links.txt"

# Real User "Kahan se aaya?" (Referers)
HUMAN_REFERERS = [
    "https://www.google.com/search?q=best+amazon+finds",
    "https://www.bing.com/",
    "https://www.pinterest.com/",
    "https://www.facebook.com/",
    "https://twitter.com/"
]

def clean_text(text):
    if not text: return ""
    return re.sub(r'[*#]', '', text).strip()

def smart_truncate_title(raw_title):
    clean_title = re.split(r'[,|\-\(]', raw_title)[0].strip()
    return clean_text(clean_title[:80])

def smart_truncate_desc(raw_desc, max_len=200):
    if len(raw_desc) <= max_len:
        return clean_text(raw_desc)
    truncated = raw_desc[:max_len]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return clean_text(truncated) + "..."

def process_and_post():
    if not os.path.exists(LINKS_FILE): return
    with open(LINKS_FILE, "r") as f:
        all_links = [l.strip() for l in f.readlines() if l.strip()]
    
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f: history = json.load(f)
        except: history = {}

    now = datetime.now()
    available = [l for l in all_links if l not in history or (now - datetime.fromisoformat(history[l])) >= timedelta(days=COOLDOWN_DAYS)]
    
    if not available: 
        print(f"Sabhi links {COOLDOWN_DAYS} din ke cooldown par hain.")
        return
        
    affiliate_link = random.choice(available)
    print(f"Processing Link: {affiliate_link}")

    # Asli Insaan ka Browser Setup (Cloudscraper handles the deep TLS fingerprints)
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    success = False
    
    # Retry System
    for attempt in range(3):
        print(f"Attempt {attempt + 1}...")
        try:
            # 1. HUMAN BEHAVIOR: Random Wait Time (Insaan turant click nahi karta)
            wait_time = random.uniform(3.5, 7.5)
            print(f"Human delay... waiting {wait_time:.2f} seconds before clicking.")
            time.sleep(wait_time)

            # 2. HUMAN BEHAVIOR: Referer (Amazon ko lagega Google ya Pinterest se traffic aaya hai)
            headers = {
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": random.choice(HUMAN_REFERERS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            }

            res = scraper.get(affiliate_link, headers=headers, timeout=20, allow_redirects=True)
            soup = BeautifulSoup(res.content, "html.parser")
            
            title_node = soup.find("span", {"id": "productTitle"})
            
            if title_node:
                raw_title = title_node.get_text(strip=True)
                img_node = soup.find("img", {"id": "landingImage"})
                img_url = img_node['src'] if img_node else ""
                
                bullets = soup.find("div", {"id": "feature-bullets"})
                raw_desc = " ".join([li.get_text(strip=True) for li in bullets.find_all("li")]) if bullets else "Great quality kitchen and home find on Amazon."
                
                category_node = soup.select_one('#wayfinding-breadcrumbs_container ul li:first-child a')
                category = category_node.get_text(strip=True) if category_node else "General"
                
                success = True
                break
            else:
                print("Amazon ne Captcha dikhaya. Agle attempt ke liye ready ho rahe hain...")
                time.sleep(random.uniform(4.0, 8.0))

        except Exception as e:
            print(f"Request Error: {e}")
            time.sleep(5)

    if not success:
        print("❌ Blocked. Amazon ko abhi bhi shaq hai. GitHub action next time schedule par try karega.")
        return

    # Formatting
    f_title = smart_truncate_title(raw_title)
    f_desc = smart_truncate_desc(raw_desc, 200)

    # Telegram (Sirf Title, Link)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        clean_token = str(TELEGRAM_BOT_TOKEN).split(']')[-1].strip().replace('[', '').replace(']', '')
        t_url = f"https://api.telegram.org/bot{clean_token}/sendPhoto"
        caption = f"🔥 <b>{f_title}</b>\n\n🛒 <b>Product Link:</b> {affiliate_link}"
        t_res = requests.post(t_url, data={"chat_id": TELEGRAM_CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"})
        if t_res.status_code == 200:
            print("✅ Telegram par bhej diya gaya.")
        else:
            print(f"⚠️ Telegram Error: {t_res.text}")

    # Webhook
    if WEBHOOK_URL:
        w_res = requests.post(WEBHOOK_URL, json={
            "title": f_title, "image": img_url, "link": affiliate_link, "desc": f_desc, "category": category
        })
        if w_res.status_code == 200:
            print("✅ Webhook par bhej diya gaya.")

    # Save History
    history[affiliate_link] = now.isoformat()
    with open(HISTORY_FILE, "w") as f: json.dump(history, f, indent=4)
    print("✅ All Automation Tasks Successful!")

if __name__ == "__main__":
    process_and_post()
