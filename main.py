# main.py
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("bot")


# ----- handlers -----
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я живой. Напиши что‑нибудь – отвечу тем же.")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ Бот запущен и работает.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # отвечает тем же текстом
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)


def build_app():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN env var is not set")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    # ВАЖНО: правильно написано add_handler и используется ~ (тильда), а не минус
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    return app


if __name__ == "__main__":
    application = build_app()
    # для Render достаточно обычного polling
    application.run_polling(close_loop=False)
