import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import asyncio

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

async def cmd_start(update, context):
    await update.message.reply_text("Привет! Бот онлайн.")

def build_app():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: None))
    return app

async def main():
    app = build_app()
    # ключ: чистим вебхук и сбрасываем накопившиеся апдейты
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.wait()

if __name__ == "__main__":
    asyncio.run(main())
