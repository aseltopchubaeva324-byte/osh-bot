import os
import sqlite3
import requests
import logging
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. ВЕБ-СЕРВЕР (RENDER ҮЧҮН) ---
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

def get_news(lang):
    try:
        url = f"https://oshcity.gov.kg/{lang}/news"
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        news = soup.find_all("h2")[:5]
        return "".join([f"📰 {n.text.strip()}\n\n" for n in news]) if news else "Жаңылык жок."
    except: return "Жаңылыктар жеткиликтүү эмес."

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    
    # ТИЛ ТАНДОО (БУЛ ЖЕРДЕ КАТА ОҢДОЛДУ)
    if text == "🇰🇬 Кыргызча":
        user_lang[user_id] = "kg"
        await update.message.reply_text("Кыргызча тандалды 🇰🇬", reply_markup=ReplyKeyboardMarkup(menu_kg, resize_keyboard=True))
        return
    elif text == "🇷🇺 Русский":
        user_lang[user_id] = "ru"
        await update.message.reply_text("Русский язык выбран 🇷🇺", reply_markup=ReplyKeyboardMarkup(menu_ru, resize_keyboard=True))
        return

    # Тилди текшерүү
    lang = user_lang.get(user_id)
    if not lang:
        await start(update, context)
        return

    # МЭРИЯ ЖӨНҮНДӨ
    if text in ["🏛 Мэрия жөнүндө", "🏛 О мэрии"]:
        if lang == "kg":
            msg = "🏛 Ош шаарынын мэриясы\n\nШаардын аткаруу бийлигинин жогорку органы.\n👤 Мэр: Акаев Жанарбек Кубанычович"
        else:
            msg = "🏛 Мэрия города Ош\n\nВысший исполнительный орган города.\n👤 Мэр: Акаев Жанарбек Кубанычович"
        kb = [[InlineKeyboardButton("🌐 Сайт", url="https://oshcity.gov.kg/")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    # ЖАҢЫЛЫКТАР
    elif text in ["📰 Жаңылыктар", "📰 Новости"]:
        await update.message.reply_text(get_news(lang))

    # ДОКУМЕНТТЕР
    elif text in ["📄 Документтер", "📄 Документы"]:
        url = "https://oshcity.gov.kg/kg/docs" if lang == "kg" else "https://oshcity.gov.kg/ru/docs"
        kb = [[InlineKeyboardButton("📂 Документтер", url=url)]]
        await update.message.reply_text("📄 Документтер / Документы:", reply_markup=InlineKeyboardMarkup(kb))

    # АРЫЗ БЕРҮҮ
    elif text in ["📝 Арыз берүү", "📝 Подать заявку"]:
        user_state[user_id] = "waiting_text"
        msg = "Арызыңызды жазыңыз:" if lang == "kg" else "Напишите вашу заявку:"
        await update.message.reply_text(msg)

    # ДАРЕК
    elif text in ["📍 Дарек", "📍 Адрес"]:
        msg = "📍 Ош шаары, Ленин көчөсү 221" if lang == "kg" else "📍 г. Ош, ул. Ленина 221"
        kb = [[InlineKeyboardButton("🗺 2GIS", url="https://2gis.kg/osh/geo/70030076135111161")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    # ФОТО
    elif text in ["📸 Фото"]:
        user_state[user_id] = "waiting_photo"
        msg = "📸 Сүрөт жибериңиз:" if lang == "kg" else "📸 Отправьте фото:"
        await update.message.reply_text(msg)

    # БАЙЛАНЫШ / САЙТ
    elif text in ["📞 Байланыш", "📞 Контакты", "🌐 Сайт"]:
        await update.message.reply_text("📞 03222 5-55-55\n🌐 oshcity.gov.kg\n📧 info@oshcity.kg")

    # АРЫЗДЫ КАБЫЛ АЛУУ
    elif user_state.get(user_id) == "waiting_text":
        cursor.execute("INSERT INTO appeals (user, text) VALUES (?, ?)", (str(user_id), text))
        conn.commit()
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 Жаңы арыз (ID: {user_id}):\n{text}")
        msg = "✅ Кабыл алынды!" if lang == "kg" else "✅ Ваша заявка принята!"
        await update.message.reply_text(msg)
        user_state[user_id] = None

# ФОТО КАБЫЛ АЛУУ
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_state.get(user_id) == "waiting_photo":
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"📸 Фото кимден: {user_id}")
        msg = "✅ Фото кабыл алынды!" if user_lang.get(user_id) == "kg" else "✅ Фото принято!"
        await update.message.reply_text(msg)
        user_state[user_id] = None

# --- 5. ИШКЕ КИРГИЗҮҮ ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    if TOKEN:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.run_polling()
