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

# --- CATBOX UPLOAD (10 TRIES) ---
def upload_to_catbox(file_path, retries=10):
    url = "https://catbox.moe/user/api.php"
    for i in range(retries):
        try:
            with open(file_path, 'rb') as f:
                data = {'reqtype': 'fileupload'}
                files = {'fileToUpload': f}
                print(f"🔄 Catbox upload try {i+1}/{retries}...")
                response = requests.post(url, data=data, files=files, timeout=30)
                if response.status_code == 200 and "catbox.moe" in response.text:
                    return response.text.strip()
        except Exception as e:
            print(f"⚠️ Catbox upload fail hua (Try {i+1}): {e}")
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

def get_available_link():
    if not os.path.exists(LINKS_FILE): return None
    with open(LINKS_FILE, "r") as f:
        all_links = [l.strip() for l in f.readlines() if l.strip()]
    history = load_history()
    now = datetime.now()
    available = [l for l in all_links if l not in history or (now - datetime.fromisoformat(history[l]) >= timedelta(days=COOLDOWN_DAYS))]
    return (random.choice(available), history) if available else None

def get_random_title():
    if not os.path.exists(TITLES_FILE): return "Awesome Product! 🔥"
    with open(TITLES_FILE, "r", encoding="utf-8") as f:
        titles = [l.strip() for l in f.readlines() if l.strip()]
    return random.choice(titles) if titles else "Awesome Product! 🔥"

def get_random_tags():
    if not os.path.exists(TAGS_FILE): return ""
    with open(TAGS_FILE, "r", encoding="utf-8") as f:
        tags = [l.strip().replace("#", "") for l in f.readlines() if l.strip()]
    return " ".join([f"#{t}" for t in random.sample(tags, min(9, len(tags)))]) if tags else ""

def process_and_post():
    result = get_available_link()
    if not result: return
    link, history = result
    
    image_url = ""
    description = ""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = context.new_page()
        
        try:
            print(f"Processing Link: {link}")
            page.goto(link, timeout=50000, wait_until="domcontentloaded")
            
            # --- 1. VISUAL & DOM MATCHING LOGIC (As per your image URL) ---
            print("👁️ Checking interface for the 'Continue shopping' button...")
            try:
                # Combining multiple exact selectors found in the Amazon "Continue shopping" page HTML
                # This guarantees it finds the button no matter how Amazon formats it
                continue_btn = page.locator("button:has-text('Continue shopping'), input[value='Continue shopping'], span.a-button-inner > a, text=/Continue shopping/i").first
                
                # Wait up to 3 seconds for it to appear
                continue_btn.wait_for(state="visible", timeout=3000)
                
                if continue_btn.is_visible():
                    print("⚠️ Match found! 'Continue shopping' button detected exactly as per your image.")
                    continue_btn.hover()
                    time.sleep(random.uniform(1.0, 2.0))
                    
                    # Force click to ensure it triggers even if Amazon tries to block automated clicks
                    continue_btn.click(delay=random.randint(200, 500), force=True)
                    
                    print("✅ Click kar diya, main page ka wait kar rahe hain...")
                    time.sleep(random.uniform(5.0, 7.0))
            except Exception:
                print("➡️ Normal page load, Continue Shopping button nahi mila. Proceeding...")
            
            # --- 2. HUMAN BEHAVIOR: WAIT & SCROLL ---
            print("Main page par pohoch gaye, insaan ki tarah ruk rahe hain...")
            time.sleep(random.uniform(5.0, 7.0))
            
            page.screenshot(path="screenshot_1_loaded.png")
            print("📸 Screenshot liya: Page Load.")

            print("Niche aur upar scroll kar rahe hain...")
            page.mouse.wheel(0, random.randint(600, 1000))
            time.sleep(random.uniform(2.0, 3.0))
            page.mouse.wheel(0, -random.randint(300, 600))
            
            page.screenshot(path="screenshot_2_scrolled.png")
            
            # --- 3. EXTRACT IMAGE AND DESCRIPTION ---
            print("🔍 Image aur Description dhoondh rahe hain...")
            try:
                page.wait_for_selector("#landingImage", timeout=15000)
                image_url = page.locator("#landingImage").get_attribute("src")
                print("✅ Product ki Image URL mil gayi.")
            except Exception:
                print("⚠️ Image nahi mili.")

            try:
                page.wait_for_selector("#feature-bullets li", timeout=15000)
                description = " ".join(page.locator("#feature-bullets li").all_inner_texts()).replace('\n', ' ')
                print("✅ Product ka Description mil gaya.")
            except Exception:
                print("⚠️ Description nahi mila.")

        except Exception as e:
            print(f"Browser Error: {e}")
            page.screenshot(path="screenshot_crash.png")
            browser.close()
            return
            
        browser.close()
        print("Browser band kar diya. Data extraction complete.")

    # --- IMAGE DOWNLOAD ---
    image_downloaded = False
    if image_url:
        img_res = requests.get(image_url, stream=True)
        if img_res.status_code == 200:
            with open(TEMP_IMAGE_FILE, 'wb') as f:
                for chunk in img_res.iter_content(1024):
                    f.write(chunk)
            image_downloaded = True

    # --- CATBOX UPLOAD ---
    final_image_link = image_url  
    if image_downloaded:
        print("🚀 Image Catbox par upload kar rahe hain...")
        catbox_link = upload_to_catbox(TEMP_IMAGE_FILE, retries=10)
        if catbox_link:
            print(f"✅ Catbox Upload Success: {catbox_link}")
            final_image_link = catbox_link
        else:
            print("❌ Catbox Upload fail ho gaya.")

    # --- PREPARE FINAL DATA ---
    short_description = description[:290] + "..." if len(description) > 290 else description
    final_title = get_random_title()
    final_tags = get_random_tags()

    # --- 1. TELEGRAM POST ---
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_caption = f"🔥 **{final_title}**\n\n🛒 **Buy Here:** {link}"
        if image_downloaded:
            t_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(TEMP_IMAGE_FILE, 'rb') as photo:
                requests.post(t_url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": telegram_caption, "parse_mode": "Markdown"}, files={"photo": photo})
        else:
            t_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(t_url, data={"chat_id": TELEGRAM_CHAT_ID, "text": telegram_caption, "parse_mode": "Markdown"})
        print("✅ Telegram process complete!")

    # --- 2. WEBHOOK POST ---
    if WEBHOOK_URL:
        webhook_data = {
            "title": final_title,
            "description": short_description,
            "affiliate_link": link,
            "tags": final_tags,
            "image_url": final_image_link  
        }
        if image_downloaded:
            with open(TEMP_IMAGE_FILE, 'rb') as image_file:
                requests.post(WEBHOOK_URL, data=webhook_data, files={"image": image_file})
        else:
            requests.post(WEBHOOK_URL, data=webhook_data)
        print("✅ Webhook process complete!")

    # --- HISTORY UPDATE & CLEANUP ---
    history[link] = datetime.now().isoformat()
    save_history(history)
    print("✅ History update ho gayi!")
    
    if os.path.exists(TEMP_IMAGE_FILE):
        os.remove(TEMP_IMAGE_FILE)

if __name__ == "__main__":
    process_and_post()
