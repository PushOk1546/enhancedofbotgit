"""
Система исключений для OF Assistant Bot.
Определяет иерархию исключений для различных компонентов системы.
"""

from typing import Optional, Dict, Any


class BotException(Exception):
    """Базовое исключение бота"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}. Details: {self.details}"
        return self.message


class ValidationError(BotException):
    """Ошибка валидации входных данных"""
    pass


class StateManagerError(BotException):
    """Ошибка менеджера состояний"""
    pass


class ChatManagerError(BotException):
    """Ошибка менеджера чатов"""
    pass


class APIError(BotException):
    """Ошибка внешнего API"""
    
    def __init__(self, message: str, service: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.service = service
        self.status_code = status_code
        super().__init__(message, details)


class GroqAPIError(APIError):
    """Ошибка Groq API"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "groq", status_code, details)


class TelegramAPIError(APIError):
    """Ошибка Telegram API"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "telegram", status_code, details)


class RateLimitError(BotException):
    """Ошибка превышения лимита запросов"""
    
    def __init__(self, user_id: int, limit: int, window: int):
        self.user_id = user_id
        self.limit = limit
        self.window = window
        message = f"Rate limit exceeded for user {user_id}: {limit} requests per {window} seconds"
        super().__init__(message)


class ConfigurationError(BotException):
    """Ошибка конфигурации"""
    pass


class DatabaseError(BotException):
    """Ошибка базы данных"""
    pass


class CacheError(BotException):
    """Ошибка кеша"""
    pass


class SerializationError(BotException):
    """Ошибка сериализации/десериализации"""
    pass 