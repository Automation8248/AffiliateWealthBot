import os
import random
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- CONFIGURATION ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") 
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

COOLDOWN_DAYS = 5
HISTORY_FILE = "history.json"
LINKS_FILE = "links.txt"

# --- 100+ USER AGENTS ---
USER_AGENTS = [f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.{random.randint(1000, 9999)}.{random.randint(10, 99)} Safari/537.36" for _ in range(100)]

def clean_text(text):
    """Stars aur Hashtags hatane ke liye"""
    return re.sub(r'[*#]', '', text).strip()

def process_with_openrouter(raw_title, raw_desc):
    """OpenRouter Fallback Logic"""
    if not OPENROUTER_API_KEY: return None, None, "No API Key"
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Short title (8 words) and catchy description (400 chars max, no # or *) for: {raw_title}. Output JSON format."
    data = {"model": "google/gemini-2.0-flash-lite:free", "messages": [{"role": "user", "content": prompt}]}
    
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
        if res.status_code == 402: return None, None, "Payment Required/Limit Reached"
        
        content = res.json()['choices'][0]['message']['content']
        # JSON parsing logic
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return clean_text(result.get("title", "")), clean_text(result.get("description", ""))[:400], None
    except: pass
    return None, None, "API Error"

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
    
    if not available: return
    affiliate_link = random.choice(available)

    try:
        res = requests.get(affiliate_link, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=15)
        soup = BeautifulSoup(res.content, "html.parser")
        
        title_node = soup.find("span", {"id": "productTitle"})
        if not title_node: return
        
        raw_title = title_node.get_text(strip=True)
        img_url = soup.find("img", {"id": "landingImage"})['src']
        
        # AI Logic
        f_title, f_desc, err = process_with_openrouter(raw_title, "Kitchen Accessory")
        alert = ""
        
        if err: # Fallback System
            f_title = clean_text(raw_title[:80])
            f_desc = "Check out this amazing kitchen find on Amazon! Limited time deal."
            alert = "\n\n<i>⚠️ OpenRouter limit reached. Using default system.</i>"

        # Telegram Fix: URL ko manual construct karna
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            # Token se link/bracket hatane ke liye cleaning
            clean_token = TELEGRAM_BOT_TOKEN.replace("https://api.telegram.org/bot", "").replace("[", "").replace("]", "").strip()
            t_url = f"https://api.telegram.org/bot{clean_token}/sendPhoto"
            caption = f"🔥 <b>{f_title}</b>\n\n{f_desc}\n\n🛒 <b>Buy Here:</b> {affiliate_link}{alert}"
            requests.post(t_url, data={"chat_id": TELEGRAM_CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"})

        # Webhook
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"title": f_title, "image": img_url, "link": affiliate_link, "desc": f_desc})

        history[affiliate_link] = now.isoformat()
        with open(HISTORY_FILE, "w") as f: json.dump(history, f, indent=4)
        print("✅ Done")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    process_and_post()
