"""
КиберГений - Telegram Q&A Bot
Русскоязычный бот для ответов на вопросы с категориальной системой ценообразования
"""

import logging
import asyncio
import time
from aiohttp import web
from bot import start_bot, bot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Endpoint для проверки здоровья приложения"""
    return web.json_response({
        "status": "healthy",
        "service": "KyberGenius Telegram Bot",
        "timestamp": time.time()
    })

async def bot_info(request):
    """Endpoint для получения информации о боте"""
    try:
        bot_info = await bot.get_me()
        return web.json_response({
            "bot_username": bot_info.username,
            "bot_id": bot_info.id,
            "bot_name": bot_info.first_name,
            "status": "running"
        })
    except Exception as e:
        logger.error(f"Error getting bot info: {e}")
        return web.json_response({
            "error": "Unable to get bot info",
            "status": "error"
        }, status=500)

async def init_app():
    """Инициализация веб-приложения"""
    app = web.Application()
    
    # Добавляем роуты
    app.router.add_get('/health', health_check)
    app.router.add_get('/bot-info', bot_info)
    app.router.add_get('/', lambda request: web.json_response({
        "message": "KyberGenius Telegram Bot is running",
        "endpoints": {
            "/health": "Health check",
            "/bot-info": "Bot information"
        }
    }))
    
    return app

async def main():
    """Главная функция запуска приложения"""
    try:
        logger.info("="*50)
        logger.info("🤖 Starting KyberGenius Telegram Bot Server")
        logger.info("="*50)
        
        # Создаем веб-приложение
        app = await init_app()
        
        # Создаем задачи для бота и веб-сервера
        bot_task = asyncio.create_task(start_bot())
        
        # Запускаем веб-сервер
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)  # Changed to port 5000
        await site.start()
        
        logger.info("🌐 Web server started on 0.0.0.0:5000")
        logger.info("🤖 Bot is starting...")
        
        # Ждем завершения задач
        await bot_task
        
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        raise
    finally:
        logger.info("👋 KyberGenius Bot Server stopped")

if __name__ == '__main__':
    asyncio.run(main())
