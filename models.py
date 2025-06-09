"""
Модели данных для OF Assistant Bot.
Содержит классы для управления состоянием пользователей и напоминаниями.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import logging
import json

# Fallback для cachetools если не установлен
try:
    from cachetools import TTLCache
except ImportError:
    # Простая реализация TTLCache для fallback
    class TTLCache(dict):
        def __init__(self, maxsize=100, ttl=3600):
            super().__init__()
            self.maxsize = maxsize
            self.ttl = ttl


# === БАЗОВЫЕ МОДЕЛИ ДЛЯ MVP ===

@dataclass
class User:
    """Базовая модель пользователя для MVP"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_bot: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Статистика активности
    total_messages: int = 0
    total_replies_generated: int = 0
    total_commands_used: int = 0
    
    def get_full_name(self) -> str:
        """Получить полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.user_id}"
    
    def get_display_name(self) -> str:
        """Получить отображаемое имя пользователя"""
        if self.username:
            return f"@{self.username}"
        else:
            return self.get_full_name()
    
    def update_activity(self) -> None:
        """Обновить время последней активности"""
        self.last_activity = datetime.now()
    
    def increment_messages(self) -> None:
        """Увеличить счетчик сообщений"""
        self.total_messages += 1
        self.update_activity()
    
    def increment_replies(self) -> None:
        """Увеличить счетчик сгенерированных ответов"""
        self.total_replies_generated += 1
        self.update_activity()
    
    def increment_commands(self) -> None:
        """Увеличить счетчик использованных команд"""
        self.total_commands_used += 1
        self.update_activity()
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация пользователя в словарь"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "language_code": self.language_code,
            "is_bot": self.is_bot,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "total_messages": self.total_messages,
            "total_replies_generated": self.total_replies_generated,
            "total_commands_used": self.total_commands_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Десериализация пользователя из словаря"""
        return cls(
            user_id=data["user_id"],
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            language_code=data.get("language_code"),
            is_bot=data.get("is_bot", False),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_activity=datetime.fromisoformat(data.get("last_activity", datetime.now().isoformat())),
            total_messages=data.get("total_messages", 0),
            total_replies_generated=data.get("total_replies_generated", 0),
            total_commands_used=data.get("total_commands_used", 0)
        )


@dataclass
class Message:
    """Базовая модель сообщения для MVP"""
    message_id: str  # MD5 хеш для уникальности
    user_id: int
    text: str
    message_type: str = "user_message"  # user_message, command, reply
    created_at: datetime = field(default_factory=datetime.now)
    
    # Метаданные сообщения
    chat_id: Optional[int] = None
    chat_type: Optional[str] = None
    message_length: int = field(init=False)
    
    # Контекст команды (если применимо)
    command: Optional[str] = None
    command_args: Optional[str] = None
    
    def __post_init__(self):
        """Автоматическое вычисление длины сообщения"""
        self.message_length = len(self.text)
    
    def get_preview(self, max_length: int = 50) -> str:
        """Получить превью сообщения"""
        if len(self.text) <= max_length:
            return self.text
        return self.text[:max_length] + "..."
    
    def is_command(self) -> bool:
        """Проверить является ли сообщение командой"""
        return self.message_type == "command" or self.text.startswith("/")
    
    def get_command_info(self) -> tuple[Optional[str], Optional[str]]:
        """Извлечь информацию о команде"""
        if self.is_command():
            parts = self.text.split(" ", 1)
            command = parts[0].lstrip("/")
            args = parts[1] if len(parts) > 1 else None
            return command, args
        return None, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация сообщения в словарь"""
        return {
            "message_id": self.message_id,
            "user_id": self.user_id,
            "text": self.text,
            "message_type": self.message_type,
            "created_at": self.created_at.isoformat(),
            "chat_id": self.chat_id,
            "chat_type": self.chat_type,
            "message_length": self.message_length,
            "command": self.command,
            "command_args": self.command_args
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Десериализация сообщения из словаря"""
        return cls(
            message_id=data["message_id"],
            user_id=data["user_id"],
            text=data["text"],
            message_type=data.get("message_type", "user_message"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            chat_id=data.get("chat_id"),
            chat_type=data.get("chat_type"),
            command=data.get("command"),
            command_args=data.get("command_args")
        )


@dataclass
class Reply:
    """Базовая модель ответа для MVP"""
    reply_id: str  # Уникальный ID ответа
    original_message_id: str  # ID исходного сообщения
    user_id: int
    style: str  # friendly, flirty, passionate, romantic, professional
    variants: List[str] = field(default_factory=list)
    selected_variant: Optional[str] = None
    selected_index: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    selected_at: Optional[datetime] = None
    
    # Метаданные генерации
    generation_time_ms: Optional[int] = None
    from_cache: bool = False
    groq_api_used: bool = False
    
    # Статистика
    total_variants: int = field(init=False)
    
    def __post_init__(self):
        """Автоматическое вычисление количества вариантов"""
        self.total_variants = len(self.variants)
    
    def select_variant(self, index: int) -> bool:
        """Выбрать вариант ответа по индексу"""
        if 0 <= index < len(self.variants):
            self.selected_index = index
            self.selected_variant = self.variants[index]
            self.selected_at = datetime.now()
            return True
        return False
    
    def get_selected_variant(self) -> Optional[str]:
        """Получить выбранный вариант"""
        return self.selected_variant
    
    def is_selected(self) -> bool:
        """Проверить выбран ли вариант"""
        return self.selected_variant is not None
    
    def add_variant(self, variant: str) -> None:
        """Добавить новый вариант ответа"""
        self.variants.append(variant)
        self.total_variants = len(self.variants)
    
    def get_style_display_name(self) -> str:
        """Получить отображаемое имя стиля"""
        style_names = {
            "friendly": "Дружелюбный",
            "flirty": "Флиртующий",
            "passionate": "Страстный",
            "romantic": "Романтичный",
            "professional": "Профессиональный"
        }
        return style_names.get(self.style, self.style.title())
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Получить статистику генерации"""
        return {
            "total_variants": self.total_variants,
            "generation_time_ms": self.generation_time_ms,
            "from_cache": self.from_cache,
            "groq_api_used": self.groq_api_used,
            "is_selected": self.is_selected(),
            "style": self.get_style_display_name()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация ответа в словарь"""
        return {
            "reply_id": self.reply_id,
            "original_message_id": self.original_message_id,
            "user_id": self.user_id,
            "style": self.style,
            "variants": self.variants,
            "selected_variant": self.selected_variant,
            "selected_index": self.selected_index,
            "created_at": self.created_at.isoformat(),
            "selected_at": self.selected_at.isoformat() if self.selected_at else None,
            "generation_time_ms": self.generation_time_ms,
            "from_cache": self.from_cache,
            "groq_api_used": self.groq_api_used,
            "total_variants": self.total_variants
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reply':
        """Десериализация ответа из словаря"""
        reply = cls(
            reply_id=data["reply_id"],
            original_message_id=data["original_message_id"],
            user_id=data["user_id"],
            style=data["style"],
            variants=data.get("variants", []),
            selected_variant=data.get("selected_variant"),
            selected_index=data.get("selected_index"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            selected_at=datetime.fromisoformat(data["selected_at"]) if data.get("selected_at") else None,
            generation_time_ms=data.get("generation_time_ms"),
            from_cache=data.get("from_cache", False),
            groq_api_used=data.get("groq_api_used", False)
        )
        return reply


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С МОДЕЛЯМИ ===

def create_message_from_telegram(telegram_message, message_type: str = "user_message") -> Message:
    """Создать объект Message из Telegram сообщения"""
    import hashlib
    
    # Создаем уникальный ID сообщения
    message_id = hashlib.md5(
        f"{telegram_message.from_user.id}_{telegram_message.text}_{datetime.now().timestamp()}".encode()
    ).hexdigest()[:12]
    
    # Извлекаем информацию о команде если есть
    command = None
    command_args = None
    if telegram_message.text.startswith("/"):
        parts = telegram_message.text.split(" ", 1)
        command = parts[0].lstrip("/")
        command_args = parts[1] if len(parts) > 1 else None
        message_type = "command"
    
    return Message(
        message_id=message_id,
        user_id=telegram_message.from_user.id,
        text=telegram_message.text,
        message_type=message_type,
        chat_id=telegram_message.chat.id,
        chat_type=telegram_message.chat.type,
        command=command,
        command_args=command_args
    )


def create_user_from_telegram(telegram_user) -> User:
    """Создать объект User из Telegram пользователя"""
    return User(
        user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
        language_code=telegram_user.language_code,
        is_bot=telegram_user.is_bot
    )


def create_reply(message: Message, style: str, variants: List[str]) -> Reply:
    """Создать объект Reply для сообщения"""
    import hashlib
    
    # Создаем уникальный ID ответа
    reply_id = hashlib.md5(
        f"{message.message_id}_{style}_{datetime.now().timestamp()}".encode()
    ).hexdigest()[:12]
    
    return Reply(
        reply_id=reply_id,
        original_message_id=message.message_id,
        user_id=message.user_id,
        style=style,
        variants=variants
    )


# === СУЩЕСТВУЮЩИЕ МОДЕЛИ (расширенные для совместимости) ===

class ConversationStage(Enum):
    """Этапы разговора с клиентом"""
    INITIAL = "initial"
    WARMING_UP = "warming_up"
    ENGAGED = "engaged"
    INTERESTED = "interested"
    READY_TO_BUY = "ready_to_buy"
    PURCHASED = "purchased"
    REGULAR = "regular"


@dataclass
class UserPreferences:
    """Предпочтения пользователя"""
    content_types: List[str] = field(default_factory=lambda: ["photos", "videos", "messages"])
    price_range: str = "medium"
    communication_style: str = "friendly"
    notification_frequency: str = "normal"
    completed_survey: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация предпочтений в словарь"""
        return {
            "content_types": self.content_types,
            "price_range": self.price_range,
            "communication_style": self.communication_style,
            "notification_frequency": self.notification_frequency,
            "completed_survey": self.completed_survey
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Десериализация предпочтений из словаря"""
        return cls(
            content_types=data.get("content_types", ["photos", "videos", "messages"]),
            price_range=data.get("price_range", "medium"),
            communication_style=data.get("communication_style", "friendly"),
            notification_frequency=data.get("notification_frequency", "normal"),
            completed_survey=data.get("completed_survey", False)
        )


@dataclass
class PPVReminder:
    """Напоминание о PPV контенте"""
    user_id: int
    message: str
    scheduled_time: datetime
    is_sent: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация напоминания в словарь"""
        return {
            "user_id": self.user_id,
            "message": self.message,
            "scheduled_time": self.scheduled_time.isoformat(),
            "is_sent": self.is_sent,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PPVReminder':
        """Десериализация напоминания из словаря"""
        try:
            return cls(
                user_id=data["user_id"],
                message=data["message"],
                scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
                is_sent=data.get("is_sent", False),
                created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
            )
        except (KeyError, ValueError) as e:
            logging.error(f"Error deserializing PPVReminder: {str(e)}", exc_info=True)
            raise ValueError(f"Invalid PPVReminder data: {str(e)}")


@dataclass
class UserState:
    """Состояние пользователя"""
    # Основные настройки
    model: str = "smart"
    preferences: UserPreferences = field(default_factory=UserPreferences)
    
    # Состояния ожидания
    waiting_for_reply: bool = False
    waiting_for_chat_name: bool = False
    waiting_for_chat_reply: bool = False
    current_survey_step: Optional[str] = None
    
    # История сообщений
    message_history: List[Dict[str, str]] = field(default_factory=list)
    
    # PPV напоминания
    ppv_reminders: List[PPVReminder] = field(default_factory=list)
    
    # Чат менеджер (будет инициализирован при необходимости)
    chat_manager: Optional[Any] = None
    
    # Метаданные
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Кэш для оптимизации
    _cache: TTLCache = field(default_factory=lambda: TTLCache(maxsize=100, ttl=3600))
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация состояния пользователя в словарь"""
        cache_key = f"user_state_dict_{id(self)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        # Сериализация chat_manager
        chat_manager_data = None
        if self.chat_manager:
            try:
                chat_manager_data = self.chat_manager.to_dict()
            except Exception as e:
                logging.error(f"Error serializing chat_manager: {str(e)}", exc_info=True)
        
        data = {
            "model": self.model,
            "preferences": self.preferences.to_dict(),
            "waiting_for_reply": self.waiting_for_reply,
            "waiting_for_chat_name": self.waiting_for_chat_name,
            "waiting_for_chat_reply": self.waiting_for_chat_reply,
            "current_survey_step": self.current_survey_step,
            "message_history": self.message_history,
            "ppv_reminders": [reminder.to_dict() for reminder in self.ppv_reminders],
            "chat_manager": chat_manager_data,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }
        
        self._cache[cache_key] = data
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserState':
        """Десериализация состояния пользователя из словаря"""
        try:
            preferences = UserPreferences.from_dict(data.get("preferences", {}))
            
            ppv_reminders = [
                PPVReminder.from_dict(reminder_data) 
                for reminder_data in data.get("ppv_reminders", [])
            ]
            
            # Десериализация chat_manager
            chat_manager = None
            if data.get("chat_manager"):
                try:
                    from chat_models import ChatManager
                    chat_manager = ChatManager.from_dict(data["chat_manager"])
                except Exception as e:
                    logging.error(f"Error deserializing chat_manager: {str(e)}", exc_info=True)
            
            return cls(
                model=data.get("model", "smart"),
                preferences=preferences,
                waiting_for_reply=data.get("waiting_for_reply", False),
                waiting_for_chat_name=data.get("waiting_for_chat_name", False),
                waiting_for_chat_reply=data.get("waiting_for_chat_reply", False),
                current_survey_step=data.get("current_survey_step"),
                message_history=data.get("message_history", []),
                ppv_reminders=ppv_reminders,
                chat_manager=chat_manager,
                created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                last_activity=datetime.fromisoformat(data.get("last_activity", datetime.now().isoformat()))
            )
        except Exception as e:
            logging.error(f"Error deserializing UserState: {str(e)}", exc_info=True)
            raise ValueError(f"Invalid UserState data: {str(e)}")
    
    def update_activity(self) -> None:
        """Обновление времени последней активности"""
        self.last_activity = datetime.now()
        self._cache.clear()  # Очищаем кэш при обновлении активности
    
    def add_message_to_history(self, role: str, content: str) -> None:
        """Добавление сообщения в историю"""
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Ограничиваем размер истории
        max_history = 50
        if len(self.message_history) > max_history:
            self.message_history = self.message_history[-max_history:]
        
        self._cache.clear()  # Очищаем кэш при изменении истории
    
    def clear_waiting_states(self) -> None:
        """Очистка всех состояний ожидания"""
        self.waiting_for_reply = False
        self.waiting_for_chat_name = False
        self.waiting_for_chat_reply = False
        self.current_survey_step = None
        self._cache.clear()  # Очищаем кэш при изменении состояний 