import os
import sqlite3
import requests
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

# МЕНЮЛАР
menu_kg = [["🏛 Мэрия жөнүндө", "📰 Жаңылыктар"], ["📄 Документтер", "📝 Арыз берүү"], ["📍 Дарек", "📸 Фото"], ["📞 Байланыш", "🌐 Сайт"]]
menu_ru = [["🏛 О мэрии", "📰 Новости"], ["📄 Документы", "📝 Подать заявку"], ["📍 Адрес", "📸 Фото"], ["📞 Контакты", "🌐 Сайт"]]

# --- 3. ФУНКЦИЯЛАР ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇰🇬 Кыргызча", "🇷🇺 Русский"]]
    await update.message.reply_text(
        "Кош келиңиз! / Добро пожаловать!\n\nТилди тандаңыз / Выберите язык:", 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    
    # ТИЛ ТАНДОО (Кыргызча же Орусча экенин аныктоо)
    if "Кыргызча" in text:
        user_lang[user_id] = "kg"
        await update.message.reply_text("Кыргызча тандалды 🇰🇬", reply_markup=ReplyKeyboardMarkup(menu_kg, resize_keyboard=True))
        return
    elif "Русский" in text:
        user_lang[user_id] = "ru"
        await update.message.reply_text("Русский язык выбран 🇷🇺", reply_markup=ReplyKeyboardMarkup(menu_ru, resize_keyboard=True))
        return

    # Тилди текшерүү (Эгер тил тандала элек болсо, автоматтык түрдө кыргызча кылат)
    lang = user_lang.get(user_id, "kg")

    # --- АРЫЗДЫ КАБЫЛ АЛУУ (Сен сураган сылык жооп ушул жерде) ---
    if user_state.get(user_id) == "waiting_text":
        cursor.execute("INSERT INTO appeals (user, text) VALUES (?, ?)", (str(user_id), text))
        conn.commit()
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 Жаңы арыз:\n{text}")
        
        thanks_msg = (
            "✅ Арызыңыз кабыл алынды. Биз аны мүмкүн болушунча тез арада карап чыгып, чечип бергенге аракет кылабыз. Кайрылганыңыз үчүн рахмат!" 
            if lang == "kg" else 
            "✅ Ваша заявка принята. Мы постараемся рассмотреть и решить её в кратчайшие сроки. Спасибо за обращение!"
        )
        await update.message.reply_text(thanks_msg)
        user_state[user_id] = None
        return

    lang = user_lang.get(user_id)
    if not lang: return

    # --- МЭРИЯ ЖӨНҮНДӨ (Сайттар кошулду) ---
    if text in ["🏛 Мэрия жөнүндө", "🏛 О мэрии"]:
        msg = (
            "🏛 **МЭРИЯ ГОРОДА ОШ**\n\n📍 723500, г. Ош, ул. Алымбек Датка, 221\n"
            "📞 0 3222 5-51-51, 0 3222 5-55-51\n"
            "⏰ Режим работы: 9:00 - 18:00\n\n"
            "🔗 Официальные ресурсы:"
        ) if lang == "ru" else (
            "🏛 **ОШ ШААРЫНЫН МЭРИЯСЫ**\n\n📍 723500, Ош ш., Алымбек Датка көчөсү, 221\n"
            "📞 0 3222 5-51-51, 0 3222 5-55-51\n"
            "⏰ Иштөө тартиби: 9:00 - 18:00\n\n"
            "🔗 Расмий булактар:"
        )
        kb = [
            [InlineKeyboardButton("🌐 Расмий сайт", url="https://oshcity.gov.kg/")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh_meriya/")],
            [InlineKeyboardButton("📘 Facebook", url="https://www.facebook.com/OshMeriya")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    # --- ЖАҢЫЛЫКТАР ---
    elif text in ["📰 Жаңылыктар", "📰 Новости"]:
        msg = "📰 Жаңылыктарды төмөнкү расмий булактардан окуй аласыздар:" if lang == "kg" else "📰 Вы можете прочитать новости в официальных источниках:"
        kb = [
            [InlineKeyboardButton("🌐 Расмий сайт", url="https://oshcity.gov.kg/kg/news")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh_meriya/")],
            [InlineKeyboardButton("📘 Facebook", url="https://www.facebook.com/OshMeriya")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    # --- САЙТ ---
    elif text in ["🌐 Сайт"]:
        kb = [
            [InlineKeyboardButton("🌐 Сайт", url="https://oshcity.gov.kg/")],
            [InlineKeyboardButton("📘 Facebook", url="https://www.facebook.com/OshMeriya")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh_meriya/")]
        ]
        await update.message.reply_text("🔗 Расмий булактар:", reply_markup=InlineKeyboardMarkup(kb))
        # ДАРЕК
    elif text in ["📍 Дарек", "📍 Адрес"]:
        keyboard = [[InlineKeyboardButton("🗺 2GIS", url="https://2gis.kg/bishkek/geo/70000001030888860")]]
        await update.message.reply_text("📍 Ленин көчөсү 221", reply_markup=InlineKeyboardMarkup(keyboard))
          # БАЙЛАНЫШ
    elif text in ["📞 Байланыш", "📞 Контакты"]:
        await update.message.reply_text("📞 03222 5-55-55\n📧 info@oshcity.kg")
            # ДОКУМЕНТ
    elif text in ["📄 Документтер", "📄 Документы"]:
        keyboard = [[InlineKeyboardButton("📂 Документтер", url="https://oshcity.gov.kg/ru/docs")]]
        await update.message.reply_text("📄 Документтер:", reply_markup=InlineKeyboardMarkup(keyboard))
 # ФОТО
    elif text in ["📸 Фото"]:
        user_state[user_id] = "photo"
        await update.message.reply_text("📸 Сүрөт жибериңиз")

    elif user_state.get(user_id) == "photo" and update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id)
        await update.message.reply_text("✅ Фото кабыл алынды")
        user_state[user_id] = None

    # --- АРЫЗ БЕРҮҮ ---
    elif text in ["📝 Арыз берүү", "📝 Подать заявку"]:
        user_state[user_id] = "waiting_text"
        msg = "Сураныч, арызыңызды же кайрылууңузду кенен жазыңыз:" if lang == "kg" else "Пожалуйста, напишите вашу заявку или обращение подробно:"
        await update.message.reply_text(msg)

    # --- АРЫЗДЫ КАБЫЛ АЛУУ (Сылык жооп) ---
    elif user_state.get(user_id) == "waiting_text":
        cursor.execute("INSERT INTO appeals (user, text) VALUES (?, ?)", (str(user_id), text))
        conn.commit()
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 Жаңы арыз:\n{text}")
        
        thanks_msg = (
            "✅ Арызыңыз ийгиликтүү кабыл алынды. Биз аны мүмкүн болушунча тез арада карап чыгып, чечип бергенге аракет кылабыз. Кайрылганыңыз үчүн рахмат!" 
            if lang == "kg" else 
            "✅ Ваша заявка успешно принята. Мы постараемся рассмотреть и решить её в кратчайшие сроки. Спасибо за обращение!"
        )
        await update.message.reply_text(thanks_msg)
        user_state[user_id] = None

# --- 4. ИШКЕ КИРГИЗҮҮ ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    if TOKEN:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
        app.run_polling()
