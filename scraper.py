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

# Ollama API Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST") # Aapke API ka URL
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY") # Aapki API Key

COOLDOWN_DAYS = 5
HISTORY_FILE = "history.json"
LINKS_FILE = "links.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36"
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                else:
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

def shorten_title_with_ollama(long_title):
    print("Ollama API se title short kar rahe hain...")
    prompt = f"Rewrite this Amazon product title to be catchy and short for a Pinterest pin (maximum 5 to 8 words). Just give the title, no quotes, no extra text: {long_title}"
    
    try:
        from ollama import Client
        
        # Agar API Key hai toh Header mein lagayenge, warna normal Client banega
        headers = {}
        if OLLAMA_API_KEY:
            headers = {'Authorization': f'Bearer {OLLAMA_API_KEY}'}
            
        client = Client(host=OLLAMA_HOST, headers=headers)
        
        # Aapka diya hua logic (qwen3.5)
        response = client.chat(
            model='qwen3.5',
            messages=[{'role': 'user', 'content': prompt}],
        )
        
        # Response extract karna
        short_title = response['message']['content'].strip()
        
        if short_title.startswith('"') and short_title.endswith('"'):
            short_title = short_title[1:-1]
            
        print(f"Ollama API Shortened Title: {short_title}")
        return short_title
    except Exception as e:
        print(f"Ollama API Error: {e}")
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
        "Referer": "https://www.google.com/" 
    }
    
    try:
        session = requests.Session()
        response = session.get(affiliate_link, headers=headers, allow_redirects=True, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        
        title_element = soup.find("span", {"id": "productTitle"})
        if title_element is None:
            print("❌ Scraping failed! Amazon ne asli page ki jagah CAPTCHA de diya hai.")
            return 
            
        raw_title = title_element.get_text(strip=True)
        
        image_element = soup.find("img", {"id": "landingImage"})
        image_url = image_element['src'] if image_element else ""
        
        bullets = soup.find("div", {"id": "feature-bullets"})
        description = ""
        if bullets:
            list_items = bullets.find_all("li")
            description = " ".join([li.get_text(strip=True) for li in list_items])
            
        # Ollama API ko call kar raha hai
        final_title = shorten_title_with_ollama(raw_title)

    except Exception as e:
        print(f"Scraping request failed. Error: {e}")
        return

    # 1. Telegram par bhejna
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        caption = f"🔥 **{final_title}**\n\n✨ {description[:120]}...\n\n🛒 **Buy Here:** {affiliate_link}"
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
