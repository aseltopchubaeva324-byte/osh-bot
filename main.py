import os
import sqlite3
import requests
import logging
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. ВЕБ-СЕРВЕР (RENDER ӨЧҮРБӨШҮ ҮЧҮН) ---
app_server = Flask(__name__)

@app_server.route('/')
def index():
    return "Ош мэриясынын боту активдүү иштеп жатат!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app_server.run(host='0.0.0.0', port=port)

# --- 2. ПАРАМЕТРЛЕР ЖАНА МААЛЫМАТ БАЗАСЫ ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1652310358

# Маалымат базасын жөндөө
conn = sqlite3.connect("osh_bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS appeals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    text TEXT
)
""")
conn.commit()

user_state = {}
user_lang = {}

# МЕНЮЛАР (Сиз жөнөткөндөй)
menu_kg = [
    ["🏛 Мэрия жөнүндө", "📰 Жаңылыктар"],
    ["📄 Документтер", "📝 Арыз берүү"],
    ["📍 Дарек", "📸 Фото"],
    ["📞 Байланыш", "🌐 Сайт"]
]

menu_ru = [
    ["🏛 О мэрии", "📰 Новости"],
    ["📄 Документы", "📝 Подать заявку"],
    ["📍 Адрес", "📸 Фото"],
    ["📞 Контакты", "🌐 Сайт"]
]

# --- 3. БОТТУН ФУНКЦИЯЛАРЫ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇰🇬 Кыргызча", "🇷🇺 Русский"]]
    await update.message.reply_text(
        "Кош келиңиз!\nДобро пожаловать!\n\nТилди тандаңыз / Выберите язык:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

def get_news(lang):
    try:
        url = "https://oshcity.gov.kg/ru/news" if lang == "ru" else "https://oshcity.gov.kg/kg/news"
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        news = soup.find_all("h2")[:5]
        result = "".join([f"📰 {n.text.strip()}\n\n" for n in news])
        return result if result else "Жаңылык табылган жок"
    except:
        return "Жаңылыктар жеткиликтүү эмес"

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # Тил тандоо
    if text == "🇰🇬 Кыргызча":
        user_lang[user_id] = "kg"
        await update.message.reply_text("Кыргызча тандалды 🇰🇬", reply_markup=ReplyKeyboardMarkup(menu_kg, resize_keyboard=True))
        return
    if text == "🇷🇺 Русский":
        user_lang[user_id] = "ru"
        await update.message.reply_text("Русский выбран 🇷🇺", reply_markup=ReplyKeyboardMarkup(menu_ru, resize_keyboard=True))
        return

    lang = user_lang.get(user_id, "kg")

    # Мэрия жөнүндө
    if text in ["🏛 Мэрия жөнүндө", "🏛 О мэрии"]:
        msg = "🏛 Ош шаарынын мэриясы\n\nШаардын аткаруу бийлигинин жогорку органы." if lang == "kg" else "🏛 Мэрия города Ош\n\nВысший исполнительный орган города."
        keyboard = [[InlineKeyboardButton("🌐 Сайт", url="https://oshcity.gov.kg/")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    # Жаңылыктар
    elif text in ["📰 Жаңылыктар", "📰 Новости"]:
        await update.message.reply_text(get_news(lang))

    # Арыз берүү
    elif text in ["📝 Арыз берүү", "📝 Подать заявку"]:
        user_state[user_id] = "waiting_text"
        await update.message.reply_text("Сураныч, арызыңызды жазыңыз / Напишите заявку:")

    # Сүрөт жөнөтүү
    elif text in ["📸 Фото"]:
        user_state[user_id] = "waiting_photo"
        await update.message.reply_text("📸 Сүрөт жибериңиз / Отправьте фото:")

    # Тексттик билдирүүлөрдү жана арыздарды иштетүү
    elif user_id in user_state:
        state = user_state[user_id]
        
        if state == "waiting_text":
            cursor.execute("INSERT INTO appeals (user, text) VALUES (?, ?)", (str(user_id), text))
            conn.commit()
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 Жаңы арыз:\n{text}")
            msg = "✅ Арызыңыз кабыл алынды." if lang == "kg" else "✅ Ваша заявка принята."
            await update.message.reply_text(msg)
            user_state[user_id] = None
            
    # Байланыш, Сайт, Дарек ж.б. (Сиздин кодуңуздагы калган бөлүмдөр)
    elif text in ["📍 Дарек", "📍 Адрес"]:
        msg = "📍 Ленин көчөсү 221"
        await update.message.reply_text(msg)

# Сүрөттөрдү кабыл алуу
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_state.get(user_id) == "waiting_photo":
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id)
        await update.message.reply_text("✅ Фото кабыл алынды!")
        user_state[user_id] = None

# --- 4. ИШКЕ КИРГИЗҮҮ ---
if __name__ == "__main__":
    # Серверди Thread менен иштетүү
    Thread(target=run_web).start()
    
    if TOKEN:
        application = ApplicationBuilder().token(TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        print("🚀 БОТ ИШТЕП ЖАТАТ...")
        application.run_polling()
