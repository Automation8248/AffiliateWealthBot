import os
import random
import time
import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# --- SECRETS & CONFIGURATION ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") 
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

COOLDOWN_DAYS = 7 
HISTORY_FILE = "history.json"
LINKS_FILE = "links.txt"
TITLES_FILE = "titles.txt"
TAGS_FILE = "tags.txt"
TEMP_IMAGE_FILE = "temp_image.jpg"

# --- 50+ RANDOM USER AGENTS ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

# --- CATBOX UPLOAD (10 TRIES) ---
def upload_to_catbox(file_path, retries=10):
    url = "https://catbox.moe/user/api.php"
    for i in range(retries):
        try:
            with open(file_path, 'rb') as f:
                data = {'reqtype': 'fileupload'}
                files = {'fileToUpload': f}
                response = requests.post(url, data=data, files=files, timeout=30)
                if response.status_code == 200 and "catbox.moe" in response.text:
                    return response.text.strip()
        except: pass
        time.sleep(2)
    return None

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f: json.dump(history, f, indent=4)

def process_and_post():
    # --- LINK SELECTION ---
    if not os.path.exists(LINKS_FILE): return
    with open(LINKS_FILE, "r") as f:
        all_links = [l.strip() for l in f.readlines() if l.strip()]
    history = load_history()
    available = [l for l in all_links if l not in history or (datetime.now() - datetime.fromisoformat(history[l]) >= timedelta(days=COOLDOWN_DAYS))]
    if not available: return
    link = random.choice(available)
    
    image_url = ""
    description = ""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = context.new_page()
        
        try:
            print(f"Opening: {link}")
            page.goto(link, timeout=60000, wait_until="domcontentloaded")
            
            # --- THE FIX: CONTINUE SHOPPING BYPASS ---
            # Hum multiple tareeko se button ko dhoondh rahe hain (ID, Text aur Class)
            continue_selectors = [
                "a.a-link-normal[href='/']", 
                "text='Continue shopping'", 
                ".a-button-text",
                "button:has-text('Continue shopping')"
            ]
            
            for selector in continue_selectors:
                btn = page.locator(selector).first
                if btn.count() > 0:
                    print(f"⚠️ Interface Detected! Clicking '{selector}'...")
                    btn.hover()
                    time.sleep(1)
                    btn.click(force=True) # Force click taaki koi layer use rok na sake
                    time.sleep(6) # Main page load hone ka wait
                    break

            # --- HUMAN BEHAVIOR ---
            time.sleep(5)
            page.mouse.wheel(0, 1000) # Niche scroll
            time.sleep(2)
            page.mouse.wheel(0, -500) # Upar scroll

            # --- EXTRACTION ---
            page.wait_for_selector("#landingImage", timeout=15000)
            image_url = page.locator("#landingImage").get_attribute("src")
            description = " ".join(page.locator("#feature-bullets li").all_inner_texts())[:290]

        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="error_capture.png")
        finally:
            browser.close()

    # --- DOWNLOAD, CATBOX & POSTING ---
    if image_url:
        img_data = requests.get(image_url).content
        with open(TEMP_IMAGE_FILE, 'wb') as f: f.write(img_data)
        
        catbox_link = upload_to_catbox(TEMP_IMAGE_FILE)
        
        # Webhook Post
        if WEBHOOK_URL:
            payload = {
                "title": "Amazing Find! 🔥", # Aap titles.txt wala logic yahan rakh sakte hain
                "description": description,
                "affiliate_link": link,
                "image_url": catbox_link
            }
            requests.post(WEBHOOK_URL, json=payload)
            print("✅ Data sent to Webhook!")

        # Telegram Post
        if TELEGRAM_BOT_TOKEN:
            caption = f"🛒 **Product Found!**\n\n🔗 {link}"
            with open(TEMP_IMAGE_FILE, 'rb') as photo:
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", 
                              data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                              files={"photo": photo})

        # History Update
        history[link] = datetime.now().isoformat()
        save_history(history)
        if os.path.exists(TEMP_IMAGE_FILE): os.remove(TEMP_IMAGE_FILE)

if __name__ == "__main__":
    process_and_post()
