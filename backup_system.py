#!/usr/bin/env python3
"""
💾 СИСТЕМА АВТОМАТИЧЕСКОГО BACKUP И ВОССТАНОВЛЕНИЯ 💾
Автоматическое резервное копирование всех критически важных данных
Поддержка локального и облачного хранения
"""

import os
import json
import shutil
import tarfile
import zipfile
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import tempfile

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
    retention_days: int

class BackupSystem:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Конфигурация backup
        self.config = {
            'auto_backup_enabled': True,
            'backup_interval_hours': 6,  # Каждые 6 часов
            'retention_days': 30,        # Хранить 30 дней
            'max_backups': 100,         # Максимум 100 backup файлов
            'compress_backups': True,    # Сжимать backup
            'verify_backups': True,      # Проверять целостность
        }
        
        # Файлы для backup
        self.backup_targets = {
            'users': {
                'files': ['premium_users.json', 'users.json'],
                'description': 'User data and subscriptions',
                'priority': 'critical'
            },
            'cache': {
                'files': ['response_cache.json'],
                'description': 'Response cache data',
                'priority': 'normal'
            },
            'monitoring': {
                'files': ['monitoring.db'],
                'description': 'Monitoring database',
                'priority': 'normal'
            },
            'config': {
                'files': ['monetization_config.py', 'config.py'],
                'description': 'System configuration',
                'priority': 'high'
            },
            'templates': {
                'files': ['adult_templates.py'],
                'description': 'Content templates',
                'priority': 'high'
            }
        }
        
        self.backup_history = []
        self.is_running = True
        
        # Загружаем историю backup
        self.load_backup_history()
        
        # Запускаем автоматический backup
        if self.config['auto_backup_enabled']:
            self.start_auto_backup()
        
        print("💾 Backup System: АКТИВИРОВАН")

    def start_auto_backup(self):
        """Запуск автоматического backup в фоне"""
        def backup_worker():
            while self.is_running:
                try:
                    time.sleep(self.config['backup_interval_hours'] * 3600)
                    if self.is_running:
                        self.create_auto_backup()
                        self.cleanup_old_backups()
                except Exception as e:
                    print(f"❌ Auto backup error: {e}")
                    time.sleep(3600)  # Повторить через час при ошибке
        
        backup_thread = threading.Thread(target=backup_worker)
        backup_thread.daemon = True
        backup_thread.start()
        print("🔄 Auto backup: ВКЛЮЧЕН")

    def create_backup(self, backup_type: str = "manual", description: str = "", 
                     targets: List[str] = None) -> str:
        """Создание backup"""
        timestamp = datetime.now()
        backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        if not targets:
            targets = list(self.backup_targets.keys())
        
        try:
            # Создаем временную директорию
            with tempfile.TemporaryDirectory() as temp_dir:
                backup_temp_path = Path(temp_dir) / backup_id
                backup_temp_path.mkdir()
                
                # Собираем файлы
                collected_files = []
                for target in targets:
                    if target in self.backup_targets:
                        target_info = self.backup_targets[target]
                        target_dir = backup_temp_path / target
                        target_dir.mkdir()
                        
                        for file_name in target_info['files']:
                            if os.path.exists(file_name):
                                dest_path = target_dir / file_name
                                shutil.copy2(file_name, dest_path)
                                collected_files.append(file_name)
                
                # Добавляем метаданные
                metadata = {
                    'backup_id': backup_id,
                    'timestamp': timestamp.isoformat(),
                    'backup_type': backup_type,
                    'description': description or f"Auto backup - {timestamp.strftime('%Y-%m-%d %H:%M')}",
                    'targets': targets,
                    'files_included': collected_files,
                    'created_by': 'backup_system',
                    'version': '1.0'
                }
                
                metadata_file = backup_temp_path / 'backup_metadata.json'
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                # Создаем архив
                if self.config['compress_backups']:
                    archive_path = self.backup_dir / f"{backup_id}.tar.gz"
                    with tarfile.open(archive_path, 'w:gz') as tar:
                        tar.add(backup_temp_path, arcname=backup_id)
                else:
                    archive_path = self.backup_dir / f"{backup_id}.zip"
                    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for file_path in backup_temp_path.rglob('*'):
                            if file_path.is_file():
                                arcname = file_path.relative_to(backup_temp_path.parent)
                                zf.write(file_path, arcname)
                
                # Вычисляем checksum
                checksum = self.calculate_file_checksum(archive_path)
                
                # Сохраняем информацию о backup
                backup_info = BackupInfo(
                    backup_id=backup_id,
                    timestamp=timestamp.isoformat(),
                    backup_type=backup_type,
                    file_path=str(archive_path),
                    size_bytes=archive_path.stat().st_size,
                    checksum=checksum,
                    description=metadata['description'],
                    retention_days=self.config['retention_days']
                )
                
                self.backup_history.append(backup_info)
                self.save_backup_history()
                
                # Проверяем целостность если включено
                if self.config['verify_backups']:
                    if self.verify_backup(backup_id):
                        print(f"✅ Backup created and verified: {backup_id}")
                    else:
                        print(f"⚠️ Backup created but verification failed: {backup_id}")
                else:
                    print(f"✅ Backup created: {backup_id}")
                
                return backup_id
                
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return ""

    def create_auto_backup(self) -> str:
        """Создание автоматического backup"""
        return self.create_backup(
            backup_type="auto",
            description=f"Automatic backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

    def create_critical_backup(self) -> str:
        """Создание критического backup (только важные данные)"""
        critical_targets = [
            target for target, info in self.backup_targets.items()
            if info['priority'] == 'critical'
        ]
        
        return self.create_backup(
            backup_type="critical",
            description=f"Critical data backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            targets=critical_targets
        )

    def restore_backup(self, backup_id: str, restore_path: str = None) -> bool:
        """Восстановление backup"""
        backup_info = self.get_backup_info(backup_id)
        if not backup_info:
            print(f"❌ Backup {backup_id} not found")
            return False
        
        backup_path = Path(backup_info.file_path)
        if not backup_path.exists():
            print(f"❌ Backup file not found: {backup_path}")
            return False
        
        try:
            # Проверяем целостность
            if not self.verify_backup(backup_id):
                print(f"❌ Backup integrity check failed: {backup_id}")
                return False
            
            # Создаем точку восстановления
            restore_point = self.create_restore_point()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                extract_path = Path(temp_dir) / "extracted"
                
                # Извлекаем архив
                if backup_path.suffix == '.gz':
                    with tarfile.open(backup_path, 'r:gz') as tar:
                        tar.extractall(extract_path)
                else:
                    with zipfile.ZipFile(backup_path, 'r') as zf:
                        zf.extractall(extract_path)
                
                # Находим данные backup
                backup_data_path = extract_path / backup_id
                if not backup_data_path.exists():
                    backup_data_path = extract_path
                
                # Загружаем метаданные
                metadata_file = backup_data_path / 'backup_metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    print(f"📋 Restoring backup: {metadata.get('description', backup_id)}")
                
                # Восстанавливаем файлы
                restored_files = []
                for target_dir in backup_data_path.iterdir():
                    if target_dir.is_dir() and target_dir.name != 'backup_metadata.json':
                        for file_path in target_dir.rglob('*'):
                            if file_path.is_file():
                                relative_path = file_path.relative_to(target_dir)
                                
                                if restore_path:
                                    dest_path = Path(restore_path) / relative_path
                                else:
                                    dest_path = Path.cwd() / relative_path
                                
                                # Создаем директорию если нужно
                                dest_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Копируем файл
                                shutil.copy2(file_path, dest_path)
                                restored_files.append(str(dest_path))
                
                print(f"✅ Backup restored successfully: {len(restored_files)} files")
                print(f"📝 Restore point created: {restore_point}")
                return True
                
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False

    def create_restore_point(self) -> str:
        """Создание точки восстановления перед restore"""
        restore_point_id = f"restore_point_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            return self.create_backup(
                backup_type="restore_point",
                description=f"Restore point before recovery - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        except Exception as e:
            print(f"⚠️ Failed to create restore point: {e}")
            return ""

    def verify_backup(self, backup_id: str) -> bool:
        """Проверка целостности backup"""
        backup_info = self.get_backup_info(backup_id)
        if not backup_info:
            return False
        
        backup_path = Path(backup_info.file_path)
        if not backup_path.exists():
            return False
        
        try:
            # Проверяем checksum
            current_checksum = self.calculate_file_checksum(backup_path)
            if current_checksum != backup_info.checksum:
                print(f"❌ Checksum mismatch for backup {backup_id}")
                return False
            
            # Проверяем, что архив можно открыть
            if backup_path.suffix == '.gz':
                with tarfile.open(backup_path, 'r:gz') as tar:
                    # Проверяем первый файл
                    members = tar.getmembers()
                    if not members:
                        return False
            else:
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    # Проверяем архив
                    result = zf.testzip()
                    if result is not None:
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ Backup verification failed: {e}")
            return False

    def list_backups(self, backup_type: str = None) -> List[BackupInfo]:
        """Список доступных backup"""
        if backup_type:
            return [b for b in self.backup_history if b.backup_type == backup_type]
        return self.backup_history.copy()

    def get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Получение информации о backup"""
        for backup in self.backup_history:
            if backup.backup_id == backup_id:
                return backup
        return None

    def delete_backup(self, backup_id: str) -> bool:
        """Удаление backup"""
        backup_info = self.get_backup_info(backup_id)
        if not backup_info:
            return False
        
        try:
            backup_path = Path(backup_info.file_path)
            if backup_path.exists():
                backup_path.unlink()
            
            self.backup_history = [b for b in self.backup_history if b.backup_id != backup_id]
            self.save_backup_history()
            
            print(f"✅ Backup deleted: {backup_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete backup: {e}")
            return False

    def cleanup_old_backups(self):
        """Очистка старых backup"""
        cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
        deleted_count = 0
        
        for backup in self.backup_history.copy():
            backup_date = datetime.fromisoformat(backup.timestamp)
            
            # Удаляем старые backup (кроме критических)
            if backup_date < cutoff_date and backup.backup_type != "critical":
                if self.delete_backup(backup.backup_id):
                    deleted_count += 1
        
        # Ограничиваем общее количество backup
        if len(self.backup_history) > self.config['max_backups']:
            # Сортируем по дате и удаляем самые старые
            sorted_backups = sorted(self.backup_history, key=lambda x: x.timestamp)
            excess_count = len(self.backup_history) - self.config['max_backups']
            
            for backup in sorted_backups[:excess_count]:
                if backup.backup_type != "critical":
                    if self.delete_backup(backup.backup_id):
                        deleted_count += 1
        
        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old backups")

    def calculate_file_checksum(self, file_path: Path) -> str:
        """Вычисление MD5 checksum файла"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_backup_statistics(self) -> Dict[str, Any]:
        """Статистика backup системы"""
        total_size = sum(b.size_bytes for b in self.backup_history)
        
        # Группировка по типам
        type_counts = {}
        type_sizes = {}
        for backup in self.backup_history:
            backup_type = backup.backup_type
            type_counts[backup_type] = type_counts.get(backup_type, 0) + 1
            type_sizes[backup_type] = type_sizes.get(backup_type, 0) + backup.size_bytes
        
        # Последний backup
        latest_backup = None
        if self.backup_history:
            latest_backup = max(self.backup_history, key=lambda x: x.timestamp)
        
        return {
            'total_backups': len(self.backup_history),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'backup_types': type_counts,
            'type_sizes_mb': {k: round(v / 1024 / 1024, 2) for k, v in type_sizes.items()},
            'latest_backup': {
                'id': latest_backup.backup_id,
                'timestamp': latest_backup.timestamp,
                'type': latest_backup.backup_type
            } if latest_backup else None,
            'auto_backup_enabled': self.config['auto_backup_enabled'],
            'backup_interval_hours': self.config['backup_interval_hours'],
            'retention_days': self.config['retention_days']
        }

    def export_backup_history(self) -> str:
        """Экспорт истории backup в JSON"""
        history_data = {
            'export_date': datetime.now().isoformat(),
            'backup_system_version': '1.0',
            'config': self.config,
            'backups': [asdict(backup) for backup in self.backup_history]
        }
        
        export_file = self.backup_dir / f"backup_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Backup history exported: {export_file}")
        return str(export_file)

    def save_backup_history(self):
        """Сохранение истории backup"""
        history_file = self.backup_dir / 'backup_history.json'
        history_data = [asdict(backup) for backup in self.backup_history]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)

    def load_backup_history(self):
        """Загрузка истории backup"""
        history_file = self.backup_dir / 'backup_history.json'
        
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                self.backup_history = [
                    BackupInfo(**backup_data) for backup_data in history_data
                ]
                print(f"📚 Loaded {len(self.backup_history)} backup records")
                
            except Exception as e:
                print(f"⚠️ Failed to load backup history: {e}")
                self.backup_history = []

    def update_config(self, new_config: Dict[str, Any]):
        """Обновление конфигурации backup"""
        self.config.update(new_config)
        print("⚙️ Backup configuration updated")

    def emergency_backup(self) -> str:
        """Экстренное backup всех критических данных"""
        print("🚨 Creating emergency backup...")
        
        # Отправляем алерт
        try:
            from notification_system import send_warning_alert
            send_warning_alert(
                "Emergency Backup Created",
                "Emergency backup procedure initiated",
                "backup_system",
                {"backup_type": "emergency", "timestamp": datetime.now().isoformat()}
            )
        except:
            pass
        
        return self.create_backup(
            backup_type="emergency",
            description=f"Emergency backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def shutdown(self):
        """Остановка backup системы"""
        self.is_running = False
        
        # Создаем final backup перед выключением
        print("💾 Creating final backup before shutdown...")
        final_backup = self.create_backup(
            backup_type="final",
            description=f"Final backup before shutdown - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        print(f"✅ Final backup created: {final_backup}")
        print("🛑 Backup System: ОСТАНОВЛЕН")

# Глобальная система backup
backup_system = BackupSystem()

# Convenience функции
def create_manual_backup(description: str = "") -> str:
    """Создание ручного backup"""
    return backup_system.create_backup("manual", description)

def create_emergency_backup() -> str:
    """Создание экстренного backup"""
    return backup_system.emergency_backup()

def restore_from_backup(backup_id: str) -> bool:
    """Восстановление из backup"""
    return backup_system.restore_backup(backup_id)

def list_available_backups() -> List[BackupInfo]:
    """Список доступных backup"""
    return backup_system.list_backups() 