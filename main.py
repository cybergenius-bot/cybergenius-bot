import logging, asyncio, aiosqlite, datetime as dt
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ContextTypes, filters
from config import API_TOKEN, FREE_QUESTIONS, UNLIM_PRICE, DB_PATH, CATEGORIES

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("bot")

PAY_LINK = "https://www.paypal.me/ВАШ_ПСЕВДОНИМ/99ILS"  # временно. Позже сделаем автопроверку оплаты

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  free_left INTEGER DEFAULT 10,
  unlim_until TEXT
);
"""


async def db_init():
  async with aiosqlite.connect(DB_PATH) as db:
    await db.execute(CREATE_SQL)
    await db.commit()


async def get_user(user_id: int):
  async with aiosqlite.connect(DB_PATH) as db:
    cur = await db.execute(
        "SELECT free_left, unlim_until FROM users WHERE user_id=?",
        (user_id, ))
    row = await cur.fetchone()
    if not row:
      await db.execute(
          "INSERT INTO users(user_id, free_left, unlim_until) VALUES(?, ?, ?)",
          (user_id, FREE_QUESTIONS, None))
      await db.commit()
      return FREE_QUESTIONS, None
    return row[0], row[1]


async def set_user(user_id: int,
                   free_left: int = None,
                   unlim_until: str = None):
  async with aiosqlite.connect(DB_PATH) as db:
    if free_left is not None and unlim_until is not None:
      await db.execute(
          "UPDATE users SET free_left=?, unlim_until=? WHERE user_id=?",
          (free_left, unlim_until, user_id))
    elif free_left is not None:
      await db.execute("UPDATE users SET free_left=? WHERE user_id=?",
                       (free_left, user_id))
    elif unlim_until is not None:
      await db.execute("UPDATE users SET unlim_until=? WHERE user_id=?",
                       (unlim_until, user_id))
    await db.commit()


def main_menu():
  rows = [
      [KeyboardButton(c) for c in CATEGORIES[:3]],
      [KeyboardButton(c) for c in CATEGORIES[3:6]],
  ]
  rows.append([KeyboardButton("Тарифы"), KeyboardButton("Мой статус")])
  return ReplyKeyboardMarkup(rows, resize_keyboard=True)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await db_init()
  free_left, unlim_until = await get_user(update.effective_user.id)
  text = "Привет! Я универсальный помощник. Выбери категорию и задай вопрос."
  await update.message.reply_text(text, reply_markup=main_menu())


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
  uid = update.effective_user.id
  free_left, unlim_until = await get_user(uid)
  if unlim_until:
    until = dt.datetime.fromisoformat(unlim_until).strftime("%d.%m.%Y")
    msg = f"Безлимит активен до {until}."
  else:
    msg = f"Бесплатных вопросов осталось: {free_left}."
  await update.message.reply_text(msg)


async def cmd_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
  msg = (
      f"Тарифы:\n"
      f"• {FREE_QUESTIONS} вопросов — бесплатно\n"
      f"• После — {3} ₪/вопрос (опция)\n"
      f"• Безлимит на 30 дней — {UNLIM_PRICE} ₪\n\n"
      f"Оформить безлимит: {PAY_LINK}\n"
      f"После оплаты пришли сюда команду /activate <последние4цифры_транзакции> (временно).\n"
  )
  await update.message.reply_text(msg)


async def cmd_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # Временная активация (ручная). Позже подключим PayPal IPN/вебхук.
  uid = update.effective_user.id
  # 30 дней безлимита:
  until = (dt.datetime.utcnow() + dt.timedelta(days=30)).isoformat()
  await set_user(uid, unlim_until=until)
  await update.message.reply_text(
      "Готово! Безлимит включён на 30 дней. /status")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  uid = update.effective_user.id
  text = (update.message.text or "").strip()

  if text.lower() in {"тарифы", "тариф", "подписка"}:
    return await cmd_tariffs(update, context)
  if text.lower() in {"мой статус", "статус"}:
    return await cmd_status(update, context)

  # выбор категории
  if text in CATEGORIES:
    context.user_data["category"] = text
    return await update.message.reply_text(
        f"Категория выбрана: {text}. Напиши свой вопрос.")

  # вопрос пользователя
  free_left, unlim_until = await get_user(uid)
  has_unlim = False
  if unlim_until:
    try:
      has_unlim = dt.datetime.fromisoformat(unlim_until) > dt.datetime.utcnow()
    except Exception:
      has_unlim = False

  if not has_unlim:
    if free_left <= 0:
      return await update.message.reply_text(
          f"Лимит бесплатных вопросов исчерпан.\nОформи безлимит {UNLIM_PRICE} ₪: {PAY_LINK}\n"
          f"или жми «Тарифы».")
    else:
      await set_user(uid, free_left=free_left - 1)

  # ⚙️ ТУТ ОТВЕТ МОДЕЛИ/ЛОГИКИ
  cat = context.user_data.get("category", "Другое")
  answer = f"[{cat}] Я принял вопрос: «{text}». (Пока демо‑ответ. Добавим ИИ на следующем шаге.)"
  await update.message.reply_text(answer)


def build_app() -> Application:
  return Application.builder().token(API_TOKEN).build()


async def run():
  await db_init()
  app = build_app()
  app.add_handler(CommandHandler("start", cmd_start))
  app.add_handler(CommandHandler("status", cmd_status))
  app.add_handler(CommandHandler("tariffs", cmd_tariffs))
  app.add_handler(CommandHandler("activate", cmd_activate))
  app.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
  log.info("Bot is running (polling)…")
  await app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
  asyncio.run(run())
