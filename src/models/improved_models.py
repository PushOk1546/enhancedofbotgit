"""
Улучшенные модели данных для OF Assistant Bot.
Используют Pydantic для валидации и типобезопасности.
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, ClassVar
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, PrivateAttr
import uuid
import json
import logging

from ..core.exceptions import ValidationError, SerializationError
from ..core.validators import ContentType, UserRole


class ConversationStage(str, Enum):
    """Этапы разговора с клиентом"""
    INITIAL = "initial"
    WARMING_UP = "warming_up"
    ENGAGED = "engaged"
    INTERESTED = "interested"
    READY_TO_BUY = "ready_to_buy"
    PURCHASED = "purchased"
    REGULAR = "regular"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class CommunicationStyle(str, Enum):
    """Стили общения"""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    FLIRTY = "flirty"
    CASUAL = "casual"
    ASSERTIVE = "assertive"


class NotificationFrequency(str, Enum):
    """Частота уведомлений"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DISABLED = "disabled"


class ModelType(str, Enum):
    """Типы AI моделей"""
    SMART = "smart"
    CREATIVE = "creative"
    BALANCED = "balanced"
    ECONOMIC = "economic"


class UserPreferences(BaseModel):
    """Улучшенные предпочтения пользователя с валидацией"""
    
    content_types: List[ContentType] = Field(
        default_factory=lambda: [ContentType.PHOTO, ContentType.VIDEO, ContentType.TEXT],
        description="Предпочитаемые типы контента"
    )
    price_range: str = Field(
        default="medium",
        pattern=r"^(low|medium|high|\d+-\d+)$",
        description="Ценовой диапазон"
    )
    communication_style: CommunicationStyle = Field(
        default=CommunicationStyle.FRIENDLY,
        description="Стиль общения"
    )
    notification_frequency: NotificationFrequency = Field(
        default=NotificationFrequency.MEDIUM,
        description="Частота уведомлений"
    )
    completed_survey: bool = Field(
        default=False,
        description="Завершен ли опрос"
    )
    timezone: str = Field(
        default="UTC",
        description="Временная зона пользователя"
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=5,
        description="Язык пользователя"
    )
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительные настройки"
    )
    
    @field_validator('content_types')
    @classmethod
    def validate_content_types(cls, v):
        if not v:
            raise ValidationError("At least one content type must be selected")
        if len(v) > 10:
            raise ValidationError("Too many content types selected")
        return list(set(v))  # Убираем дубликаты
    
    @field_validator('custom_settings')
    @classmethod
    def validate_custom_settings(cls, v):
        # Ограничиваем размер для предотвращения DoS
        if len(str(v)) > 5000:
            raise ValidationError("Custom settings too large")
        return v
    
    model_config = ConfigDict(use_enum_values=True)


class PPVReminder(BaseModel):
    """Улучшенное напоминание о PPV контенте"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Уникальный ID")
    user_id: int = Field(..., gt=0, description="ID пользователя")
    message: str = Field(..., min_length=1, max_length=1000, description="Текст напоминания")
    scheduled_time: datetime = Field(..., description="Время отправки")
    is_sent: bool = Field(default=False, description="Отправлено ли")
    attempts: int = Field(default=0, ge=0, le=5, description="Количество попыток отправки")
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    updated_at: datetime = Field(default_factory=datetime.now, description="Время обновления")
    priority: int = Field(default=1, ge=1, le=5, description="Приоритет (1-5)")
    tags: List[str] = Field(default_factory=list, description="Теги для категоризации")
    
    @field_validator('scheduled_time')
    @classmethod
    def validate_scheduled_time(cls, v):
        if v < datetime.now():
            raise ValidationError("Scheduled time cannot be in the past")
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValidationError("Too many tags")
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    def mark_sent(self):
        """Отметить как отправленное"""
        self.is_sent = True
        self.updated_at = datetime.now()
    
    def increment_attempts(self):
        """Увеличить счетчик попыток"""
        self.attempts += 1
        self.updated_at = datetime.now()
        if self.attempts >= 5:
            self.is_sent = True  # Помечаем как отправленное после 5 попыток


class ConversationMetrics(BaseModel):
    """Метрики разговора с пользователем"""
    
    total_messages: int = Field(default=0, ge=0, description="Общее количество сообщений")
    user_messages: int = Field(default=0, ge=0, description="Сообщений от пользователя")
    bot_messages: int = Field(default=0, ge=0, description="Сообщений от бота")
    average_response_time: float = Field(default=0.0, ge=0.0, description="Среднее время ответа")
    last_interaction: Optional[datetime] = Field(default=None, description="Последнее взаимодействие")
    engagement_score: float = Field(default=0.0, ge=0.0, le=10.0, description="Оценка вовлеченности")
    conversion_events: List[str] = Field(default_factory=list, description="События конверсии")
    
    def update_message_count(self, is_user_message: bool):
        """Обновление счетчиков сообщений"""
        self.total_messages += 1
        if is_user_message:
            self.user_messages += 1
        else:
            self.bot_messages += 1
        self.last_interaction = datetime.now()
    
    def calculate_engagement_score(self) -> float:
        """Расчет оценки вовлеченности"""
        if self.total_messages == 0:
            return 0.0
        
        # Базовая формула на основе активности
        base_score = min(self.total_messages / 10, 5.0)  # Максимум 5 баллов за количество
        
        # Бонус за взаимодействие
        if self.user_messages > 0:
            interaction_ratio = self.user_messages / self.total_messages
            base_score += interaction_ratio * 3.0  # Максимум 3 балла за взаимодействие
        
        # Бонус за недавнюю активность
        if self.last_interaction:
            hours_since = (datetime.now() - self.last_interaction).total_seconds() / 3600
            if hours_since < 24:
                base_score += 2.0  # 2 балла за активность в последние 24 часа
        
        self.engagement_score = min(base_score, 10.0)
        return self.engagement_score


class UserState(BaseModel):
    """Улучшенное состояние пользователя"""
    
    # Основная информация
    user_id: int = Field(..., gt=0, description="ID пользователя")
    username: Optional[str] = Field(None, description="Username пользователя")
    role: UserRole = Field(default=UserRole.USER, description="Роль пользователя")
    
    # Настройки
    model: ModelType = Field(default=ModelType.SMART, description="Тип AI модели")
    preferences: UserPreferences = Field(default_factory=UserPreferences, description="Предпочтения")
    
    # Состояния
    conversation_stage: ConversationStage = Field(
        default=ConversationStage.INITIAL,
        description="Этап разговора"
    )
    is_active: bool = Field(default=True, description="Активен ли пользователь")
    is_blocked: bool = Field(default=False, description="Заблокирован ли пользователь")
    
    # Состояния ожидания
    waiting_for_reply: bool = Field(default=False, description="Ожидает ответа")
    waiting_for_chat_name: bool = Field(default=False, description="Ожидает название чата")
    waiting_for_chat_reply: bool = Field(default=False, description="Ожидает ответ в чате")
    current_survey_step: Optional[str] = Field(default=None, description="Текущий шаг опроса")
    
    # История и метрики
    message_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="История сообщений"
    )
    conversation_metrics: ConversationMetrics = Field(
        default_factory=ConversationMetrics,
        description="Метрики разговора"
    )
    
    # PPV напоминания
    ppv_reminders: List[PPVReminder] = Field(
        default_factory=list,
        description="PPV напоминания"
    )
    
    # Чат менеджер (будет сериализован отдельно)
    chat_manager_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Данные чат менеджера"
    )
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    last_activity: datetime = Field(default_factory=datetime.now, description="Последняя активность")
    updated_at: datetime = Field(default_factory=datetime.now, description="Время обновления")
    version: int = Field(default=1, description="Версия записи")
    
    @field_validator('message_history')
    @classmethod
    def validate_message_history(cls, v):
        # Ограничиваем размер истории
        max_history = 100
        if len(v) > max_history:
            return v[-max_history:]
        return v
    
    @field_validator('ppv_reminders')
    @classmethod
    def validate_ppv_reminders(cls, v):
        # Ограничиваем количество напоминаний
        if len(v) > 50:
            raise ValidationError("Too many PPV reminders")
        return v
    
    @model_validator(mode='after')
    def validate_state_consistency(self):
        """Проверка консистентности состояния"""
        if self.is_blocked and self.is_active:
            self.is_active = False
        
        return self
    
    # Упрощенные методы логирования без сложной интеграции
    def _get_logger(self):
        """Простое получение логгера"""
        return logging.getLogger(f"UserState.{self.user_id}")
    
    def log_debug(self, message: str, **kwargs):
        """Логирование debug сообщения"""
        self._get_logger().debug(message, extra=kwargs)
    
    def log_info(self, message: str, **kwargs):
        """Логирование info сообщения"""
        self._get_logger().info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Логирование warning сообщения"""
        self._get_logger().warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Логирование error сообщения"""
        self._get_logger().error(message, extra=kwargs)
    
    def log_exception(self, message: str, **kwargs):
        """Логирование исключения"""
        self._get_logger().exception(message, extra=kwargs)
    
    def update_activity(self):
        """Обновление времени последней активности"""
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
        self.conversation_metrics.last_interaction = datetime.now()
    
    def add_message_to_history(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Добавление сообщения в историю"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.message_history.append(message)
        self.conversation_metrics.update_message_count(role == "user")
        self.update_activity()
        
        # Ограничиваем размер истории
        max_history = 100
        if len(self.message_history) > max_history:
            self.message_history = self.message_history[-max_history:]
    
    def clear_waiting_states(self):
        """Очистка всех состояний ожидания"""
        self.waiting_for_reply = False
        self.waiting_for_chat_name = False
        self.waiting_for_chat_reply = False
        self.current_survey_step = None
        self.update_activity()
    
    def block_user(self, reason: str = ""):
        """Блокировка пользователя"""
        self.is_blocked = True
        self.is_active = False
        self.conversation_stage = ConversationStage.BLOCKED
        self.clear_waiting_states()
        self.update_activity()
        
        self.log_warning(f"User blocked", user_id=self.user_id, reason=reason)
    
    def unblock_user(self):
        """Разблокировка пользователя"""
        self.is_blocked = False
        self.is_active = True
        if self.conversation_stage == ConversationStage.BLOCKED:
            self.conversation_stage = ConversationStage.INITIAL
        self.update_activity()
        
        self.log_info(f"User unblocked", user_id=self.user_id)
    
    def add_ppv_reminder(self, message: str, scheduled_time: datetime, priority: int = 1, tags: List[str] = None):
        """Добавление PPV напоминания"""
        reminder = PPVReminder(
            user_id=self.user_id,
            message=message,
            scheduled_time=scheduled_time,
            priority=priority,
            tags=tags or []
        )
        self.ppv_reminders.append(reminder)
        self.update_activity()
        return reminder
    
    def get_active_reminders(self) -> List[PPVReminder]:
        """Получение активных напоминаний"""
        return [r for r in self.ppv_reminders if not r.is_sent and r.scheduled_time <= datetime.now()]
    
    def cleanup_old_reminders(self, days: int = 30):
        """Очистка старых напоминаний"""
        cutoff = datetime.now() - timedelta(days=days)
        initial_count = len(self.ppv_reminders)
        
        self.ppv_reminders = [
            r for r in self.ppv_reminders
            if not r.is_sent or r.updated_at > cutoff
        ]
        
        cleaned_count = initial_count - len(self.ppv_reminders)
        if cleaned_count > 0:
            self.log_info(f"Cleaned {cleaned_count} old reminders", user_id=self.user_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        try:
            data = self.model_dump()
            
            # Специальная обработка для datetime
            for field in ['created_at', 'last_activity', 'updated_at']:
                if field in data and data[field]:
                    if isinstance(data[field], datetime):
                        data[field] = data[field].isoformat()
            
            # Обработка вложенных объектов
            if 'conversation_metrics' in data and 'last_interaction' in data['conversation_metrics']:
                if data['conversation_metrics']['last_interaction']:
                    if isinstance(data['conversation_metrics']['last_interaction'], datetime):
                        data['conversation_metrics']['last_interaction'] = data['conversation_metrics']['last_interaction'].isoformat()
            
            return data
        except Exception as e:
            raise SerializationError(f"Failed to serialize UserState: {str(e)}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserState':
        """Десериализация из словаря"""
        try:
            # Обработка datetime полей
            for field in ['created_at', 'last_activity', 'updated_at']:
                if field in data and isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
            
            # Обработка conversation_metrics
            if 'conversation_metrics' in data:
                metrics_data = data['conversation_metrics']
                if 'last_interaction' in metrics_data and isinstance(metrics_data['last_interaction'], str):
                    metrics_data['last_interaction'] = datetime.fromisoformat(metrics_data['last_interaction'])
            
            return cls(**data)
        except Exception as e:
            raise SerializationError(f"Failed to deserialize UserState: {str(e)}")
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True  # Разрешаем произвольные типы для logger
    ) 