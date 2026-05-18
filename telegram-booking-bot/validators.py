"""
Проверка корректности данных
"""
import re
from config import PHONE_PATTERN


def validate_name(name):
    """
    Проверка имени:
    - Минимум 2 символа
    - Только буквы, пробелы и дефисы
    """
    if not name or len(name.strip()) < 2:
        return False, "Имя должно содержать минимум 2 символа"
    
    if len(name.strip()) > 50:
        return False, "Имя не должно превышать 50 символов"
    
    # Разрешаем буквы, пробелы, дефисы и апостроф
    if not re.match(r"^[а-яА-ЯёЁa-zA-Z\s\-']+$", name):
        return False, "Имя может содержать только буквы, пробелы и дефисы"
    
    return True, "OK"


def validate_phone(phone):
    """
    Проверка номера телефона:
    - Формат: +7XXXXXXXXXX или 8XXXXXXXXXX или 79XXXXXXXXX
    """
    # Удаляем пробелы и спецсимволы
    clean_phone = re.sub(r'[\s\-\(\)]+', '', phone)
    
    # Проверяем формат
    if not re.match(PHONE_PATTERN, clean_phone):
        return False, "Введите корректный номер телефона (+7 или 8)"
    
    return True, "OK"


def validate_service(service, available_services):
    """
    Проверка выбранной услуги
    """
    if service not in available_services:
        return False, "Выберите услугу из предложенных"
    
    return True, "OK"


def sanitize_phone(phone):
    """Преобразование номера в стандартный формат +7XXXXXXXXXX"""
    clean_phone = re.sub(r'[\s\-\(\)]+', '', phone)
    
    if clean_phone.startswith('8'):
        clean_phone = '7' + clean_phone[1:]
    elif clean_phone.startswith('+7'):
        clean_phone = clean_phone[1:]
    elif not clean_phone.startswith('7'):
        clean_phone = '7' + clean_phone
    
    return '+' + clean_phone
