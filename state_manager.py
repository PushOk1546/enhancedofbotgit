"""
Менеджер состояний пользователей.
Обрабатывает создание, обновление и сохранение состояний пользователей.
КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ от команды сеньор разработчиков:
- Атомарная запись данных для предотвращения коррупции
- Улучшенное управление памятью
- Асинхронные операции ввода/вывода
- НОВОЕ: Автоматическая очистка старых временных файлов
"""

import json
import logging
import asyncio
import os
import tempfile
import shutil
import gc
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field

logger = logging.getLogger("bot_logger")

@dataclass
class UserPreferences:
    """Предпочтения пользователя"""
    content_types: List[str] = field(default_factory=list)
    price_range: str = "any"
    communication_style: str = "friendly"
    notification_frequency: str = "sometimes"
    completed_survey: bool = False

@dataclass
class UserState:
    """Состояние пользователя"""
    user_id: int
    model: str = "eco"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    preferences: UserPreferences = field(default_factory=UserPreferences)
    current_survey_step: Optional[str] = None
    waiting_for_reply: bool = False
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Дополнительные поля для чатов
    waiting_for_chat_name: bool = False
    waiting_for_chat_reply: bool = False
    chat_manager = None
    
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Строгие лимиты для memory management
    MAX_HISTORY_SIZE = 50
    MAX_CONTENT_LENGTH = 4000  # 🆕 Увеличено для двуязычных сообщений (EN + RU)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует состояние в словарь для сериализации"""
        data = asdict(self)
        data['preferences'] = asdict(self.preferences)
        
        # Сериализуем chat_manager если он есть
        if self.chat_manager is not None:
            data['chat_manager'] = self.chat_manager.to_dict()
        else:
            data['chat_manager'] = None
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserState':
        """Создает состояние из словаря"""
        preferences_data = data.pop('preferences', {})
        preferences = UserPreferences(**preferences_data)
        
        # Восстанавливаем chat_manager если он есть
        chat_manager_data = data.pop('chat_manager', None)
        
        user_state = cls(
            preferences=preferences,
            **data
        )
        
        # Создаем ChatManager если есть данные
        if chat_manager_data is not None:
            from chat_models import ChatManager
            user_state.chat_manager = ChatManager.from_dict(chat_manager_data)
        else:
            user_state.chat_manager = None
            
        return user_state
    
    def add_message_to_history(self, role: str, content: str):
        """
        Добавляет сообщение в историю пользователя.
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Контроль памяти и принудительная очистка.
        """
        # Обрезаем контент для экономии памяти
        truncated_content = content[:self.MAX_CONTENT_LENGTH]
        if len(content) > self.MAX_CONTENT_LENGTH:
            logger.warning(f"Content truncated for user {self.user_id}: {len(content)} -> {self.MAX_CONTENT_LENGTH}")
        
        message = {
            'role': role,
            'content': truncated_content,
            'timestamp': datetime.now().isoformat()
        }
        
        self.history.append(message)
        
        # ПРИНУДИТЕЛЬНАЯ очистка памяти
        if len(self.history) > self.MAX_HISTORY_SIZE:
            # Удаляем старые сообщения и освобождаем память
            removed_count = len(self.history) - self.MAX_HISTORY_SIZE
            removed_messages = self.history[:-self.MAX_HISTORY_SIZE]
            self.history = self.history[-self.MAX_HISTORY_SIZE:]
            
            # Явная очистка памяти
            del removed_messages
            gc.collect()
            
            logger.debug(f"Memory cleanup: removed {removed_count} old messages for user {self.user_id}")
    
    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = datetime.now().isoformat()

class StateManager:
    """
    Менеджер состояний пользователей.
    КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ:
    - Атомарная запись данных
    - Асинхронные операции I/O
    - Улучшенная обработка ошибок
    - НОВОЕ: Автоматическая очистка временных файлов
    """
    
    def __init__(self, data_file: str = 'data/users.json'):
        self.data_file = data_file
        self.users: Dict[int, UserState] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        
        # Создаем директорию если её нет
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Очистка старых временных файлов при инициализации
        self._cleanup_old_temp_files()
        
        # Попытка синхронной загрузки при первой инициализации
        self._sync_load_data()
    
    def _cleanup_old_temp_files(self):
        """
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Очистка старых временных файлов.
        Удаляет все .tmp файлы связанные с данным файлом данных.
        """
        try:
            # Ищем все временные файлы для этого data_file
            pattern = f"{self.data_file}.tmp.*"
            temp_files = glob.glob(pattern)
            
            cleaned_count = 0
            for temp_file in temp_files:
                try:
                    # Проверяем что файл действительно временный и старый
                    if os.path.exists(temp_file):
                        # Удаляем файлы старше 1 минуты (чтобы не удалить активные)
                        file_age = os.path.getmtime(temp_file)
                        current_time = datetime.now().timestamp()
                        
                        if current_time - file_age > 60:  # 60 секунд
                            os.remove(temp_file)
                            cleaned_count += 1
                            logger.debug(f"Cleaned up old temp file: {temp_file}")
                        
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file {temp_file}: {cleanup_error}")
            
            if cleaned_count > 0:
                logger.info(f"🧹 Startup cleanup: removed {cleaned_count} old temporary files")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup old temp files: {e}")
    
    def _sync_load_data(self):
        """Синхронная загрузка данных при инициализации"""
        try:
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for user_id_str, user_data in data.items():
                    user_id = int(user_id_str)
                    self.users[user_id] = UserState.from_dict(user_data)
                
                logger.info(f"Loaded {len(self.users)} users from {self.data_file}")
                
            except FileNotFoundError:
                logger.info(f"Data file {self.data_file} not found, starting with empty state")
                self.users = {}
        except Exception as e:
            logger.error(f"Error loading user data: {str(e)}", exc_info=True)
            self.users = {}
        
        self._initialized = True
    
    async def ensure_initialized(self):
        """Гарантирует, что данные загружены (для async контекста)"""
        if not self._initialized:
            await self.load_data()
    
    async def load_data(self):
        """
        Загружает данные пользователей из файла (async версия).
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Использует асинхронный I/O.
        """
        try:
            async with self._lock:
                try:
                    # ИСПРАВЛЕНИЕ: Используем асинхронное чтение
                    try:
                        import aiofiles
                        async with aiofiles.open(self.data_file, 'r', encoding='utf-8') as f:
                            content = await f.read()
                            data = json.loads(content)
                    except ImportError:
                        # Fallback на синхронный режим если aiofiles недоступен
                        logger.warning("aiofiles not available, using sync I/O")
                        with open(self.data_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    
                    for user_id_str, user_data in data.items():
                        user_id = int(user_id_str)
                        self.users[user_id] = UserState.from_dict(user_data)
                    
                    logger.info(f"Async loaded {len(self.users)} users from {self.data_file}")
                    
                except FileNotFoundError:
                    logger.info(f"Data file {self.data_file} not found, starting with empty state")
                    self.users = {}
                    
                self._initialized = True
                    
        except Exception as e:
            logger.error(f"Error loading user data: {str(e)}", exc_info=True)
            self.users = {}
    
    async def save_data(self):
        """
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Атомарная запись данных.
        Предотвращает коррупцию файлов при сбоях.
        ОБНОВЛЕНО: Улучшенная очистка временных файлов.
        """
        temp_file = None
        try:
            async with self._lock:
                # ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА: Очищаем старые временные файлы перед записью
                self._cleanup_old_temp_files()
                
                # Преобразуем данные для сериализации
                data = {}
                for user_id, user_state in self.users.items():
                    data[str(user_id)] = user_state.to_dict()
                
                # АТОМАРНАЯ ЗАПИСЬ: используем временный файл
                temp_file = f"{self.data_file}.tmp.{os.getpid()}.{int(datetime.now().timestamp())}"
                
                try:
                    import aiofiles
                    # Асинхронная запись
                    async with aiofiles.open(temp_file, 'w', encoding='utf-8') as f:
                        await f.write(json.dumps(data, ensure_ascii=False, indent=2))
                except ImportError:
                    # Fallback на синхронную запись
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Атомарное перемещение файла
                shutil.move(temp_file, self.data_file)
                temp_file = None  # Файл успешно перемещен
                
                logger.debug(f"✅ Atomically saved {len(self.users)} users to {self.data_file}")
                
        except Exception as e:
            logger.error(f"🚨 CRITICAL: Error saving user data: {str(e)}", exc_info=True)
            
            # Очистка временного файла при ошибке
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup temp file: {cleanup_error}")
            
            # Пробрасываем исключение для уведомления вышестоящего кода
            raise
    
    def get_user(self, user_id: int) -> UserState:
        """Получает состояние пользователя, создает новое если не существует"""
        if user_id not in self.users:
            self.users[user_id] = UserState(user_id=user_id)
            logger.info(f"Created new user state for {user_id}")
        
        # Обновляем время последней активности
        self.users[user_id].last_activity = datetime.now().isoformat()
        
        return self.users[user_id]
    
    def add_to_history(self, user_id: int, role: str, content: str):
        """
        Добавляет сообщение в историю пользователя.
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Использует улучшенный memory management.
        """
        user = self.get_user(user_id)
        user.add_message_to_history(role, content)
        
        logger.debug(f"Added message to history for user {user_id}: {role}")
    
    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает историю сообщений пользователя"""
        user = self.get_user(user_id)
        return user.history[-limit:] if limit > 0 else user.history
    
    def get_user_count(self) -> int:
        """Возвращает общее количество пользователей"""
        return len(self.users)
    
    def get_active_users(self, hours: int = 24) -> List[UserState]:
        """Возвращает список активных пользователей за указанное время"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        active_users = []
        
        for user in self.users.values():
            try:
                last_activity = datetime.fromisoformat(user.last_activity)
                if last_activity > cutoff_time:
                    active_users.append(user)
            except (ValueError, TypeError):
                # Игнорируем пользователей с некорректными временными метками
                continue
        
        return active_users
    
    async def load_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Загружает промпт из файла или возвращает None если не найден.
        ИСПРАВЛЕНИЕ: Добавлена асинхронная версия.
        """
        try:
            # Создаем директорию prompts если её нет
            prompts_dir = 'prompts'
            os.makedirs(prompts_dir, exist_ok=True)
            
            prompt_file = f"{prompts_dir}/{prompt_name}.txt"
            
            # Проверяем существование файла
            if not os.path.exists(prompt_file):
                logger.debug(f"Prompt file not found: {prompt_file}")
                return None
            
            # Асинхронное чтение содержимого файла
            try:
                import aiofiles
                async with aiofiles.open(prompt_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
            except ImportError:
                # Fallback на синхронное чтение
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            content = content.strip()
            
            if content:
                logger.debug(f"Loaded prompt: {prompt_name}")
                return content
            else:
                logger.warning(f"Empty prompt file: {prompt_file}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading prompt {prompt_name}: {str(e)}", exc_info=True)
            return None
    
    def save_user(self, user_id: int, user_state: UserState):
        """Сохраняет состояние пользователя"""
        self.users[user_id] = user_state
        logger.debug(f"Updated user state for {user_id}")
    
    def cleanup_memory(self):
        """
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Принудительная очистка памяти.
        Вызывается периодически для предотвращения memory leaks.
        """
        logger.debug("Starting memory cleanup...")
        
        cleaned_users = 0
        for user_state in self.users.values():
            if len(user_state.history) > user_state.MAX_HISTORY_SIZE:
                old_size = len(user_state.history)
                user_state.history = user_state.history[-user_state.MAX_HISTORY_SIZE:]
                cleaned_users += 1
                logger.debug(f"Cleaned history for user {user_state.user_id}: {old_size} -> {len(user_state.history)}")
        
        # Принудительная сборка мусора
        gc.collect()
        
        logger.info(f"Memory cleanup completed: {cleaned_users} users cleaned")
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """Возвращает статистику системы"""
        import psutil
        
        return {
            "users_count": len(self.users),
            "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "active_users_24h": len(self.get_active_users(24)),
            "data_file_size_kb": os.path.getsize(self.data_file) / 1024 if os.path.exists(self.data_file) else 0,
            "total_messages": sum(len(user.history) for user in self.users.values())
        }

    def force_cleanup_temp_files(self):
        """
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Принудительная очистка всех временных файлов.
        Для использования в emergency случаях.
        """
        try:
            pattern = f"{self.data_file}.tmp.*"
            temp_files = glob.glob(pattern)
            
            cleaned_count = 0
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        cleaned_count += 1
                        logger.debug(f"Force cleaned temp file: {temp_file}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to force cleanup temp file {temp_file}: {cleanup_error}")
            
            if cleaned_count > 0:
                logger.info(f"🔧 Force cleanup: removed {cleaned_count} temporary files")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to force cleanup temp files: {e}")
            return 0 