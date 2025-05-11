import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import os
import time
import traceback
import schedule
from datetime import datetime

# Twilio WhatsApp configuration
TWILIO_SID = os.environ['TWILIO_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
FROM_WHATSAPP_NUMBER = os.environ['FROM_WHATSAPP_NUMBER']
TO_WHATSAPP_NUMBER = os.environ['TO_WHATSAPP_NUMBER']

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(message):
    try:
        message = client.messages.create(
            body=message,
            from_=FROM_WHATSAPP_NUMBER,
            to=TO_WHATSAPP_NUMBER
        )
        print(f"✅ Sent message with SID: {message.sid}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")

def fetch_hacker_news():
    try:
        url = "https://thehackernews.com/search/label/Vulnerability"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        posts = soup.find_all('div', class_='body-post')[:3]
        messages = []

        for post in posts:
            title = post.find('h2').text.strip()
            link = post.find('a')['href']
            messages.append(f"[Hacker News] {title}\n{link}")

        return messages
    except Exception as e:
        print(f"❌ Error fetching from Hacker News: {e}")
        return []

def load_sent_entries():
    try:
        with open('sent_entries.txt', 'r') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_sent_entries(entries):
    with open('sent_entries.txt', 'w') as f:
        f.write('\n'.join(entries))

def fetch_exploit_db():
    try:
        url = "https://www.exploit-db.com/rss.xml"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item')

        sent_entries = load_sent_entries()
        new_entries = set()
        messages = []

        for item in items:
            title = item.title.text
            link = item.link.text
            entry_id = f"{title}|{link}"

            if entry_id not in sent_entries:
                messages.append(f"[Exploit-DB] {title}\n{link}")
                new_entries.add(entry_id)

        sent_entries.update(new_entries)
        save_sent_entries(sent_entries)

        return messages
    except Exception as e:
        print(f"❌ Error fetching from Exploit-DB: {e}")
        return []

def main():
    print(f"\n⏰ Running at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    hn_messages = fetch_hacker_news()
    print(f"🔍 Found {len(hn_messages)} Hacker News updates")

    edb_messages = fetch_exploit_db()
    print(f"🔍 Found {len(edb_messages)} Exploit-DB updates")

    all_messages = hn_messages + edb_messages
    print(f"📤 Sending {len(all_messages)} messages...")

    for msg in all_messages:
        send_whatsapp_message(msg)
        time.sleep(1.5)  # Prevent hitting rate limits

# Scheduler setup for every 5 minutes
if __name__ == "__main__":
    print("🚀 Starting Cyber Security WhatsApp Bot on Render...")
    schedule.every(5).minutes.do(main)

    while True:
        schedule.run_pending()
        time.sleep(60)
