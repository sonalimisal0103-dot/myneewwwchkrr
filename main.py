import telebot, base64, re, time, os, json, threading, hashlib, requests, datetime, queue, urllib3
import logging
urllib3.disable_warnings()

from requests_toolbelt.multipart.encoder import MultipartEncoder
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

# ====================== LOGGING SETUP ======================
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

USE_PROXY = False
PROXY_FILE = "proxy.txt"

# Files
USERS_FILE = 'Data/users.txt'
PREMIUM_FILE = 'Data/premium.txt'
BANNED_FILE = 'Data/banned.txt'
STATS_FILE = 'stats.json'
CHARGED_FILE = 'Data/charged.txt'
APPROVED_FILE = 'Data/approved.txt'

os.makedirs('Data', exist_ok=True)
for f in [USERS_FILE, PREMIUM_FILE, BANNED_FILE, APPROVED_FILE, CHARGED_FILE]:
    if not os.path.exists(f): open(f, 'w').close()

if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, 'w') as f: 
        json.dump({"charged": 0, "approved": 0, "total_users": 0, "premium_users": 0, "banned_users": 0}, f)

bot = telebot.TeleBot(BOT_TOKEN)

logger.info(f"Bot Started | Proxy: {'ENABLED' if USE_PROXY else 'DISABLED'} | Admin: {ADMIN_ID}")

# ====================== CACHES & FUNCTIONS ======================
ACTIVE_JOBS = {}
ACTIVE_USERS_PP = {}
ACTIVE_USERS_MPP = {}
USER_ACTIVE_JOB = {}
STATS_LOCK = threading.Lock()

def get_stats():
    with STATS_LOCK:
        try:
            with open(STATS_FILE, 'r') as f: return json.load(f)
        except: return {"charged": 0, "approved": 0, "total_users": 0, "premium_users": 0, "banned_users": 0}

def save_stats(stats):
    with STATS_LOCK:
        try:
            with open(STATS_FILE, 'w') as f: json.dump(stats, f)
        except: pass

def save_unique_cc(filepath, cc, note):
    cc_num = cc.split('|')[0].strip()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            if cc_num in f.read(): return
    except: pass
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"{cc} - {note}\n")

def is_admin(user_id): return user_id == ADMIN_ID

def is_premium(user_id):
    with open(PREMIUM_FILE, 'r') as f:
        for line in f:
            if str(user_id) in line:
                parts = line.strip().split('|')
                if len(parts) > 1:
                    exp = float(parts[1])
                    if exp == 0 or time.time() < exp: return True
                return True
    return False

def is_banned(user_id):
    with open(BANNED_FILE, 'r') as f:
        for line in f:
            if str(user_id) in line:
                parts = line.strip().split('|')
                if len(parts) > 1:
                    exp = float(parts[1])
                    if exp == 0 or time.time() < exp: return True
                return True
    return False

def add_user(user_id):
    with open(USERS_FILE, 'a+') as f:
        f.seek(0)
        if str(user_id) not in f.read():
            f.write(str(user_id) + '\n')
            s = get_stats()
            s["total_users"] += 1
            save_stats(s)

# ====================== CHECKER WITH LOGGING ======================
def check_cc(ccx, proxy=None):
    proxy_status = "🟢 PROXY USED" if proxy else "🔴 NO PROXY"
    logger.info(f"Checking {ccx[:6]}xxxx | {proxy_status}")

    try:
        parts = ccx.split("|")
        n, mm, yy, cvc = parts[0], parts[1].zfill(2), parts[2][-2:], parts[3].strip()

        us = generate_user_agent()
        session = requests.Session()
        session.verify = False
        if proxy:
            session.proxies.update(proxy)

        logger.info(f"[{ccx[:6]}xxxx] → Loading Donate Page...")
        response = session.get('https://www.rarediseasesinternational.org/donate/', 
                             headers={'User-Agent': us}, timeout=25)

        if 'cf-ray' in response.headers or response.status_code == 403:
            logger.warning(f"[{ccx[:6]}xxxx] → Cloudflare Blocked")
            return "ERROR", "Cloudflare Block"

        # ... (Your original token extraction and payment logic remains same)

        # Final Result Log
        logger.info(f"[{ccx[:6]}xxxx] → Result: {status} | {response}")
        return status, response

    except Exception as e:
        logger.error(f"[{ccx[:6]}xxxx] → ERROR: {str(e)[:100]}")
        if "timeout" in str(e).lower():
            return "ERROR", "Read Timeout"
        return "ERROR", "Request Error"

# ====================== COMMANDS ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")
        return
    add_user(user_id)
    logger.info(f"User {user_id} started bot")
    bot.reply_to(message, "✅ Bot is Online!\nUse /pp for single check")

@bot.message_handler(commands=['pp'])
def pp(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        return bot.reply_to(message, "𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")

    try:
        cc = message.text.split()[1]
    except:
        return bot.reply_to(message, "Usage: /pp 4111111111111111|04|28|123")

    logger.info(f"User {user_id} checking: {cc[:6]}xxxx")

    msg = bot.reply_to(message, "🔄 Processing...")

    status, response = "ERROR", "N/A"
    for _ in range(MAX_RETRIES):
        proxy_dict = None
        if USE_PROXY:
            # proxy logic here if needed
            pass
        status, response = check_cc(cc)
        if status != "ERROR": break

    # Save stats and result (your original code)
    if status == "CHARGED":
        s = get_stats(); s["charged"] += 1; save_stats(s)
        save_unique_cc(CHARGED_FILE, cc, response)
    elif status == "APPROVED":
        s = get_stats(); s["approved"] += 1; save_stats(s)
        save_unique_cc(APPROVED_FILE, cc, response)

    status_font = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥" if status == "CHARGED" else "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅" if status == "APPROVED" else "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝"

    res = f"""
𝐂𝐚𝐫𝐝 ➜ <code>{cc}</code>
𝐒𝐭𝐚𝐭𝐮𝐬 ➜ {status_font}
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ {response}
━━━━━━━━━━━
Checked By: {message.from_user.first_name}
"""
    bot.edit_message_text(res, message.chat.id, msg.message_id, parse_mode="HTML")
    logger.info(f"Check Finished → {status} for {cc[:6]}xxxx")

if __name__ == "__main__":
    logger.info("=== BOT IS RUNNING ===")
    bot.infinity_polling()
