import os
import random
import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
from datetime import datetime, timedelta

# --- SECRETS & CONFIGURATION ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") 
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

COOLDOWN_DAYS = 5
HISTORY_FILE = "history.json"
LINKS_FILE = "links.txt"

# --- 50+ RANDOM USER AGENTS ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Vivaldi/6.6.3271.45",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-T500) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
]

def load_history():
    """ Load history and ensure it is a dictionary to prevent TypeError. """
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                else:
                    print("Warning: history.json was a list. Resetting to empty dict.")
                    return {} 
            except json.JSONDecodeError:
                return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_available_link():
    if not os.path.exists(LINKS_FILE):
        print(f"Error: {LINKS_FILE} nahi mili.")
        return None
        
    with open(LINKS_FILE, "r") as f:
        all_links = [line.strip() for line in f.readlines() if line.strip()]

    if not all_links:
        print("Error: links.txt file khali hai.")
        return None

    history = load_history()
    now = datetime.now()
    available_links = []

    for link in all_links:
        if link in history:
            last_used_str = history[link]
            last_used_date = datetime.fromisoformat(last_used_str)
            if now - last_used_date >= timedelta(days=COOLDOWN_DAYS):
                available_links.append(link)
        else:
            available_links.append(link)

    if not available_links:
        print(f"Sabhi links {COOLDOWN_DAYS} din ke cooldown par hain.")
        return None

    return random.choice(available_links), history

def shorten_title_with_pollinations(long_title):
    """ Pollinations AI ka use karke Amazon title ko short aur catchy banana. """
    print("AI se title short kar rahe hain...")
    prompt = f"Rewrite this Amazon product title to be catchy and short for a Pinterest pin (maximum 5 to 8 words). Just give the title, no quotes, no extra text: {long_title}"
    
    try:
        # Pollinations Text API par POST request
        response = requests.post("https://text.pollinations.ai/", data=prompt.encode('utf-8'), headers={'Content-Type': 'text/plain'})
        if response.status_code == 200:
            short_title = response.text.strip()
            # Agar AI quotes laga de toh usko hatana
            if short_title.startswith('"') and short_title.endswith('"'):
                short_title = short_title[1:-1]
            print(f"AI Shortened Title: {short_title}")
            return short_title
        else:
            print("AI failed, fallback to original short.")
            return long_title[:60] + "..."
    except Exception as e:
        print(f"Pollinations AI Error: {e}")
        return long_title[:60] + "..."

def process_and_post():
    result = get_available_link()
    if not result:
        return

    affiliate_link, history = result
    print(f"Processing Link: {affiliate_link}")
    
    random_user_agent = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": random_user_agent,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/" # Google ka referer dene se Amazon ko lagta hai user search karke aaya hai
    }
    
    try:
        # Session ka use karna normal requests se zyada safe hota hai
        session = requests.Session()
        response = session.get(affiliate_link, headers=headers, allow_redirects=True, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # 1. SAFE EXTRACTION: Pehle check karein ki Title mila ya nahi
        title_element = soup.find("span", {"id": "productTitle"})
        
        if title_element is None:
            print("❌ Scraping failed! Amazon ne asli page ki jagah CAPTCHA de diya hai.")
            print("Action: Yeh link skip kar rahe hain, code crash nahi hoga. Next time retry hoga.")
            return # Script yahin ruk jayegi aur crash nahi hogi
            
        raw_title = title_element.get_text(strip=True)
        
        # Image extract karna
        image_element = soup.find("img", {"id": "landingImage"})
        image_url = image_element['src'] if image_element else ""
        
        # Description extract karna
        bullets = soup.find("div", {"id": "feature-bullets"})
        description = ""
        if bullets:
            list_items = bullets.find_all("li")
            description = " ".join([li.get_text(strip=True) for li in list_items])
            
        # AI Title
        final_title = shorten_title_with_pollinations(raw_title)

    except Exception as e:
        print(f"Scraping request failed. Error: {e}")
        return

    # 1. Telegram par bhejna
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        caption = f"🔥 **{final_title}**\n\n✨ \n\n🛒 **Buy Here:** {affiliate_link}"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": caption, "parse_mode": "Markdown"}
        t_res = requests.post(telegram_api_url, data=payload)
        if t_res.status_code == 200:
            print("✅ Telegram par message chala gaya!")
        else:
            print(f"❌ Telegram Error: {t_res.text}")

    # 2. Webhook par bhejna
    if WEBHOOK_URL:
        webhook_payload = {
            "title": final_title,
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
