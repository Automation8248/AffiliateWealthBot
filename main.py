import os
import random
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

# --- SECRETS & CONFIGURATION ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") 
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- 7 DAYS COOLDOWN LOGIC ---
COOLDOWN_DAYS = 7 

HISTORY_FILE = "history.json"
LINKS_FILE = "links.txt"
TEMP_IMAGE_FILE = "temp_image.jpg"
TITLES_FILE = "titles.txt"
TAGS_FILE = "tags.txt"

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
            # 7 Din ka Cooldown check
            if now - last_used_date >= timedelta(days=COOLDOWN_DAYS):
                available_links.append(link)
        else:
            available_links.append(link)

    if not available_links:
        print(f"Sabhi links {COOLDOWN_DAYS} din ke cooldown par hain.")
        return None

    return random.choice(available_links), history

def get_random_title():
    if not os.path.exists(TITLES_FILE):
        return "Check Out This Awesome Product! 🔥" 
    
    with open(TITLES_FILE, "r", encoding="utf-8") as f:
        titles = [line.strip() for line in f.readlines() if line.strip()]
        
    if not titles:
        return "Check Out This Awesome Product! 🔥"
        
    return random.choice(titles)

def get_random_tags(count=9):
    if not os.path.exists(TAGS_FILE):
        return "" 
        
    with open(TAGS_FILE, "r", encoding="utf-8") as f:
        tags = [line.strip().replace("#", "") for line in f.readlines() if line.strip()]
        
    if not tags:
        return ""
        
    selected_tags = random.sample(tags, min(count, len(tags)))
    return " ".join([f"#{tag}" for tag in selected_tags])

def process_and_post():
    result = get_available_link()
    if not result:
        return

    affiliate_link, history = result
    print(f"Processing Link: {affiliate_link}")
    
    random_user_agent = random.choice(USER_AGENTS)
    
    # EXTRA ANTI-BOT HEADERS ADDED HERE
    headers = {
        "User-Agent": random_user_agent,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Connection": "keep-alive"
    }
    
    try:
        session = requests.Session()
        response = session.get(affiliate_link, headers=headers, allow_redirects=True, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Check for CAPTCHA block
        title_element = soup.find("span", {"id": "productTitle"})
        if title_element is None:
            print("❌ Scraping failed! Amazon ne asli page ki jagah CAPTCHA de diya hai.")
            print("Action: Yeh link skip kar rahe hain, code crash nahi hoga. Next time retry hoga.")
            return
            
        # Image extract and download
        image_element = soup.find("img", {"id": "landingImage"})
        image_url = image_element['src'] if image_element else ""
        
        image_downloaded = False
        if image_url:
            print(f"Downloading image from: {image_url}")
            img_response = requests.get(image_url, stream=True)
            if img_response.status_code == 200:
                with open(TEMP_IMAGE_FILE, 'wb') as f:
                    for chunk in img_response.iter_content(1024):
                        f.write(chunk)
                image_downloaded = True
                print("✅ Image successfully downloaded.")
            else:
                print("❌ Failed to download image.")

        # Description extract (Max 300 Chars)
        bullets = soup.find("div", {"id": "feature-bullets"})
        description = ""
        if bullets:
            list_items = bullets.find_all("li")
            description = " ".join([li.get_text(strip=True) for li in list_items])
            
        if len(description) > 300:
            short_description = description[:297] + "..."
        else:
            short_description = description

        # Files se Random Title aur Tags uthana
        final_title = get_random_title()
        final_tags = get_random_tags(count=9)

    except Exception as e:
        print(f"Scraping request failed. Error: {e}")
        return

    # 1. Telegram par bhejna
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        caption = f"🔥 **{final_title}**\n\n✨ {short_description}\n\n🛒 **Buy Here:** {affiliate_link}\n\n{final_tags}"
        
        if image_downloaded:
            telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(TEMP_IMAGE_FILE, 'rb') as photo:
                payload = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
                files = {"photo": photo}
                t_res = requests.post(telegram_api_url, data=payload, files=files)
        else:
            telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": caption, "parse_mode": "Markdown"}
            t_res = requests.post(telegram_api_url, data=payload)
            
        if t_res.status_code == 200:
            print("✅ Telegram par message chala gaya!")
        else:
            print(f"❌ Telegram Error: {t_res.text}")

    # 2. Webhook par bhejna
    if WEBHOOK_URL:
        webhook_data = {
            "title": final_title,
            "description": short_description,
            "affiliate_link": affiliate_link,
            "tags": final_tags
        }
        
        if image_downloaded:
            with open(TEMP_IMAGE_FILE, 'rb') as image_file:
                files = {"image": image_file} 
                w_res = requests.post(WEBHOOK_URL, data=webhook_data, files=files)
        else:
            w_res = requests.post(WEBHOOK_URL, data=webhook_data)
            
        if w_res.status_code == 200:
            print("✅ Webhook par data chala gaya!")
        else:
            print(f"❌ Webhook Error: {w_res.status_code}")

    # 3. Post hone ke baad History Update karna (Yahin se 7 din ka timer shuru hoga)
    history[affiliate_link] = datetime.now().isoformat()
    save_history(history)
    print("✅ History update ho gayi! Ab yeh link 7 din baad hi repeat hoga.")
    
    # 4. Clean Up
    if os.path.exists(TEMP_IMAGE_FILE):
        os.remove(TEMP_IMAGE_FILE)
        print("🧹 Temporary image deleted.")

if __name__ == "__main__":
    process_and_post()
