"""
Telegram-бот для записи клиентов (мини-CRM)
"""
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN, ADMIN_CHAT_ID, SERVICES
from database import logger
from validators import validate_name, validate_phone, validate_service, sanitize_phone

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger_log = logging.getLogger(__name__)

# Состояния для ConversationHandler
NAME, PHONE, SERVICE = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога с пользователем"""
    user = update.effective_user
    
    welcome_message = (
        f"👋 Привет, {user.first_name}!\n\n"
        "📋 Я помогу вам записаться на услугу.\n\n"
        "Давайте начнём. Как вас зовут?"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=ReplyKeyboardRemove())
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение имени пользователя"""
    name = update.message.text
    
    is_valid, message = validate_name(name)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {message}\n\nПожалуйста, введите корректное имя:"
        )
        return NAME
    
    context.user_data['name'] = name
    
    await update.message.reply_text(
        f"✅ Спасибо, {name}!\n\n"
        "Теперь введите ваш номер телефона (формат: +7 или 8):",
        reply_markup=ReplyKeyboardRemove()
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение номера телефона"""
    phone = update.message.text
    
    is_valid, message = validate_phone(phone)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {message}\n\n"
            "Пожалуйста, введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX:"
        )
        return PHONE
    
    context.user_data['phone'] = sanitize_phone(phone)
    
    # Создание клавиатуры с услугами
    keyboard = []
    for key, service_name in SERVICES.items():
        keyboard.append([service_name])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "✅ Спасибо! Какую услугу вас интересует?",
        reply_markup=reply_markup
    )
    return SERVICE


async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение выбранной услуги"""
    service_name = update.message.text
    
    # Найти ключ услуги по имени
    service_key = None
    for key, name in SERVICES.items():
        if name == service_name:
            service_key = key
            break
    
    if not service_key:
        is_valid = False
    else:
        is_valid, _ = validate_service(service_key, SERVICES.keys())
    
    if not is_valid:
        keyboard = []
        for key, service_name in SERVICES.items():
            keyboard.append([service_name])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            "❌ Выберите услугу из предложенных:",
            reply_markup=reply_markup
        )
        return SERVICE
    
    context.user_data['service'] = service_key
    
    # Сохранение заявки
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    name = context.user_data['name']
    phone = context.user_data['phone']
    service = context.user_data['service']
    
    # Логирование в БД и файл
    application_id = logger.save_application(user_id, username, name, phone, service)
    
    # Отправка заявки администратору
    admin_message = (
        "📝 <b>НОВАЯ ЗАЯВКА</b>\n\n"
        f"<b>ID:</b> {application_id}\n"
        f"<b>От:</b> @{username} (ID: {user_id})\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Телефон:</b> {phone}\n"
        f"<b>Услуга:</b> {SERVICES[service]}\n"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode='HTML'
        )
        logger_log.info(f"Заявка отправлена администратору: ID={application_id}")
    except Exception as e:
        logger_log.error(f"Ошибка при отправке заявки администратору: {e}")
    
    # Подтверждение пользователю
    await update.message.reply_text(
        "✅ <b>Спасибо!</b>\n\n"
        "Ваша заявка успешно принята! 🎉\n\n"
        f"<b>Ваше ID заявки:</b> <code>{application_id}</code>\n\n"
        "Администратор свяжется с вами в ближайшее время.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='HTML'
    )
    
    logger_log.info(f"Заявка успешно обработана: ID={application_id}, пользователь={username}")
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена процесса заполнения"""
    await update.message.reply_text(
        "❌ Процесс отменён.\n\n"
        "Введите /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Справка по командам"""
    help_text = (
        "<b>📋 Доступные команды:</b>\n\n"
        "<b>/start</b> - Начать запись на услугу\n"
        "<b>/cancel</b> - Отменить запись\n"
        "<b>/help</b> - Показать эту справку\n\n"
        "<b>❓ Как это работает?</b>\n"
        "1️⃣ Нажмите /start\n"
        "2️⃣ Введите свои данные (имя, телефон)\n"
        "3️⃣ Выберите интересующую услугу\n"
        "4️⃣ Готово! Администратор свяжется с вами"
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')


def main() -> None:
    """Основная функция запуска бота"""
    # Проверка наличия TOKEN и ADMIN_CHAT_ID
    if BOT_TOKEN == 'ВАШ_ТОКЕН_ЗДЕСЬ':
        print("❌ ОШИБКА: Установите BOT_TOKEN в .env файле!")
        print("Инструкция:")
        print("1. Создайте файл .env в папке проекта")
        print("2. Добавьте строку: BOT_TOKEN=ваш_токен_от_BotFather")
        print("3. Добавьте строку: ADMIN_CHAT_ID=ваш_id_чата")
        return
    
    if ADMIN_CHAT_ID == 0:
        print("❌ ОШИБКА: Установите ADMIN_CHAT_ID в .env файле!")
        print("Инструкция:")
        print("1. Откройте .env файл")
        print("2. Добавьте строку: ADMIN_CHAT_ID=ваш_id_чата")
        return
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчик ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Добавление обработчиков
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    # Запуск бота
    print("🚀 Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
