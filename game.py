import os
import json
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

DATA_FILE = "users.json"

# ----------------------------
# Basit veri katmanı
# ----------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ----------------------------
# Bot fonksiyonları
# ----------------------------
def start(update, context):
    user = update.effective_user
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"👋 Selam {user.first_name}!  
Tap-To-Earn oyununa hoş geldin!  
Puan kazanmak için */tap* yazman yeterli."
    )

def tap(update, context):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"points": 0}

    data[user_id]["points"] += 1
    save_data(data)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🔥 *+1 TAP!*  
Toplam puanın: *{data[user_id]['points']}*",
        parse_mode=ParseMode.MARKDOWN
    )

def stats(update, context):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Hiç puanın yok. Başlamak için */tap* kullan."
        )
        return

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"📊 Toplam puanın: *{data[user_id]['points']}*",
        parse_mode=ParseMode.MARKDOWN
    )

# ----------------------------
# Botu başlat
# ----------------------------
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise Exception("BOT_TOKEN ortam değişkeni ayarlı değil!")

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("tap", tap))
    dp.add_handler(CommandHandler("stats", stats))

    updater.start_polling()
    print("Bot çalışıyor...")
    updater.idle()

if __name__ == "__main__":
    main()
