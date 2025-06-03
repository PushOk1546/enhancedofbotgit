"""
Система валидации входных данных на основе Pydantic.
Обеспечивает типобезопасность и валидацию всех входящих данных.
"""

from typing import Optional, Dict, Any, List, Literal, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

from .exceptions import ValidationError


class UserRole(str, Enum):
    """Роли пользователей"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class ContentType(str, Enum):
    """Типы контента"""
    PHOTO = "photo"
    VIDEO = "video"
    VOICE = "voice"
    TEXT = "text"
    DOCUMENT = "document"
    STICKER = "sticker"


class MessageType(str, Enum):
    """Типы сообщений"""
    TEXT = "text"
    COMMAND = "command"
    CALLBACK = "callback"
    INLINE = "inline"


class ValidatedUser(BaseModel):
    """Валидированная модель пользователя"""
    user_id: int = Field(..., gt=0, description="ID пользователя Telegram")
    username: Optional[str] = Field(None, min_length=1, max_length=32, description="Username пользователя")
    first_name: Optional[str] = Field(None, min_length=1, max_length=64, description="Имя пользователя")
    last_name: Optional[str] = Field(None, min_length=1, max_length=64, description="Фамилия пользователя")
    language_code: Optional[str] = Field(None, min_length=2, max_length=5, description="Код языка")
    role: UserRole = Field(default=UserRole.USER, description="Роль пользователя")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValidationError(f"Invalid user_id: {v}. Must be positive integer")
        if v > 2**63 - 1:  # Максимальное значение для int64
            raise ValidationError(f"Invalid user_id: {v}. Too large")
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if not v.replace('_', '').isalnum():
                raise ValidationError(f"Invalid username: {v}. Must contain only alphanumeric characters and underscores")
        return v


class ValidatedMessage(BaseModel):
    """Валидированная модель сообщения"""
    message_id: int = Field(..., gt=0, description="ID сообщения")
    text: Optional[str] = Field(None, max_length=4096, description="Текст сообщения")
    content_type: ContentType = Field(default=ContentType.TEXT, description="Тип контента")
    user: ValidatedUser = Field(..., description="Пользователь отправитель")
    chat_id: int = Field(..., description="ID чата")
    date: datetime = Field(default_factory=datetime.now, description="Время отправки")
    reply_to_message_id: Optional[int] = None
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if v is not None:
            # Проверка на потенциально опасный контент
            dangerous_patterns = ['<script', 'javascript:', 'data:']
            for pattern in dangerous_patterns:
                if pattern.lower() in v.lower():
                    raise ValidationError(f"Potentially dangerous content detected: {pattern}")
        return v
    
    @field_validator('chat_id')
    @classmethod
    def validate_chat_id(cls, v):
        # Telegram chat_id может быть как положительным (приватные чаты), так и отрицательным (группы)
        if abs(v) > 2**63 - 1:
            raise ValidationError(f"Invalid chat_id: {v}. Too large")
        return v


class ValidatedCallback(BaseModel):
    """Валидированная модель callback запроса"""
    callback_id: str = Field(..., min_length=1, max_length=64, description="ID callback запроса")
    data: str = Field(..., min_length=1, max_length=64, description="Данные callback")
    user: ValidatedUser = Field(..., description="Пользователь")
    message: Optional[ValidatedMessage] = None
    
    @field_validator('data')
    @classmethod
    def validate_callback_data(cls, v):
        # Валидация формата callback данных
        if not v.replace('_', '').replace('-', '').replace(':', '').isalnum():
            raise ValidationError(f"Invalid callback data format: {v}")
        return v


class ValidatedChatSettings(BaseModel):
    """Валидированные настройки чата"""
    chat_id: str = Field(..., min_length=1, max_length=50, description="ID чата")
    name: str = Field(..., min_length=1, max_length=100, description="Название чата")
    description: Optional[str] = Field(None, max_length=500, description="Описание чата")
    client_preferences: Dict[str, Any] = Field(default_factory=dict, description="Предпочтения клиента")
    active: bool = Field(default=True, description="Активность чата")
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValidationError("Chat name cannot be empty")
        return v.strip()
    
    @field_validator('client_preferences')
    @classmethod
    def validate_preferences(cls, v):
        # Ограничение размера preferences для предотвращения DoS
        if len(str(v)) > 10000:  # 10KB limit
            raise ValidationError("Client preferences too large")
        return v


class ValidatedAPIRequest(BaseModel):
    """Валидированный запрос к API"""
    prompt: str = Field(..., min_length=1, max_length=8000, description="Prompt для API")
    model: str = Field(default="llama3-8b-8192", description="Модель для использования")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: int = Field(default=1000, ge=1, le=8192, description="Максимальное количество токенов")
    user_id: int = Field(..., gt=0, description="ID пользователя для rate limiting")
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        # Проверка на потенциально вредоносные промпты
        harmful_patterns = [
            'ignore previous instructions',
            'forget everything',
            'system prompt',
            'developer mode',
            'admin override'
        ]
        
        v_lower = v.lower()
        for pattern in harmful_patterns:
            if pattern in v_lower:
                raise ValidationError(f"Potentially harmful prompt pattern detected: {pattern}")
        
        return v
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        allowed_models = [
            'llama3-8b-8192',
            'llama3-70b-8192',
            'mixtral-8x7b-32768',
            'gemma-7b-it',
            'whisper-large-v3'
        ]
        if v not in allowed_models:
            raise ValidationError(f"Model {v} not allowed. Allowed models: {allowed_models}")
        return v


class ValidatedUserPreferences(BaseModel):
    """Валидированные пользовательские предпочтения"""
    content_types: List[ContentType] = Field(default_factory=list, description="Предпочитаемые типы контента")
    price_range: Optional[str] = Field(None, pattern=r'^\d+-\d+$', description="Ценовой диапазон")
    communication_style: Literal["friendly", "professional", "flirty", "casual"] = Field(
        default="friendly", description="Стиль общения"
    )
    notification_frequency: Literal["high", "medium", "low"] = Field(
        default="medium", description="Частота уведомлений"
    )
    completed_survey: bool = Field(default=False, description="Завершен ли опрос")
    
    @field_validator('content_types')
    @classmethod
    def validate_content_types(cls, v):
        if len(v) > 10:  # Разумное ограничение
            raise ValidationError("Too many content types selected")
        return v


def validate_user_input(data: Dict[str, Any], validation_type: str) -> BaseModel:
    """
    Центральная функция валидации входных данных.
    
    Args:
        data: Данные для валидации
        validation_type: Тип валидации
        
    Returns:
        Валидированная модель
        
    Raises:
        ValidationError: При ошибке валидации
    """
    validators = {
        'user': ValidatedUser,
        'message': ValidatedMessage,
        'callback': ValidatedCallback,
        'chat_settings': ValidatedChatSettings,
        'api_request': ValidatedAPIRequest,
        'user_preferences': ValidatedUserPreferences
    }
    
    if validation_type not in validators:
        raise ValidationError(f"Unknown validation type: {validation_type}")
    
    try:
        validator_class = validators[validation_type]
        return validator_class(**data)
    except Exception as e:
        raise ValidationError(f"Validation failed for {validation_type}: {str(e)}")


# Декораторы для валидации

def validate_input(validation_type: str):
    """Декоратор для автоматической валидации входных данных"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Предполагаем, что первый аргумент - это данные для валидации
            if args:
                try:
                    validated_data = validate_user_input(args[0], validation_type)
                    args = (validated_data,) + args[1:]
                except ValidationError as e:
                    raise e
            return func(*args, **kwargs)
        return wrapper
    return decorator 