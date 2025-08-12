import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# читаем токен из переменной окружения
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Бот запущен ✅")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # простая эхо‑ответка
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)

def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    # ВАЖНО: правильные скобки вокруг отрицания команды
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
