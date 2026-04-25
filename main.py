import sqlite3
import requests
from bs4 import BeautifulSoup

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8791805795:AAH41B49LpEyIC9SLDray7Q5pcLHPjg4tx4"
ADMIN_ID = 1652310358

# DATABASE
conn = sqlite3.connect("osh_bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS appeals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    text TEXT
)
""")

user_state = {}
user_lang = {}

# MENU
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

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇰🇬 Кыргызча", "🇷🇺 Русский"]]
    await update.message.reply_text(
        "Кош келиңиз!\nДобро пожаловать!\n\nТилди тандаңыз / Выберите язык:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# NEWS (scraping)
def get_news(lang):
    try:
        if lang == "ru":
            url = "https://oshcity.gov.kg/ru/news"
        else:
            url = "https://oshcity.gov.kg/kg/news"

        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        news = soup.find_all("h2")[:5]

        result = ""
        for n in news:
            result += "📰 " + n.text.strip() + "\n\n"

        return result if result else "Жаңылык табылган жок"
    except:
        return "Жаңылыктар жеткиликтүү эмес"

# HANDLE
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # LANGUAGE
    if text == "🇰🇬 Кыргызча":
        user_lang[user_id] = "kg"
        await update.message.reply_text("Кыргызча тандалды 🇰🇬", reply_markup=ReplyKeyboardMarkup(menu_kg, resize_keyboard=True))
        return

    if text == "🇷🇺 Русский":
        user_lang[user_id] = "ru"
        await update.message.reply_text("Русский выбран 🇷🇺", reply_markup=ReplyKeyboardMarkup(menu_ru, resize_keyboard=True))
        return

    lang = user_lang.get(user_id, "kg")

    # МЭРИЯ
    if text in ["🏛 Мэрия жөнүндө", "🏛 О мэрии"]:
        if lang == "ru":
            msg = (
                "🏛 Мэрия города Ош\n\n"
                "Высший исполнительный орган города.\n"
                "👤 Мэр: Акаев Жанарбек Кубанычович\n\n"
                "ℹ️ Подробнее:"
            )
        else:
            msg = (
                "🏛 Ош шаарынын мэриясы\n\n"
                "Шаардын аткаруу бийлигинин жогорку органы.\n"
                "👤 Мэр: Акаев Жанарбек Кубанычович\n\n"
                "ℹ️ Толук маалымат:"
            )

        keyboard = [
            [InlineKeyboardButton("🌐 Сайт", url="https://oshcity.gov.kg/ru/")],
            [InlineKeyboardButton("📘 Facebook", url="https://www.facebook.com/OshMeriya")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh.meriya")]
        ]

        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    # ЖАҢЫЛЫК
    elif text in ["📰 Жаңылыктар", "📰 Новости"]:
        news_text = get_news(lang)

        keyboard = [
            [InlineKeyboardButton("🌐 Сайт", url="https://oshcity.gov.kg/ru/")],
            [InlineKeyboardButton("📘 Facebook", url="https://www.facebook.com/OshMeriya")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh.meriya")]
        ]

        await update.message.reply_text(news_text, reply_markup=InlineKeyboardMarkup(keyboard))

    # ДОКУМЕНТ
    elif text in ["📄 Документтер", "📄 Документы"]:
        keyboard = [
            [InlineKeyboardButton("📂 Документтер", url="https://oshcity.gov.kg/ru/docs")],
            [InlineKeyboardButton("🌐 Сайт", url="https://oshcity.gov.kg/ru/")]
        ]
        await update.message.reply_text("📄 Документтер:", reply_markup=InlineKeyboardMarkup(keyboard))

    # АРЫЗ
    elif text in ["📝 Арыз берүү", "📝 Подать заявку"]:
        user_state[user_id] = "text"
        await update.message.reply_text("Сураныч, арызыңызды жазыңыз / Напишите заявку:")

    elif user_state.get(user_id) == "text":
        cursor.execute("INSERT INTO appeals (user, text) VALUES (?, ?)", (str(user_id), text))
        conn.commit()

        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 Жаңы арыз:\n{text}")

        if lang == "ru":
            msg = "✅ Ваша заявка принята. Мы постараемся рассмотреть её в кратчайшие сроки."
        else:
            msg = "✅ Арызыңыз кабыл алынды. Биз аны мүмкүн болушунча тез арада карап чыгабыз."

        await update.message.reply_text(msg)
        user_state[user_id] = None

    # ДАРЕК
    elif text in ["📍 Дарек", "📍 Адрес"]:
        if lang == "ru":
            msg = "📍 Мэрия г. Ош\nЛенин көчөсү 221\n\n🗺 Открыть на карте:"
        else:
            msg = "📍 Ош шаарынын мэриясы\nЛенин көчөсү 221\n\n🗺 Картадан көрүү:"

        keyboard = [[InlineKeyboardButton("🗺 2GIS", url="https://2gis.kg/bishkek/geo/70000001030888860/72.804713,40.516801")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    # ФОТО
    elif text in ["📸 Фото"]:
        user_state[user_id] = "photo"
        await update.message.reply_text("📸 Сүрөт жибериңиз")

    elif user_state.get(user_id) == "photo" and update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id)
        await update.message.reply_text("✅ Фото кабыл алынды")
        user_state[user_id] = None

    # БАЙЛАНЫШ
    elif text in ["📞 Байланыш", "📞 Контакты"]:
        await update.message.reply_text("📞 03222 5-55-55\n📧 info@oshcity.kg")

    # САЙТ
    elif text in ["🌐 Сайт"]:
        keyboard = [
            [InlineKeyboardButton("🌐 Сайт", url="https://oshcity.gov.kg/ru/")],
            [InlineKeyboardButton("📘 Facebook", url="https://www.facebook.com/OshMeriya")],
            [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/osh.meriya")]
        ]
        await update.message.reply_text("🔗 Расмий булактар:", reply_markup=InlineKeyboardMarkup(keyboard))


# RUN
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, handle))

print("🔥 МЭРИЯ БОТ ИШТЕП ЖАТАТ")
app.run_polling()