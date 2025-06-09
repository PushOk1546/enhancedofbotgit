#!/usr/bin/env python3
"""
🔥 UNIFIED CORE SYSTEM 🔥
Объединенная система мониторинга, backup'а и управления ботом
Лучшие функции из всех компонентов в одном файле
"""

import os
import sys
import json
import time
import psutil
import shutil
import sqlite3
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from pathlib import Path
import hashlib
import tempfile
import tarfile

@dataclass
class SystemMetrics:
    """Системные метрики"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    active_users: int
    messages_per_minute: int
    response_time_avg: float
    error_count: int
    uptime_seconds: int

@dataclass
class BackupInfo:
    """Информация о backup"""
    backup_id: str
    timestamp: str
    backup_type: str
    file_path: str
    size_bytes: int
    checksum: str
    description: str

class CoreSystem:
    """Единая система управления ботом"""
    
    def __init__(self):
        self.db_path = "core_system.db"
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Мониторинг
        self.metrics_history = deque(maxlen=1440)  # 24 часа
        self.user_sessions = {}
        self.error_log = deque(maxlen=1000)
        self.response_times = deque(maxlen=100)
        self.start_time = datetime.now()
        
        # Backup
        self.backup_targets = {
            'users': ['premium_users.json', 'users.json'],
            'cache': ['response_cache.json'],
            'config': ['config.py', 'monetization_config.py'],
            'logs': ['logs/*.log']
        }
        
        # Конфигурация
        self.config = {
            'auto_backup_enabled': True,
            'backup_interval_hours': 6,
            'retention_days': 30,
            'monitoring_enabled': True,
            'max_backups': 50
        }
        
        self.init_database()
        self.start_background_tasks()
        
        print("🔥 Core System: АКТИВИРОВАН")

    def init_database(self):
        """Инициализация единой базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица метрик
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_percent REAL,
                memory_percent REAL,
                memory_mb REAL,
                active_users INTEGER,
                messages_per_minute INTEGER,
                response_time_avg REAL,
                error_count INTEGER,
                uptime_seconds INTEGER
            )
        ''')
        
        # Таблица backup'ов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                backup_id TEXT PRIMARY KEY,
                timestamp TEXT,
                backup_type TEXT,
                file_path TEXT,
                size_bytes INTEGER,
                checksum TEXT,
                description TEXT
            )
        ''')
        
        # Таблица активности пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                user_id INTEGER,
                timestamp TEXT,
                action TEXT,
                response_time REAL,
                PRIMARY KEY (user_id, timestamp)
            )
        ''')
        
        conn.commit()
        conn.close()

    def start_background_tasks(self):
        """Запуск фоновых задач"""
        if self.config['monitoring_enabled']:
            monitor_thread = threading.Thread(target=self._monitoring_worker)
            monitor_thread.daemon = True
            monitor_thread.start()
        
        if self.config['auto_backup_enabled']:
            backup_thread = threading.Thread(target=self._backup_worker)
            backup_thread.daemon = True
            backup_thread.start()

    def _monitoring_worker(self):
        """Фоновый мониторинг"""
        while True:
            try:
                metrics = self.collect_metrics()
                self.save_metrics(metrics)
                self.metrics_history.append(metrics)
                time.sleep(60)  # Каждую минуту
            except Exception as e:
                self.log_error("monitoring_error", str(e))
                time.sleep(30)

    def _backup_worker(self):
        """Фоновые backup'ы"""
        while True:
            try:
                time.sleep(self.config['backup_interval_hours'] * 3600)
                self.create_backup("auto")
                self.cleanup_old_backups()
            except Exception as e:
                self.log_error("backup_error", str(e))
                time.sleep(3600)

    def collect_metrics(self) -> SystemMetrics:
        """Сбор метрик системы"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_mb = memory.used / 1024 / 1024
        
        current_time = datetime.now()
        active_users = len([s for s in self.user_sessions.values() 
                           if datetime.fromisoformat(s['last_activity']) > current_time - timedelta(minutes=5)])
        
        messages_per_minute = sum(1 for t in self.response_times if t > 0)
        response_time_avg = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        error_count = len([e for e in self.error_log 
                          if datetime.fromisoformat(e['timestamp']) > current_time - timedelta(minutes=1)])
        
        uptime_seconds = int((current_time - self.start_time).total_seconds())
        
        return SystemMetrics(
            timestamp=current_time.isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            active_users=active_users,
            messages_per_minute=messages_per_minute,
            response_time_avg=response_time_avg,
            error_count=error_count,
            uptime_seconds=uptime_seconds
        )

    def track_user_action(self, user_id: int, action: str, response_time: float = 0.0):
        """Отслеживание действий пользователя"""
        timestamp = datetime.now().isoformat()
        
        self.user_sessions[user_id] = {
            'last_activity': timestamp,
            'session_messages': self.user_sessions.get(user_id, {}).get('session_messages', 0) + 1
        }
        
        if response_time > 0:
            self.response_times.append(response_time)
        
        # Сохраняем в БД
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_activity 
            (user_id, timestamp, action, response_time)
            VALUES (?, ?, ?, ?)
        ''', (user_id, timestamp, action, response_time))
        conn.commit()
        conn.close()

    def log_error(self, error_type: str, error_message: str, user_id: Optional[int] = None):
        """Логирование ошибок"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'user_id': user_id
        }
        self.error_log.append(error_entry)

    def create_backup(self, backup_type: str = "manual", description: str = "") -> str:
        """Создание backup"""
        timestamp = datetime.now()
        backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                backup_temp_path = Path(temp_dir) / backup_id
                backup_temp_path.mkdir()
                
                # Собираем файлы
                for category, files in self.backup_targets.items():
                    category_dir = backup_temp_path / category
                    category_dir.mkdir()
                    
                    for file_pattern in files:
                        for file_path in Path('.').glob(file_pattern):
                            if file_path.exists() and file_path.is_file():
                                dest_path = category_dir / file_path.name
                                shutil.copy2(file_path, dest_path)
                
                # Создаем метаданные
                metadata = {
                    'backup_id': backup_id,
                    'timestamp': timestamp.isoformat(),
                    'backup_type': backup_type,
                    'description': description or f"Auto backup - {timestamp.strftime('%Y-%m-%d %H:%M')}",
                    'created_by': 'core_system'
                }
                
                with open(backup_temp_path / 'metadata.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Создаем архив
                archive_path = self.backup_dir / f"{backup_id}.tar.gz"
                with tarfile.open(archive_path, 'w:gz') as tar:
                    tar.add(backup_temp_path, arcname=backup_id)
                
                # Вычисляем checksum
                checksum = self._calculate_checksum(archive_path)
                
                # Сохраняем информацию о backup
                backup_info = BackupInfo(
                    backup_id=backup_id,
                    timestamp=timestamp.isoformat(),
                    backup_type=backup_type,
                    file_path=str(archive_path),
                    size_bytes=archive_path.stat().st_size,
                    checksum=checksum,
                    description=metadata['description']
                )
                
                self._save_backup_info(backup_info)
                
                print(f"✅ Backup создан: {backup_id}")
                return backup_id
                
        except Exception as e:
            self.log_error("backup_creation_failed", str(e))
            print(f"❌ Ошибка создания backup: {e}")
            return ""

    def restore_backup(self, backup_id: str, restore_path: str = ".") -> bool:
        """Восстановление из backup"""
        try:
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                print(f"❌ Backup {backup_id} не найден")
                return False
            
            archive_path = Path(backup_info.file_path)
            if not archive_path.exists():
                print(f"❌ Файл backup не существует: {archive_path}")
                return False
            
            # Проверяем checksum
            if self._calculate_checksum(archive_path) != backup_info.checksum:
                print(f"❌ Checksum не совпадает для backup {backup_id}")
                return False
            
            # Восстанавливаем
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(restore_path)
            
            print(f"✅ Backup {backup_id} восстановлен")
            return True
            
        except Exception as e:
            self.log_error("backup_restore_failed", str(e))
            print(f"❌ Ошибка восстановления: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        if not self.metrics_history:
            return {"status": "no_data", "message": "Нет данных мониторинга"}
        
        latest_metrics = self.metrics_history[-1]
        
        # Определяем статус
        status = "healthy"
        if latest_metrics.cpu_percent > 80 or latest_metrics.memory_percent > 80:
            status = "warning"
        if latest_metrics.cpu_percent > 95 or latest_metrics.memory_percent > 95:
            status = "critical"
        
        return {
            "status": status,
            "timestamp": latest_metrics.timestamp,
            "cpu_percent": latest_metrics.cpu_percent,
            "memory_percent": latest_metrics.memory_percent,
            "memory_mb": latest_metrics.memory_mb,
            "active_users": latest_metrics.active_users,
            "messages_per_minute": latest_metrics.messages_per_minute,
            "response_time_avg": latest_metrics.response_time_avg,
            "error_count": latest_metrics.error_count,
            "uptime": self._format_uptime(latest_metrics.uptime_seconds),
            "recent_errors": list(self.error_log)[-5:]  # Последние 5 ошибок
        }

    def list_backups(self) -> List[BackupInfo]:
        """Список всех backup'ов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT backup_id, timestamp, backup_type, file_path, 
                   size_bytes, checksum, description
            FROM backups 
            ORDER BY timestamp DESC
        ''')
        
        backups = []
        for row in cursor.fetchall():
            backups.append(BackupInfo(*row))
        
        conn.close()
        return backups

    def cleanup_old_backups(self):
        """Очистка старых backup'ов"""
        cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT backup_id, file_path FROM backups 
            WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))
        
        for backup_id, file_path in cursor.fetchall():
            try:
                Path(file_path).unlink(missing_ok=True)
                cursor.execute('DELETE FROM backups WHERE backup_id = ?', (backup_id,))
                print(f"🗑️ Удален старый backup: {backup_id}")
            except Exception as e:
                self.log_error("backup_cleanup_failed", str(e))
        
        conn.commit()
        conn.close()

    def emergency_backup(self) -> str:
        """Экстренный backup критически важных данных"""
        return self.create_backup("emergency", "Emergency backup of critical data")

    def save_metrics(self, metrics: SystemMetrics):
        """Сохранение метрик в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO metrics 
            (timestamp, cpu_percent, memory_percent, memory_mb,
             active_users, messages_per_minute, response_time_avg,
             error_count, uptime_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
            metrics.memory_mb, metrics.active_users, metrics.messages_per_minute,
            metrics.response_time_avg, metrics.error_count, metrics.uptime_seconds
        ))
        conn.commit()
        conn.close()

    def _save_backup_info(self, backup_info: BackupInfo):
        """Сохранение информации о backup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO backups 
            (backup_id, timestamp, backup_type, file_path, 
             size_bytes, checksum, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            backup_info.backup_id, backup_info.timestamp, backup_info.backup_type,
            backup_info.file_path, backup_info.size_bytes, backup_info.checksum,
            backup_info.description
        ))
        conn.commit()
        conn.close()

    def _get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Получение информации о backup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT backup_id, timestamp, backup_type, file_path,
                   size_bytes, checksum, description
            FROM backups WHERE backup_id = ?
        ''', (backup_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return BackupInfo(*row)
        return None

    def _calculate_checksum(self, file_path: Path) -> str:
        """Вычисление checksum файла"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _format_uptime(self, seconds: int) -> str:
        """Форматирование времени работы"""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        return f"{days}d {hours}h {minutes}m"

    def shutdown(self):
        """Корректное завершение работы"""
        print("🛑 Core System: ЗАВЕРШЕНИЕ РАБОТЫ")
        # Создаем последний backup перед выключением
        self.create_backup("shutdown", "Backup before system shutdown")

# Глобальный экземпляр системы
core_system = CoreSystem()

def get_system_status() -> Dict[str, Any]:
    """Получить статус системы"""
    return core_system.get_system_status()

def create_backup(description: str = "") -> str:
    """Создать backup"""
    return core_system.create_backup("manual", description)

def emergency_backup() -> str:
    """Экстренный backup"""
    return core_system.emergency_backup()

def track_user(user_id: int, action: str, response_time: float = 0.0):
    """Отследить действие пользователя"""
    return core_system.track_user_action(user_id, action, response_time)

def log_error(error_type: str, message: str, user_id: Optional[int] = None):
    """Залогировать ошибку"""
    return core_system.log_error(error_type, message, user_id)

if __name__ == "__main__":
    print("🔥 Core System запущен в standalone режиме")
    print("Доступные команды:")
    print("  status   - показать статус системы")
    print("  backup   - создать backup")
    print("  list     - список backup'ов")
    print("  help     - показать справку")
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == "status":
                status = get_system_status()
                print(json.dumps(status, indent=2, ensure_ascii=False))
            
            elif cmd == "backup":
                description = input("Описание backup (опционально): ").strip()
                backup_id = create_backup(description)
                if backup_id:
                    print(f"✅ Создан backup: {backup_id}")
                else:
                    print("❌ Ошибка создания backup")
            
            elif cmd == "list":
                backups = core_system.list_backups()
                for backup in backups[:10]:  # Показываем последние 10
                    size_mb = backup.size_bytes / 1024 / 1024
                    print(f"{backup.backup_id} | {backup.timestamp} | "
                          f"{backup.backup_type} | {size_mb:.1f}MB | {backup.description}")
            
            elif cmd in ["exit", "quit", "q"]:
                core_system.shutdown()
                break
            
            elif cmd == "help":
                print("Доступные команды:")
                print("  status   - показать статус системы")
                print("  backup   - создать backup")
                print("  list     - список backup'ов")
                print("  exit     - выход")
            
            else:
                print("Неизвестная команда. Используйте 'help' для справки.")
                
        except KeyboardInterrupt:
            print("\n🛑 Завершение работы...")
            core_system.shutdown()
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}") 