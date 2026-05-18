"""
Логирование и хранение заявок
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from config import DATABASE_FILE, LOG_FILE


class ApplicationLogger:
    """Класс для логирования заявок в файл и БД"""
    
    def __init__(self):
        self.db_file = DATABASE_FILE
        self.log_file = LOG_FILE
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                name TEXT,
                phone TEXT,
                service TEXT,
                timestamp TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_application(self, user_id, username, name, phone, service):
        """Сохранение заявки в БД и логирование"""
        timestamp = datetime.now().isoformat()
        
        # Сохранение в БД
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO applications 
            (user_id, username, name, phone, service, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, name, phone, service, timestamp))
        
        conn.commit()
        app_id = cursor.lastrowid
        conn.close()
        
        # Логирование в файл
        log_entry = {
            'id': app_id,
            'user_id': user_id,
            'username': username,
            'name': name,
            'phone': phone,
            'service': service,
            'timestamp': timestamp
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        return app_id
    
    def get_all_applications(self):
        """Получить все заявки"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM applications ORDER BY created_at DESC')
        applications = cursor.fetchall()
        
        conn.close()
        return applications
    
    def get_application_count(self):
        """Получить количество заявок"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM applications')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def export_csv(self, filename='applications_export.csv'):
        """Экспорт заявок в CSV"""
        import csv
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM applications ORDER BY created_at DESC')
        applications = cursor.fetchall()
        
        conn.close()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'User ID', 'Username', 'Имя', 'Телефон', 'Услуга', 'Время', 'Дата создания'])
            writer.writerows(applications)


# Глобальный экземпляр логгера
logger = ApplicationLogger()
