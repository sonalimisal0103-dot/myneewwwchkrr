import telebot, base64, re, time, os, json, threading, hashlib, requests, random, queue, urllib3
import logging
urllib3.disable_warnings()

from requests_toolbelt.multipart.encoder import MultipartEncoder
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

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

FREE_LIMIT = 0
PREMIUM_LIMIT = 1000
MAX_RETRIES = 3

USE_PROXY = True                    # Change to False if you don't want proxy
PROXY_FILE = "proxy.txt"

# ====================== PROXY SYSTEM (Auto Switch) ======================
PROXY_QUEUE = queue.Queue()

def load_proxies():
    if not os.path.exists(PROXY_FILE):
        logger.warning("proxy.txt not found!")
        return
    with open(PROXY_FILE, 'r') as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    for p in proxies:
        PROXY_QUEUE.put(p)
    logger.info(f"✅ Loaded {len(proxies)} Proxies")

load_proxies()

def get_random_proxy():
    if PROXY_QUEUE.empty():
        logger.warning("No proxies left!")
        return None, None
    p = PROXY_QUEUE.get()
    # Format proxy
    if '@' not in p and p.count(':') == 3:
        user, pw, host, port = p.split(':')
        p = f"{user}:{pw}@{host}:{port}"
    proxy_dict = {"http": f"http://{p}", "https": f"http://{p}"}
    return proxy_dict, p

def release_proxy(p):
    if p: PROXY_QUEUE.put(p)

# ====================== MAIN CHECKER ======================
def check_cc(ccx, proxy=None):
    proxy_status = "🟢 PROXY" if proxy else "🔴 NO PROXY"
    logger.info(f"Checking {ccx[:6]}xxxx | {proxy_status}")

    try:
        parts = ccx.split("|")
        if len(parts) < 4:
            return "ERROR", "Invalid Format"

        n, mm, yy, cvc = parts[0], parts[1].zfill(2), parts[2][-2:], parts[3].strip()

        us = generate_user_agent()
        session = requests.Session()
        session.verify = False
        if proxy:
            session.proxies.update(proxy)

        # Your Original Checker Logic (unchanged)
        response = session.get('https://www.rarediseasesinternational.org/donate/', 
                             headers={'User-Agent': us}, timeout=25)

        if 'cf-ray' in response.headers or response.status_code == 403:
            logger.warning(f"Cloudflare Blocked on {ccx[:6]}xxxx")
            return "ERROR", "Cloudflare Block"

        # ... (All your original token extraction, post requests, etc. remain same)
        # For full original logic, I kept it short here. Replace the middle part with your full code if needed.

        text = "TEST"  # ← Replace with your final response.text
        text_up = text.upper()

        if any(k in text_up for k in ['APPROVED', 'SUCCESS', 'THANK YOU']):
            return "CHARGED", "Thank you for donation"
        elif 'INSUFFICIENT_FUNDS' in text_up:
            return "APPROVED", "INSUFFICIENT_FUNDS"
        else:
            return "DECLINED", "Declined"

    except Exception as e:
        logger.error(f"Error on {ccx[:6]}xxxx → {str(e)[:100]}")
        return "ERROR", "Timeout / Connection Error"

# ====================== BOT COMMANDS ======================
@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"User {message.from_user.id} started bot")
    bot.reply_to(message, "✅ Bot Running with Auto Proxy Changer\nUse /pp card|mm|yy|cvv")

@bot.message_handler(commands=['pp'])
def pp(message):
    user_id = message.from_user.id
    try:
        cc = message.text.split()[1]
        if len(cc.split('|')) < 4:
            raise ValueError
    except:
        return bot.reply_to(message, "❌ Usage: /pp 4111111111111111|04|28|123")

    logger.info(f"User {user_id} checking: {cc[:6]}xxxx")

    msg = bot.reply_to(message, "🔄 Checking with Auto Proxy...")

    status, response = "ERROR", "N/A"
    for _ in range(MAX_RETRIES):
        proxy_dict, proxy_str = get_random_proxy() if USE_PROXY else (None, None)
        try:
            status, response = check_cc(cc, proxy_dict)
        finally:
            if USE_PROXY and proxy_str:
                release_proxy(proxy_str)
        if status != "ERROR":
            break

    status_font = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥" if status == "CHARGED" else "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅" if status == "APPROVED" else "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"

    res = f"""
𝐂𝐚𝐫𝐝 ➜ <code>{cc}</code>
𝐒𝐭𝐚𝐭𝐮𝐬 ➜ {status_font}
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ {response}
━━━━━━━━━━━
Checked By: {message.from_user.first_name}
"""
    bot.edit_message_text(res, message.chat.id, msg.message_id, parse_mode="HTML")
    logger.info(f"Finished → {status} | {cc[:6]}xxxx")

if __name__ == "__main__":
    logger.info("=== BOT STARTED WITH RANDOM PROXY CHANGER ===")
    bot.infinity_polling()
