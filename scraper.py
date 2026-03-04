import os
import time
import requests
from playwright.sync_api import sync_playwright

# GitHub Secrets
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL') # Naya Webhook Secret

def send_to_telegram(image_url, caption, affiliate_url):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    final_caption = f"{caption}\n\n🛒 **Grab it here:** {affiliate_url}"
    
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'caption': final_caption,
        'parse_mode': 'Markdown'
    }
    
    if image_url:
        payload['photo'] = image_url
        response = requests.post(api_url, data=payload)
    else:
        text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload['text'] = final_caption
        del payload['caption']
        response = requests.post(text_url, data=payload)
        
    print("Telegram Response:", response.json())

def send_to_webhook(shortened_text, image_url, affiliate_url):
    if not WEBHOOK_URL:
        print("Webhook URL is missing. Skipping webhook step.")
        return
        
    payload = {
        "content": shortened_text,
        "image_url": image_url,
        "affiliate_link": affiliate_url
    }
    
    try:
        # Webhook par JSON format mein data bhej rahe hain
        response = requests.post(WEBHOOK_URL, json=payload)
        print(f"Webhook Status Code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send to Webhook: {e}")

def run_automation():
    try:
        with open('links.txt', 'r') as file:
            links = file.readlines()
    except FileNotFoundError:
        print("links.txt not found!")
        return

    if not links:
        print("No links left in links.txt")
        return
        
    target_url = links[0].strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()

        # STEP 1: Scrape Amazon
        print(f"Visiting Amazon: {target_url}")
        page.goto(target_url, timeout=60000)
        
        try:
            title = page.locator('#productTitle').inner_text().strip()
        except:
            title = "Title not found"
            
        try:
            desc = page.locator('#feature-bullets').inner_text().strip()
        except:
            desc = "Description not found"
            
        try:
            img_element = page.locator('#landingImage')
            img_url = img_element.get_attribute('data-old-hires') or img_element.get_attribute('src')
        except:
            img_url = None

        print("Amazon Data Scraped!")

        # STEP 2: Shorten text via deepai.org
        print("Visiting deepai.org to shorten text...")
        page.goto('https://deepai.org/chat')
        
        prompt = f"Summarize this Amazon product into 2 catchy lines for a promo post. Don't use hashtags.\n\nTitle: {title}\nDescription: {desc}"
        
        try:
            chat_box = page.locator('textarea') 
            chat_box.wait_for(state="visible", timeout=10000)
            chat_box.fill(prompt)
            chat_box.press('Enter')
            
            time.sleep(10) # AI ko sochne ka time de rahe hain
            
            responses = page.locator('.chat-message-text').all_inner_texts()
            if responses:
                shortened_text = responses[-1].strip() 
            else:
                shortened_text = f"🔥 Checkout this amazing product!\n{title[:100]}..."
                
        except Exception as e:
            print(f"DeepAI UI issue: {e}")
            shortened_text = f"🔥 Checkout this amazing product!\n{title[:100]}..."

        browser.close()

        # STEP 3: Send to Telegram AND Webhook
        print("Sending data to destinations...")
        send_to_telegram(img_url, shortened_text, target_url)
        send_to_webhook(shortened_text, img_url, target_url)
        
        # Update File
        with open('links.txt', 'w') as file:
            file.writelines(links[1:])
        print("Done! Link removed from links.txt")

if __name__ == "__main__":
    run_automation()
