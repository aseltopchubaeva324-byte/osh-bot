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

   
  # --- МЭРИЯ ЖӨНҮНДӨ БӨЛҮМҮ ---
    if text in ["🏛 Мэрия жөнүндө", "🏛 О мэрии"]:
        if lang == "ru":
            msg = (
                "🏛 **МЭРИЯ ГОРОДА ОШ**\n\n"
                "📍 723500, г. Ош, ул. Алымбек Датка, 221\n"
                "📞 0 3222 5-51-51, 0 3222 5-55-51\n"
                "⏰ Режим работы: 9:00 - 18:00\n\n"
                "🏛 **О городе Ош**\n\n"
                "📜 **История:**\n"
                "Ош – один из древнейших городов Центральной Азии.\n"
                "Был важным центром на Великом Шелковом пути.\n"
                "📅 История насчитывает более ~3000 лет.\n\n"
                "🌄 **Сулайман-Тоо:**\n"
                "Уникальная гора, расположенная прямо в центре города.\n"
                "Длина ~1140 м, ширина ~560 м.\n"
                "Имеет 5 вершин (самая высокая ~1175 м).\n\n"
                "🕌 **Особенности:**\n"
                "• Всемирное наследие ЮНЕСКО (2009)\n"
                "• Пещеры, петроглифы\n"
                "• Мечети, музеи\n"
                "• Древняя баня (XIV век)\n\n"
                "🏛 **Музейный комплекс:**\n"
                "Национальный музей Сулайман-Тоо — один из крупнейших в стране.\n"
                "Хранит более 33 000+ экспонатов.\n\n"
                "👥 **Население:** 366 000+ человек.\n\n"
                "🔗 **Официальные ресурсы:**"
            )
        else:
            msg = (
    "🏛 Ош шаары жөнүндө\n\n"
    
    "📜 Тарыхы:\n"
    "Ош – Борбордук Азиядагы эң байыркы шаарлардын бири.\n"
    "Улуу Жибек жолунун маанилүү борбору болгон.\n"
    "📅 ~3000 жылдык тарыхы бар.\n\n"
    
    "🌄 Сулайман-Тоо:\n"
    "Ош шаарынын так ортосунда жайгашкан уникалдуу тоо.\n"
    "Узундугу ~1140 м, туурасы ~560 м.\n"
    "5 чокусу бар (эң бийиги ~1175 м).\n\n"
    
    "🕌 Өзгөчөлүктөрү:\n"
    "• ЮНЕСКО дүйнөлүк мурасы (2009)\n"
    "• Үңкүрлөр, петроглифтер\n"
    "• Мечиттер, музейлер\n"
    "• Байыркы мончо (XIV кылым)\n\n"
    
    "🏛 Музей комплекси:\n"
    "Сулайман-Тоо улуттук музейи – өлкөдөгү эң ири музейлердин бири.\n"
    "33 000+ экспонат сакталат.\n\n"
    
    "📚 Экспозициялар:\n"
    "• Археология\n"
    "• Этнография\n"
    "• Кол өнөрчүлүк\n"
    "• Сүрөт жана скульптура\n\n"
    
    "📍 География:\n"
    "870–1110 м бийиктикте жайгашкан.\n\n"
    
    "👥 Калкы:\n"
    "366 000+ (500 000 чейин)\n\n"
    
    "🌐 Мааниси:\n"
    "Ош – тарыхый, маданий жана туристтик борбор.\n\n"
    
    "ℹ️ Толук маалымат төмөндө:"
            "📞 0 3222 5-51-51, 0 3222 5-55-51\n"
            "⏰ Режим работы: 9:00 - 18:00\n\n"
            "🔗 Официальные ресурсы:"
        ) if lang == "ru" else (
            "🏛 *ОШ ШААРЫНЫН МЭРИЯСЫ*\n\n📍 723500, Ош ш., Алымбек Датка көчөсү, 221\n"
            "📞 0 3222 5-51-51, 0 3222 5-55-51\n"
            "⏰ Иштөө тартиби: 9:00 - 18:00\n\n"
            "🔗 Расмий булактар:"
            )
        
        kb = [
            [InlineKeyboardButton("🌐 Сайт", url="https://oshcity.gov.kg/")],
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
      # БАЙЛАНЫШ (КОНТАКТЫ) БӨЛҮМҮ
    elif text in ["📞 Байланыш", "📞 Контакты"]:
        if lang == "ru":
            msg = (
                "📞 *Мэрия города Ош – контактные номера*\n\n"
                "🏛 **Общий отдел (Канцелярия):** 0 3222 5-51-51\n"
                "☎️ **Телефон доверия:** 0 3222 5-55-51\n\n"
                "📌 Организационно-инспекторский отдел: 0 3222 5-56-42\n"
                "📌 Экономика и финансы: 0 3222 7-07-01\n"
                "📌 Градостроительство и муниципальная собственность: 0 3222 5-53-79\n"
                "📌 Социальное развитие: 0 3222 5-53-06\n"
                "📌 Чрезвычайные ситуации и безопасность: 0 3222 5-58-29\n"
                "📌 Городское хозяйство и транспорт: 0 3222 5-53-34\n"
                "📌 Документационное обеспечение: 0 3222 5-52-62\n"
                "📌 Информационное обеспечение: 0 3222 5-50-19\n"
                "📌 Юридический сектор: 0 3222 5-50-65\n"
                "📌 Человеческие ресурсы: 0 3222 5-54-59\n"
                "📌 Техническое обслуживание: 0 3222 5-54-34\n\n"
                "📧 info@oshcity.kg"
            )
        else:
            msg = (
                "📞 *Ош шаарынын мэриясы – байланыш номерлери*\n\n"
                "🏛 **Жалпы бөлүм (Кеңсе):** 0 3222 5-51-51\n"
                "☎️ **Ишеним телефону:** 0 3222 5-55-51\n\n"
                "📌 Уюштуруу-инспектордук бөлүм: 0 3222 5-56-42\n"
                "📌 Экономика жана финансы: 0 3222 7-07-01\n"
                "📌 Шаар куруу жана муниципалдык менчик: 0 3222 5-53-79\n"
                "📌 Социалдык өнүгүү: 0 3222 5-53-06\n"
                "📌 Өзгөчө кырдаалдар жана коопсуздук: 0 3222 5-58-29\n"
                "📌 Шаардык чарба жана транспорт: 0 3222 5-53-34\n"
                "📌 Документтик камсыздоо: 0 3222 5-52-62\n"
                "📌 Маалыматтык камсыздоо: 0 3222 5-50-19\n"
                "📌 Юридикалык сектор: 0 3222 5-50-65\n"
                "📌 Адам ресурстары: 0 3222 5-54-59\n"
                "📌 Техникалык тейлөө: 0 3222 5-54-34\n\n"
                "📧 info@oshcity.kg"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")
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
        msg = "Сураныч, арызыңызды же кайрылууңузду кененирээк жазыңыз:" if lang == "kg" else "Пожалуйста, напишите вашу заявку или обращение подробно:"
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
