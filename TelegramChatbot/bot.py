import logging
import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from config import API_TOKEN, CATEGORIES, FREE_QUESTIONS_COUNT, CATEGORY_RESPONSES

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище данных пользователей (в продакшене лучше использовать базу данных)
user_data = {}

# Создание главного меню
def create_main_menu():
    """Создает главное меню с категориями"""
    category_buttons = [[KeyboardButton(text=cat)] for cat in CATEGORIES.keys()]
    main_menu = ReplyKeyboardMarkup(keyboard=category_buttons, resize_keyboard=True)
    return main_menu

# Создание меню для возврата в главное меню
def create_back_menu():
    """Создает меню с кнопкой возврата"""
    back_menu = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Главное меню")]], 
        resize_keyboard=True
    )
    return back_menu

def get_user_data(user_id):
    """Получает данные пользователя или создает новые"""
    if user_id not in user_data:
        user_data[user_id] = {
            "free_questions": FREE_QUESTIONS_COUNT,
            "category": None,
            "total_questions": 0
        }
    return user_data[user_id]

def generate_smart_response(category, question):
    """Генерирует умный ответ на основе категории и вопроса"""
    try:
        # Получаем шаблоны ответов для категории
        responses = CATEGORY_RESPONSES.get(category, CATEGORY_RESPONSES["🧠 Другое"])
        
        # Выбираем случайный базовый ответ
        base_response = random.choice(responses)
        
        # Добавляем персонализацию на основе ключевых слов в вопросе
        question_lower = question.lower()
        
        additional_tips = []
        
        # Анализ ключевых слов для более точного ответа
        if any(word in question_lower for word in ["как", "что делать", "помогите", "совет"]):
            additional_tips.append("💡 Рекомендую пошагово разбить задачу на более мелкие части.")
        
        if any(word in question_lower for word in ["проблема", "сложно", "не получается"]):
            additional_tips.append("🔧 Иногда стоит сделать паузу и подойти к вопросу с другой стороны.")
        
        if any(word in question_lower for word in ["деньги", "бюджет", "стоимость", "цена"]):
            additional_tips.append("💰 При планировании бюджета всегда закладывайте резерв на непредвиденные расходы.")
        
        # Формируем финальный ответ
        response_parts = [f"📝 **Ваш вопрос по категории {category}:**", f'"{question}"', "", f"✅ **Мой ответ:**", base_response]
        
        if additional_tips:
            response_parts.extend(["", "🎯 **Дополнительные рекомендации:**"] + additional_tips)
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"✅ Спасибо за вопрос по категории {category}! Я обработал ваш запрос и дам развернутый ответ на основе лучших практик в данной области."

@dp.message(Command('start'))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        user = get_user_data(user_id)
        
        welcome_text = (
            "👋 Привет! Я КиберГений — бот, который поможет тебе разобраться в любой теме.\n\n"
            f"🎁 У тебя есть {user['free_questions']} бесплатных вопроса!\n\n"
            "Выбери интересующую категорию и задай вопрос:"
        )
        
        await message.answer(welcome_text, reply_markup=create_main_menu())
        logger.info(f"User {user_id} started the bot")
        
    except Exception as e:
        logger.error(f"Error in start_handler: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@dp.message(lambda message: message.text and message.text == "🏠 Главное меню")
async def main_menu_handler(message: types.Message):
    """Возврат в главное меню"""
    try:
        user_id = message.from_user.id
        user = get_user_data(user_id)
        user["category"] = None
        
        await message.answer(
            f"🏠 Главное меню\n\nОсталось бесплатных вопросов: {user['free_questions']}\nВсего задано вопросов: {user['total_questions']}\n\nВыбери категорию:",
            reply_markup=create_main_menu()
        )
        
    except Exception as e:
        logger.error(f"Error in main_menu_handler: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@dp.message(lambda message: message.text and message.text in CATEGORIES)
async def category_selected(message: types.Message):
    """Обработчик выбора категории"""
    try:
        user_id = message.from_user.id
        user = get_user_data(user_id)
        user["category"] = message.text
        
        price = CATEGORIES[message.text]
        
        if user["free_questions"] > 0:
            response_text = (
                f"✅ Отлично! Ты выбрал категорию: **{message.text}**\n\n"
                f"💝 Это будет бесплатный вопрос (осталось: {user['free_questions']})\n\n"
                "Напиши свой вопрос:"
            )
        else:
            response_text = (
                f"✅ Отлично! Ты выбрал категорию: **{message.text}**\n\n"
                f"💰 Стоимость ответа: {price} ₪\n\n"
                "Напиши свой вопрос:"
            )
        
        await message.answer(response_text, reply_markup=create_back_menu())
        logger.info(f"User {user_id} selected category: {message.text}")
        
    except Exception as e:
        logger.error(f"Error in category_selected: {e}")
        await message.answer("Произошла ошибка при выборе категории. Попробуйте снова.")

@dp.message(Command('help'))
async def help_handler(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "🤖 **КиберГений - Помощь**\n\n"
        "**Доступные команды:**\n"
        "/start - начать работу с ботом\n"
        "/help - показать эту справку\n"
        "/stats - показать статистику\n\n"
        "**Как пользоваться:**\n"
        "1. Выберите категорию из меню\n"
        "2. Задайте свой вопрос\n"
        "3. Получите умный ответ\n\n"
        "**Категории и цены:**\n"
    )
    
    for category, price in CATEGORIES.items():
        help_text += f"{category}: {price} ₪\n"
    
    await message.answer(help_text, reply_markup=create_main_menu())

@dp.message(Command('stats'))
async def stats_handler(message: types.Message):
    """Показать статистику пользователя"""
    try:
        user_id = message.from_user.id
        user = get_user_data(user_id)
        
        stats_text = (
            f"📊 **Твоя статистика:**\n\n"
            f"🎁 Бесплатных вопросов осталось: {user['free_questions']}\n"
            f"📝 Всего задано вопросов: {user['total_questions']}\n"
            f"📂 Текущая категория: {user.get('category', 'Не выбрана')}"
        )
        
        await message.answer(stats_text, reply_markup=create_main_menu())
        
    except Exception as e:
        logger.error(f"Error in stats_handler: {e}")
        await message.answer("Произошла ошибка при получении статистики.")

@dp.message()
async def handle_question(message: types.Message):
    """Обработчик вопросов пользователей"""
    try:
        user_id = message.from_user.id
        user = get_user_data(user_id)
        category = user.get("category")
        
        # Проверяем, выбрана ли категория
        if not category:
            await message.answer(
                "❗ Пожалуйста, сначала выбери категорию с помощью кнопок ниже.",
                reply_markup=create_main_menu()
            )
            return
        
        question_text = message.text
        if not question_text:
            await message.answer(
                "❗ Пожалуйста, отправьте текстовое сообщение с вашим вопросом.",
                reply_markup=create_back_menu()
            )
            return
            
        question = question_text.strip()
        
        # Проверяем длину вопроса
        if len(question) < 5:
            await message.answer(
                "❗ Пожалуйста, задайте более развернутый вопрос (минимум 5 символов).",
                reply_markup=create_back_menu()
            )
            return
        
        # Обрабатываем вопрос
        if user["free_questions"] > 0:
            # Бесплатный ответ
            user["free_questions"] -= 1
            user["total_questions"] += 1
            
            # Генерируем умный ответ
            smart_response = generate_smart_response(category, question)
            
            await message.answer("⏳ Обрабатываю ваш вопрос...")
            await message.answer(smart_response, reply_markup=create_back_menu())
            
            if user["free_questions"] > 0:
                await message.answer(
                    f"🎁 У вас осталось {user['free_questions']} бесплатных вопросов!",
                    reply_markup=create_back_menu()
                )
            else:
                await message.answer(
                    "🎯 Бесплатные вопросы закончились! Следующие ответы будут платными согласно тарифам категорий.",
                    reply_markup=create_back_menu()
                )
            
            logger.info(f"User {user_id} asked free question in {category}")
            
        else:
            # Платный ответ
            price = CATEGORIES[category]
            user["total_questions"] += 1
            
            await message.answer(
                f"💰 **Платный ответ**\n\n"
                f"Категория: {category}\n"
                f"Стоимость: {price} ₪\n\n"
                f"Для получения ответа необходимо произвести оплату.\n"
                f"После оплаты вы получите развернутый ответ от КиберГения.\n\n"
                f"📞 Для оплаты свяжитесь с администратором.",
                reply_markup=create_back_menu()
            )
            
            logger.info(f"User {user_id} asked paid question in {category} (price: {price})")
        
        # Сбрасываем категорию после ответа
        user["category"] = None
        
    except Exception as e:
        logger.error(f"Error in handle_question: {e}")
        await message.answer(
            "❗ Произошла ошибка при обработке вопроса. Попробуйте снова.",
            reply_markup=create_main_menu()
        )

async def on_startup():
    """Действия при запуске бота"""
    logger.info("Bot started successfully!")

async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Bot stopped!")

async def start_bot():
    """Запуск бота"""
    try:
        logger.info("Starting KyberGenius Telegram Bot...")
        await on_startup()
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await on_shutdown()
