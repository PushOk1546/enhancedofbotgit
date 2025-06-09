"""
Скрипт для инициализации базы данных.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging import get_logger
from app.core.config import DATABASE_CONFIG

logger = get_logger().logger

def init_database():
    """Инициализация базы данных"""
    try:
        # Создаем директорию для базы данных, если её нет
        os.makedirs(os.path.dirname(DATABASE_CONFIG["path"]), exist_ok=True)
        
        # Подключаемся к базе данных
        conn = sqlite3.connect(DATABASE_CONFIG["path"])
        cursor = conn.cursor()
        
        # Создаем таблицы
        cursor.executescript("""
            -- Таблица пользователей
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Таблица сообщений
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            
            -- Таблица платежей
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id INTEGER,
                amount REAL,
                currency TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            
            -- Таблица предпочтений
            CREATE TABLE IF NOT EXISTS preferences (
                user_id INTEGER PRIMARY KEY,
                model TEXT,
                style TEXT,
                temperature REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            
            -- Таблица PPV контента
            CREATE TABLE IF NOT EXISTS ppv_content (
                content_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                description TEXT,
                price REAL,
                type TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            
            -- Таблица напоминаний
            CREATE TABLE IF NOT EXISTS reminders (
                reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                frequency TEXT,
                last_sent TIMESTAMP,
                next_send TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            
            -- Таблица статистики
            CREATE TABLE IF NOT EXISTS statistics (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                metric_name TEXT,
                metric_value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
        """)
        
        # Создаем индексы для оптимизации запросов
        cursor.executescript("""
            CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
            CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
            CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
            CREATE INDEX IF NOT EXISTS idx_ppv_content_user_id ON ppv_content(user_id);
            CREATE INDEX IF NOT EXISTS idx_reminders_next_send ON reminders(next_send);
            CREATE INDEX IF NOT EXISTS idx_statistics_user_id ON statistics(user_id);
            CREATE INDEX IF NOT EXISTS idx_statistics_metric ON statistics(metric_name);
        """)
        
        # Сохраняем изменения
        conn.commit()
        
        logger.info("База данных успешно инициализирована")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_database() 