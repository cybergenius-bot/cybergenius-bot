import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- БАЗА ДАННЫХ ---
DB_PATH = os.getenv("DB_PATH", "bot/db/users.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn

# --- ХЕНДЛЕРЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот на Render запущен ✅")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# снимаем вебхук перед polling, чтобы не было конфликта
async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

def build_app():
    token = os.environ["TELEGRAM_TOKEN"]
    app = ApplicationBuilder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return app

if __name__ == "__main__":
    app = build_app()
    app.run_polling()
