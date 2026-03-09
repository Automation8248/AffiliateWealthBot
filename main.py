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
TEMP_IMAGE_FILE = "temp_image.jpg"
TITLES_FILE = "titles.txt"
TAGS_FILE = "tags.txt"

# --- 50+ RANDOM USER AGENTS (PURI LIST) ---
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
                return data if isinstance(data, dict) else {}
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
    return random.choice(titles) if titles else "Check Out This Awesome Product! 🔥"

def get_random_tags(count=9):
    if not os.path.exists(TAGS_FILE):
        return "" 
    with open(TAGS_FILE, "r", encoding="utf-8") as f:
        tags = [line.strip().replace("#", "") for line in f.readlines() if line.strip()]
    if not tags: return ""
    selected_tags = random.sample(tags, min(count, len(tags)))
    return " ".join([f"#{tag}" for tag in selected_tags])

def process_and_post():
    result = get_available_link()
    if not result:
        return

    affiliate_link, history = result
    print(f"Processing Link: {affiliate_link}")
    random_user_agent = random.choice(USER_AGENTS)
    
    # --- START REAL BROWSER (PLAYWRIGHT) ---
    with sync_playwright() as p:
        print("Asli browser open kar rahe hain...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=random_user_agent,
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            # 1. Page load karo
            page.goto(affiliate_link, timeout=45000)
            print("Page par pohoch gaye, insaan ki tarah wait kar rahe hain...")
            
            # 2. Human Behavior: 2 se 5 second wait karna
            time.sleep(random.uniform(2.0, 5.0))
            
            # 3. Screenshot 1: Load hone ke turant baad
            page.screenshot(path="screenshot_1_loaded.png")
            print("📸 Screenshot liya: Page Load.")

            # 4. Human Behavior: Mouse hilaana
            page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            time.sleep(random.uniform(0.5, 1.5))
            
            # 5. Human Behavior: Niche Scroll karna product details padhne ke liye
            print("Niche scroll kar rahe hain...")
            page.mouse.wheel(0, random.randint(400, 1000))
            time.sleep(random.uniform(1.0, 3.0))
            
            # 6. Screenshot 2: Scroll karne ke baad
            page.screenshot(path="screenshot_2_scrolled.png")
            print("📸 Screenshot liya: Scroll karne ke baad.")

            # --- EXTRACT DATA ---
            # Check for CAPTCHA
            if page.locator("#captchacharacters").count() > 0:
                print("❌ Amazon ne abhi bhi CAPTCHA de diya (IP block).")
                page.screenshot(path="screenshot_error_captcha.png")
                browser.close()
                return
            
            # Image extract karna
            image_url = ""
            img_locator = page.locator("#landingImage")
            if img_locator.count() > 0:
                image_url = img_locator.get_attribute("src")

            # Description extract karna
            description = ""
            bullets_locator = page.locator("#feature-bullets li")
            if bullets_locator.count() > 0:
                description = " ".join(bullets_locator.all_inner_texts()).replace('\n', ' ')

        except Exception as e:
            print(f"Scraping failed inside browser. Error: {e}")
            page.screenshot(path="screenshot_crash.png")
            browser.close()
            return

        browser.close()
        print("Browser band kar diya. Data mil gaya.")

    # --- IMAGE DOWNLOAD ---
    image_downloaded = False
    if image_url:
        img_response = requests.get(image_url, stream=True)
        if img_response.status_code == 200:
            with open(TEMP_IMAGE_FILE, 'wb') as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)
            image_downloaded = True

    # 300 Chars Limit Description
    short_description = description[:297] + "..." if len(description) > 300 else description
    
    # Files se Random Title (Keval 1) aur Tags (Keval 9) select karna
    final_title = get_random_title()
    final_tags = get_random_tags(count=9)

    # --- 1. TELEGRAM POST (ONLY IMAGE, TITLE, LINK) ---
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_caption = f"🔥 **{final_title}**\n\n🛒 **Buy Here:** {affiliate_link}"
        
        if image_downloaded:
            t_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(TEMP_IMAGE_FILE, 'rb') as photo:
                payload = {"chat_id": TELEGRAM_CHAT_ID, "caption": telegram_caption, "parse_mode": "Markdown"}
                t_res = requests.post(t_url, data=payload, files={"photo": photo})
        else:
            t_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": telegram_caption, "parse_mode": "Markdown"}
            t_res = requests.post(t_url, data=payload)
            
        if t_res.status_code == 200:
            print("✅ Telegram par message gaya!")
        else:
            print(f"❌ Telegram Error: {t_res.text}")

    # --- 2. WEBHOOK POST (ALL DATA: TITLE, DESCRIPTION, LINK, TAGS, IMAGE) ---
    if WEBHOOK_URL:
        webhook_data = {
            "title": final_title,
            "description": short_description,
            "affiliate_link": affiliate_link,
            "tags": final_tags,
            "image_url": image_url
        }
        if image_downloaded:
            with open(TEMP_IMAGE_FILE, 'rb') as image_file:
                w_res = requests.post(WEBHOOK_URL, data=webhook_data, files={"image": image_file})
        else:
            w_res = requests.post(WEBHOOK_URL, data=webhook_data)
            
        if w_res.status_code == 200:
            print("✅ Webhook par data gaya!")
        else:
            print(f"❌ Webhook Error: {w_res.status_code}")

    # --- HISTORY UPDATE (7-DAY COOLDOWN START) ---
    history[affiliate_link] = datetime.now().isoformat()
    save_history(history)
    print("✅ History update ho gayi! Ab yeh link 7 din baad hi repeat hoga.")
    
    # --- CLEANUP ---
    if os.path.exists(TEMP_IMAGE_FILE):
        os.remove(TEMP_IMAGE_FILE)

if __name__ == "__main__":
    process_and_post()
