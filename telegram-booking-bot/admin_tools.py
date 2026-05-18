"""
Инструменты для администратора (просмотр и экспорт заявок)
"""
import sys
from database import logger
from config import SERVICES


def print_applications(limit=None):
    """Вывести все заявки"""
    applications = logger.get_all_applications()
    
    if not applications:
        print("❌ Нет заявок")
        return
    
    if limit:
        applications = applications[:limit]
    
    print("\n" + "="*100)
    print(f"📋 ЗАЯВКИ ({len(applications)} записей)")
    print("="*100)
    
    for app in applications:
        app_id, user_id, username, name, phone, service, timestamp, created_at = app
        service_name = SERVICES.get(service, service)
        
        print(f"\n🔹 ID заявки: {app_id}")
        print(f"   👤 Пользователь: @{username} (ID: {user_id})")
        print(f"   📝 Имя: {name}")
        print(f"   📞 Телефон: {phone}")
        print(f"   🎯 Услуга: {service_name}")
        print(f"   ⏰ Время: {timestamp}")
        print(f"   📅 Создано: {created_at}")
    
    print("\n" + "="*100 + "\n")


def print_stats():
    """Вывести статистику"""
    total = logger.get_application_count()
    
    print("\n" + "="*50)
    print("📊 СТАТИСТИКА")
    print("="*50)
    print(f"Всего заявок: {total}")
    print("="*50 + "\n")


def export_to_csv():
    """Экспорт в CSV"""
    filename = 'applications_export.csv'
    logger.export_csv(filename)
    print(f"✅ Заявки экспортированы в {filename}")


def show_help():
    """Показать справку"""
    print("""
    ✅ Доступные команды:
    
    python admin_tools.py list [N]      - Показать заявки (N последних)
    python admin_tools.py stats         - Показать статистику
    python admin_tools.py export        - Экспортировать в CSV
    python admin_tools.py help          - Показать эту справку
    """)


def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        print_applications(limit)
    
    elif command == 'stats':
        print_stats()
    
    elif command == 'export':
        export_to_csv()
    
    elif command == 'help':
        show_help()
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        show_help()


if __name__ == '__main__':
    main()
