"""
Модели данных для OF Assistant Bot.
Содержит классы для управления состоянием пользователей и напоминаниями.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


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


@dataclass
class PPVReminder:
    """Напоминание о PPV контенте"""
    user_id: int
    message: str
    scheduled_time: datetime
    is_sent: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "message": self.message,
            "scheduled_time": self.scheduled_time.isoformat(),
            "is_sent": self.is_sent,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data["user_id"],
            message=data["message"],
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            is_sent=data.get("is_sent", False),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )


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
    
    def to_dict(self):
        # Сериализация chat_manager
        chat_manager_data = None
        if self.chat_manager:
            chat_manager_data = self.chat_manager.to_dict()
        
        return {
            "model": self.model,
            "preferences": {
                "content_types": self.preferences.content_types,
                "price_range": self.preferences.price_range,
                "communication_style": self.preferences.communication_style,
                "notification_frequency": self.preferences.notification_frequency,
                "completed_survey": self.preferences.completed_survey
            },
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
    
    @classmethod
    def from_dict(cls, data):
        preferences_data = data.get("preferences", {})
        preferences = UserPreferences(
            content_types=preferences_data.get("content_types", ["photos", "videos", "messages"]),
            price_range=preferences_data.get("price_range", "medium"),
            communication_style=preferences_data.get("communication_style", "friendly"),
            notification_frequency=preferences_data.get("notification_frequency", "normal"),
            completed_survey=preferences_data.get("completed_survey", False)
        )
        
        ppv_reminders = [
            PPVReminder.from_dict(reminder_data) 
            for reminder_data in data.get("ppv_reminders", [])
        ]
        
        # Десериализация chat_manager
        chat_manager = None
        if data.get("chat_manager"):
            from chat_models import ChatManager
            chat_manager = ChatManager.from_dict(data["chat_manager"])
        
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
    
    def update_activity(self):
        """Обновление времени последней активности"""
        self.last_activity = datetime.now()
    
    def add_message_to_history(self, role, content):
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
    
    def clear_waiting_states(self):
        """Очистка всех состояний ожидания"""
        self.waiting_for_reply = False
        self.waiting_for_chat_name = False
        self.waiting_for_chat_reply = False
        self.current_survey_step = None 