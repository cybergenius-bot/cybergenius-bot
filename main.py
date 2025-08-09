import os
import aiosqlite
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# =========[ НАСТРОЙКИ ]=========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # ОБЯЗАТЕЛЬНО задать на Render -> Environment
if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN env var is not set")

DB_PATH = "bot.db"

# тарифы
FREE_QUESTIONS = 5         # бесплатно
PACK_QUESTIONS = 5         # платный пакет
PACK_PRICE_USD = 3         # $ за пакет 5
UNLIM_PRICE_USD = 27       # $/месяц

# твоя ссылка PayPal. Замени на свою!
# Временный вариант: кнопка ведет на оплату и пользователь присылает ID/скрин, ты подтверждаешь /confirm
PAYPAL_LINK_PACK   = "https://www.paypal.me/YOUR_NAME/3USD"
PAYPAL_LINK_UNLIM  = "https://www.paypal.me/YOUR_NAME/27USD"

# кто может подтверждать оплаты (ID админов телеграм)
ADMINS = set()  # {123456789}

# поддерживаемые языки
LANGS = ("ru", "he", "en")

# текстовые ресурсы (минимум для старта)
TEXT = {
    "ru": {
        "hello": "Привет! Я универсальный помощник. Выберите язык:",
        "picked_lang": "Язык установлен: Русский 🇷🇺",
        "menu_title": "Выберите категорию или задайте вопрос:",
        "cats": ["Стройка", "Отношения", "Секс", "Бизнес", "Жизнь", "Другое", "Тарифы", "Мой статус"],
        "status": "Осталось бесплатно: {free}\nПлатных в пакете: {paid}\nБезлимит до: {unlim}",
        "tariffs": f"Тарифы:\n• 5 вопросов бесплатно\n• Пакет {PACK_QUESTIONS} за ${PACK_PRICE_USD}\n• Безлимит 30 дней за ${UNLIM_PRICE_USD}",
        "buy_what": "Что хотите купить?",
        "pay_pack": "Купить пакет (5 за $3)",
        "pay_unlim": "Купить безлимит ($27/30д)",
        "send_receipt": "После оплаты пришлите номер транзакции PayPal или скрин. Мы быстро активируем.",
        "no_quota": "Лимит исчерпан. Выберите «Тарифы» → «Купить».",
        "confirmed": "Оплата подтверждена. Приятного использования!",
        "not_admin": "Только админ может подтверждать оплаты.",
        "ask_tx": "Отправьте: /confirm <user_id> <pack|unlim>",
        "start_lang": "Выберите язык:",
        "set_lang_btns": ["Русский 🇷🇺", "Иврит 🇮🇱", "English 🇬🇧"],
        "lang_saved": "Готово! Язык сохранен.",
        "unknown": "Не понял. Напишите вопрос или нажмите кнопку.",
    },
    "he": {
        "hello": "שלום! אני עוזר אוניברסלי. בחר שפה:",
        "picked_lang": "השפה נקבעה: עברית 🇮🇱",
        "menu_title": "בחר קטגוריה או שאל שאלה:",
        "cats": ["בנייה", "יחסים", "מין", "עסקים", "חיים", "אחר", "תעריפים", "הסטטוס שלי"],
        "status": "חינם נותרו: {free}\nבתשלום בחבילה: {paid}\nללא הגבלה עד: {unlim}",
        "tariffs": f"תעריפים:\n• 5 שאלות בחינם\n• חבילה {PACK_QUESTIONS} ב-${PACK_PRICE_USD}\n• ללא הגבלה 30 ימים ב-${UNLIM_PRICE_USD}",
        "buy_what": "מה תרצה לקנות?",
        "pay_pack": "קנה חבילה (5 ב-$3)",
        "pay_unlim": "קנה ללא הגבלה ($27/30 ימים)",
        "send_receipt": "אחרי התשלום שלח מספר עסקה או צילום מסך. נפעיל במהירות.",
        "no_quota": "הגעת למגבלה. בחר \"תעריפים\" → \"קנה\".",
        "confirmed": "התשלום אושר. שימוש נעים!",
        "not_admin": "רק אדמין יכול לאשר תשלום.",
        "ask_tx": "שלח: /confirm <user_id> <pack|unlim>",
        "start_lang": "בחר שפה:",
        "set_lang_btns": ["Русский 🇷🇺", "Иврит 🇮🇱", "English 🇬🇧"],
        "lang_saved": "בוצע! השפה נשמרה.",
        "unknown": "לא הבנתי. כתוב שאלה או לחץ על כפתור.",
    },
    "en": {
        "hello": "Hi! I’m a universal assistant. Choose your language:",
        "picked_lang": "Language set: English 🇬🇧",
        "menu_title": "Pick a category or ask a question:",
        "cats": ["Construction", "Relationships", "Sex", "Business", "Life", "Other", "Plans", "My status"],
        "status": "Free left: {free}\nPaid in pack: {paid}\nUnlimited until: {unlim}",
        "tariffs": f"Plans:\n• 5 questions free\n• Pack of {PACK_QUESTIONS} for ${PACK_PRICE_USD}\n• Unlimited 30 days for ${UNLIM_PRICE_USD}",
        "buy_what": "What would you like to buy?",
        "pay_pack": "Buy pack (5 for $3)",
        "pay_unlim": "Buy unlimited ($27/30d)",
        "send_receipt": "After payment, send PayPal transaction ID or a screenshot. We’ll activate quickly.",
        "no_quota": "You’ve hit your limit. Pick “Plans” → “Buy”.",
        "confirmed": "Payment confirmed. Enjoy!",
        "not_admin": "Only admin can confirm payments.",
        "ask_tx": "Send: /confirm <user_id> <pack|unlim>",
        "start_lang": "Choose language:",
        "set_lang_btns": ["Русский 🇷🇺", "Иврит 🇮🇱", "English 🇬🇧"],
        "lang_saved": "Done! Language saved.",
        "unknown": "Didn’t get that. Send a question or click a button.",
    }
}

CATEGORIES = {
    "ru": ["Стройка", "Отношения", "Секс", "Бизнес", "Жизнь", "Другое"],
    "he": ["בנייה", "יחסים", "מין", "עסקים", "חיים", "אחר"],
    "en": ["Construction", "Relationships", "Sex", "Business", "Life", "Other"],
}

# =========[ БАЗА ]=========
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS users (
  user_id     INTEGER PRIMARY KEY,
  lang        TEXT,
  free_left   INTEGER,
  paid_left   INTEGER,
  unlim_until TEXT
);
"""

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_SQL)
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT lang, free_left, paid_left, unlim_until FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO users (user_id, lang, free_left, paid_left, unlim_until) VALUES (?, ?, ?, ?, ?)",
                (user_id, "ru", FREE_QUESTIONS, 0, None)
            )
            await db.commit()
            return {"lang": "ru", "free_left": FREE_QUESTIONS, "paid_left": 0, "unlim_until": None}
        return {"lang": row[0], "free_left": row[1], "paid_left": row[2], "unlim_until": row[3]}

async def set_user(user_id: int, *, lang=None, free_left=None, paid_left=None, unlim_until=None):
    user = await get_user(user_id)
    lang = lang if lang is not None else user["lang"]
    free_left = free_left if free_left is not None else user["free_left"]
    paid_left = paid_left if paid_left is not None else user["paid_left"]
    unlim_until = unlim_until if unlim_until is not None else user["unlim_until"]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET lang = ?, free_left = ?, paid_left = ?, unlim_until = ? WHERE user_id = ?",
            (lang, free_left, paid_left, unlim_until, user_id)
        )
        await db.commit()

def is_unlimited(unlim_until: str | None) -> bool:
    if not unlim_until:
        return False
    try:
        return datetime.utcnow() < datetime.fromisoformat(unlim_until)
    except Exception:
        return False

# =========[ UI ]=========
def lang_keyboard():
    # общая одинаковая клавиатура языков
    buttons = [[KeyboardButton(t)] for t in TEXT["ru"]["set_lang_btns"]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def main_menu(lang: str):
    cats = TEXT[lang]["cats"]
    rows = [
        [KeyboardButton(c) for c in cats[:3]],
        [KeyboardButton(c) for c in cats[3:6]],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

# =========[ ЛОГИКА ]=========
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await db_init()
    uid = update.effective_user.id
    user = await get_user(uid)
    await update.message.reply_text(TEXT[user["lang"]]["start_lang"], reply_markup=lang_keyboard())

async def handle_set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").lower()

    mapping = {
        "русский": "ru", "иврит": "he", "english": "en"
    }
    chosen = None
    for k, v in mapping.items():
        if k in text:
            chosen = v
            break
    if not chosen:
        # просто проваливаемся в меню
        user = await get_user(uid)
        await update.message.reply_text(TEXT[user["lang"]]["unknown"])
        return

    await set_user(uid, lang=chosen)
    await update.message.reply_text(TEXT[chosen]["lang_saved"], reply_markup=main_menu(chosen))

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = await get_user(uid)
    lang = user["lang"]
    unlim_txt = user["unlim_until"] if user["unlim_until"] else "—"
    await update.message.reply_text(
        TEXT[lang]["status"].format(free=user["free_left"], paid=user["paid_left"], unlim=unlim_txt),
        reply_markup=main_menu(lang)
    )

async def cmd_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = await get_user(uid)
    lang = user["lang"]

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXT[lang]["pay_pack"], url=PAYPAL_LINK_PACK)],
        [InlineKeyboardButton(TEXT[lang]["pay_unlim"], url=PAYPAL_LINK_UNLIM)],
    ])
    await update.message.reply_text(TEXT[lang]["tariffs"], reply_markup=kb)
    await update.message.reply_text(TEXT[lang]["send_receipt"], reply_markup=main_menu(lang))

async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /confirm <user_id> <pack|unlim>
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text(TEXT["ru"]["not_admin"])
        return
    try:
        _, uid_str, what = update.message.text.strip().split(maxsplit=2)
        uid = int(uid_str)
        user = await get_user(uid)
        if what.lower().startswith("pack"):
            await set_user(uid, paid_left=user["paid_left"] + PACK_QUESTIONS)
        else:
            until = datetime.utcnow() + timedelta(days=30)
            await set_user(uid, unlim_until=until.isoformat())
        await update.message.reply_text(TEXT[user["lang"]]["confirmed"])
    except Exception:
        await update.message.reply_text(TEXT["ru"]["ask_tx"])

def pick_lang_by_button(txt: str) -> str | None:
    low = txt.lower()
    if "рус" in low:
        return "ru"
    if "ивр" in low:
        return "he"
    if "english" in low or "eng" in low:
        return "en"
    return None

def is_tariffs_button(txt: str, lang: str) -> bool:
    btn = TEXT[lang]["cats"][6]  # "Тарифы"/"Plans"/...
    return txt.strip().lower() in (btn.lower(), "тарифы", "plans")

def is_status_button(txt: str, lang: str) -> bool:
    btn = TEXT[lang]["cats"][7]
    return txt.strip().lower() in (btn.lower(), "мой статус", "הסטטוס שלי", "my status")

async def generate_answer(category: str, lang: str, user_text: str) -> str:
    """
    Простейший генератор ответа (без внешних API), чтобы бот уже работал.
    Потом сюда легко подключим LLM.
    """
    if lang == "ru":
        base = f"Категория: {category}\nВопрос: {user_text}\nОтвет (кратко и по делу): "
        tips = {
            "Стройка": "проверьте смету, сроки и гарантию подрядчика; фиксируйте всё в договоре.",
            "Отношения": "говорите «я-сообщениями», уточняйте ожидания и назначайте время на разговор без телефонов.",
            "Секс": "согласие, безопасность и открытое общение — база; обсуждайте границы и желания.",
            "Бизнес": "сформулируйте оффер в одном предложении, опишите ICP и цифрами проверьте гипотезу.",
            "Жизнь": "распишите цель→шаги на 2 недели; маленький ежедневный прогресс побеждает.",
            "Другое": "уточните контекст в 1-2 предложениях, и я дам конкретный план из 3 шагов.",
        }
        return base + tips.get(category, "дайте немного контекста — и я составлю пошаговый план.")
    if lang == "he":
        return "תן קצת הקשר (2 משפטים) ואחזיר תוכנית בת 3 צעדים שתוכל לבצע היום."
    return "Give me a bit of context (1–2 sentences) and I’ll return a 3‑step plan you can apply today."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = await get_user(uid)
    lang = user["lang"]
    text = update.message.text or ""

    # выбор языка через кнопку
    new_lang = pick_lang_by_button(text)
    if new_lang:
        await set_user(uid, lang=new_lang)
        await update.message.reply_text(TEXT[new_lang]["picked_lang"], reply_markup=main_menu(new_lang))
        return

    # кнопки меню
    if is_tariffs_button(text, lang):
        await cmd_tariffs(update, context)
        return
    if is_status_button(text, lang):
        await cmd_status(update, context)
        return

    # определяем категорию: если совпадает с одной из
    if text.strip() in CATEGORIES[lang]:
        # пользователь ткнул категорию — просто подсказка
        await update.message.reply_text(TEXT[lang]["menu_title"], reply_markup=main_menu(lang))
        return

    # реальный вопрос — проверяем лимиты
    if not is_unlimited(user["unlim_until"]):
        if user["free_left"] > 0:
            await set_user(uid, free_left=user["free_left"] - 1)
        elif user["paid_left"] > 0:
            await set_user(uid, paid_left=user["paid_left"] - 1)
        else:
            await update.message.reply_text(TEXT[lang]["no_quota"], reply_markup=main_menu(lang))
            return

    # определяем предполагаемую категорию (грубо — по последней нажатой в чате у нас нет,
    # поэтому просто ставим "Другое"/"Other")
    category = CATEGORIES[lang][-1]
    answer = await generate_answer(category, lang, text)
    await update.message.reply_text(answer, reply_markup=main_menu(lang))

# =========[ MAIN ]=========
def build_app() -> Application:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("tariffs", cmd_tariffs))
    app.add_handler(CommandHandler("confirm", cmd_confirm))  # админская
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app

def main():
    app = build_app()
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
