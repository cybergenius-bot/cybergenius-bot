# main.py
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Логи
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

# Берём токен из переменной окружения Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN or not TOKEN.strip():
    log.error("TELEGRAM_TOKEN не задан в переменных окружения. Открой Render → Environment и проверь.")
    raise SystemExit(1)

# --- Временные простые хэндлеры для проверки ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот запущен и слышит вас!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

def main():
    app = Application.builder().token(TOKEN).build()

    # Временные хэндлеры (заменишь на свои после проверки)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    log.info("Starting polling…")
    # Сбрасываем старые накопившиеся апдейты, чтобы не было конфликтов
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
