import os
import random
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta

# --- CONFIGURATION ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") 
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

COOLDOWN_DAYS = 5
HISTORY_FILE = "history.json"
LINKS_FILE = "links.txt"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_available_link():
    # Saare links load karein
    if not os.path.exists(LINKS_FILE):
        print(f"Error: {LINKS_FILE} nahi mili. Kripya file banayein aur links daalein.")
        return None
        
    with open(LINKS_FILE, "r") as f:
        all_links = [line.strip() for line in f.readlines() if line.strip()]

    if not all_links:
        print("Error: links.txt file khali hai.")
        return None

    history = load_history()
    now = datetime.now()
    available_links = []

    # Filter karein wo links jo cooldown period mein nahi hain
    for link in all_links:
        if link in history:
            last_used_str = history[link]
            last_used_date = datetime.fromisoformat(last_used_str)
            
            # Agar last post hue 5 din se zyada ho gaye hain, toh available maanein
            if now - last_used_date >= timedelta(days=COOLDOWN_DAYS):
                available_links.append(link)
        else:
            # Agar link history mein hai hi nahi (first time), toh available hai
            available_links.append(link)

    if not available_links:
        print(f"Abhi koi link available nahi hai. Sabhi links {COOLDOWN_DAYS} din ke cooldown par hain.")
        return None

    # Available links mein se koi ek random chunein
    chosen_link = random.choice(available_links)
    return chosen_link, history

def process_and_post():
    result = get_available_link()
    if not result:
        return

    affiliate_link, history = result
    print(f"Processing Link: {affiliate_link}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(affiliate_link, headers=headers, allow_redirects=True, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Title aur Image nikalna
        title = soup.find("span", {"id": "productTitle"}).get_text(strip=True)
        image_url = soup.find("img", {"id": "landingImage"})['src']
        
        # Description (Feature Bullets) nikalna
        bullets = soup.find("div", {"id": "feature-bullets"})
        description = ""
        if bullets:
            list_items = bullets.find_all("li")
            description = " ".join([li.get_text(strip=True) for li in list_items])
            
    except Exception as e:
        print(f"Scraping failed. Error: {e}")
        return

    # 1. Telegram par bhejna
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        caption = f"🔥 **{title[:60]}...**\n\n✨ {description[:150]}...\n\n🛒 **Buy Here:** {affiliate_link}"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": caption, "parse_mode": "Markdown"}
        t_res = requests.post(telegram_api_url, data=payload)
        if t_res.status_code == 200:
            print("✅ Telegram par message chala gaya!")
        else:
            print(f"❌ Telegram Error: {t_res.text}")

    # 2. Webhook par bhejna
    if WEBHOOK_URL:
        webhook_payload = {
            "title": title,
            "description": description[:300],
            "image_url": image_url,
            "affiliate_link": affiliate_link
        }
        w_res = requests.post(WEBHOOK_URL, json=webhook_payload)
        if w_res.status_code == 200:
            print("✅ Webhook par data chala gaya!")
        else:
            print(f"❌ Webhook Error: {w_res.status_code}")

    # 3. Post successful hone ke baad History Update karna
    history[affiliate_link] = datetime.now().isoformat()
    save_history(history)
    print("✅ History update ho gayi!")

if __name__ == "__main__":
    process_and_post()
