import os
import sqlite3
import requests
import logging
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. ВЕБ-СЕРВЕР ---
app_server = Flask(__name__)
@app_server.route('/')
def index(): return "Мэрия боту активдүү!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app_server.run(host='0.0.0.0', port=port)

# --- 2. ПАРАМЕТРЛЕР ЖАНА БАЗА ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1652310358

conn = sqlite3.connect("osh_bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS appeals (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, text TEXT)")
conn.commit()

user_state = {}
user_lang = {}

# --- 3. МЕНЮЛАР ---
menu_kg = [["🏛 Мэрия жөнүндө", "📰 Жаңылыктар"], ["📄 Документтер", "📝 Арыз берүү"], ["📍 Дарек", "📸 Фото"], ["📞 Байланыш", "🌐 Сайт"]]
menu_ru = [["🏛 О мэрии", "📰 Новости"], ["📄 Документы", "📝 Подать заявку"], ["📍 Адрес", "📸 Фото"], ["📞 Контакты", "🌐 Сайт"]]

# --- 4. ФУНКЦИЯЛАР ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇰🇬 Кыргызча", "🇷🇺 Русский"]]
    await update.message.reply_text("Кош келиңиз! / Добро пожаловать!\n\nТилди тандаңыз / Выберите язык:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    
    if text == "🇰🇬 Кыргызча":
        user_lang[user_id] = "kg"
        await update.message.reply_text("Кыргызча тандалды 🇰🇬", reply_markup=ReplyKeyboardMarkup(menu_kg, resize_keyboard=True))
        return
    elif text == "🇷🇺 Русский":
        user_lang[user_id] = "ru"
        await update.message.reply_text("Русский язык выбран 🇷🇺", reply_markup=ReplyKeyboardMarkup(menu_ru, resize_keyboard=True))
        return

    lang = user_lang.get(user_id)
    if not lang: return

    # --- МЭРИЯ ЖӨНҮНДӨ (Сиз айткан маалыматтар ушул жерде) ---
    if text in ["🏛 Мэрия жөнүндө", "🏛 О мэрии"]:
        msg = (
            "🏛 **МЭРИЯ ГОРОДА ОШ**\n\n"
            "📍 723500, Кыргызская Республика, город Ош, ул. Алымбек Датка, 221\n"
            "📞 0 3222 5-51-51, 0 3222 5-55-51\n"
            "⏰ Режим работы: 9:00 - 18:00 (15-ноября - 31-марта)"
        ) if lang == "ru" else (
            "🏛 **ОШ ШААРЫНЫН МЭРИЯСЫ**\n\n"
            "📍 723500, Кыргыз Республикасы, Ош шаары, Алымбек Датка көчөсү, 221\n"
            "📞 0 3222 5-51-51, 0 3222 5-55-51\n"
            "⏰ Иштөө тартиби: 9:00 - 18:00 (15-ноябрь - 31-март)"
        )
          kb = [
            [InlineKeyboardButton("🌐 Расмий сайт", url="https://oshcity.gov.kg/kg/news")],
            [InlineKeyboardButton("📱 Facebook", url="https://www.facebook.com/OshMeriya")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh_meriya/")]
        await update.message.reply_text(msg, parse_mode="Markdown")

    # --- ЖАҢЫЛЫКТАР (Шилтемелер менен) ---
    elif text in ["📰 Жаңылыктар", "📰 Новости"]:
        msg = (
            "📰 Жаңылыктарды төмөнкү сайттардан окуй аласыздар:" if lang == "kg" 
            else "📰 Вы можете прочитать новости на следующих сайтах:"
        )
        kb = [
            [InlineKeyboardButton("🌐 Расмий сайт", url="https://oshcity.gov.kg/kg/news")],
            [InlineKeyboardButton("📱 Facebook", url="https://www.facebook.com/OshMeriya")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh_meriya/")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    # --- САЙТ (Инстаграм, Фейсбук кошулду) ---
    elif text in ["🌐 Сайт"]:
        msg = "🔗 Расмий булактар / Официальные ресурсы:"
        kb = [
            [InlineKeyboardButton("🌐 Официальный сайт", url="https://oshcity.gov.kg/")],
            [InlineKeyboardButton("📘 Facebook", url="https://www.facebook.com/OshMeriya")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh_meriya/")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    # --- АРЫЗ БЕРҮҮ ---
    elif text in ["📝 Арыз берүү", "📝 Подать заявку"]:
        user_state[user_id] = "waiting_text"
        await update.message.reply_text("Сураныч, арызыңызды жазыңыз / Напишите вашу заявку:")

    # --- АРЫЗДЫ КАБЫЛ АЛУУ ---
    elif user_state.get(user_id) == "waiting_text":
        cursor.execute("INSERT INTO appeals (user, text) VALUES (?, ?)", (str(user_id), text))
        conn.commit()
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 Жаңы арыз:\n{text}")
        await update.message.reply_text("✅ Кабыл алынды! / Принято!")
        user_state[user_id] = None

# --- 5. ИШКЕ КИРГИЗҮҮ ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    if TOKEN:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
        app.run_polling()
