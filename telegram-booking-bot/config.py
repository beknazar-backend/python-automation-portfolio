"""
Конфигурация Telegram-бота
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API токен
BOT_TOKEN = os.getenv('BOT_TOKEN', 'ВАШ_ТОКЕН_ЗДЕСЬ')

# ID администратора для отправки заявок
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '0'))

# Список доступных услуг
SERVICES = {
    'konsultaciya': '💬 Консультация',
    'obsluzh': '🛠️ Обслуживание',
    'remont': '🔧 Ремонт',
    'ustanovka': '📦 Установка',
    'test': '✅ Тестирование',
}

# Путь к логам
LOG_FILE = 'applications.log'
DATABASE_FILE = 'applications.db'

# Регулярное выражение для проверки номера телефона (Россия)
PHONE_PATTERN = r'^(\+7|8)(\d{10})$'
