"""
Скрипт для резервного копирования базы данных.
"""

import os
import sys
import shutil
from datetime import datetime
import sqlite3

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging import get_logger
from app.core.config import DATABASE_CONFIG

logger = get_logger().logger

def backup_database():
    """Создание резервной копии базы данных"""
    try:
        # Создаем директорию для бэкапов, если её нет
        backup_dir = os.path.join(os.path.dirname(DATABASE_CONFIG["path"]), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Формируем имя файла бэкапа
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
        
        # Создаем резервную копию
        shutil.copy2(DATABASE_CONFIG["path"], backup_file)
        
        # Проверяем целостность бэкапа
        conn = sqlite3.connect(backup_file)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == "ok":
            logger.info(f"Резервная копия успешно создана: {backup_file}")
            
            # Удаляем старые бэкапы (оставляем последние 5)
            backups = sorted([
                os.path.join(backup_dir, f) for f in os.listdir(backup_dir)
                if f.startswith("backup_") and f.endswith(".db")
            ])
            
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    os.remove(old_backup)
                    logger.info(f"Удален старый бэкап: {old_backup}")
        else:
            logger.error("Ошибка проверки целостности бэкапа")
            os.remove(backup_file)
            raise Exception("Ошибка проверки целостности бэкапа")
            
    except Exception as e:
        logger.error(f"Ошибка при создании резервной копии: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    backup_database() 