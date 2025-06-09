"""
Система обработки ошибок для OF Assistant Bot
Содержит кастомные исключения и утилиты для обработки ошибок
"""

import asyncio
from typing import Optional, Dict, Any, Type, Callable
import traceback
from datetime import datetime

# === БАЗОВЫЕ КАСТОМНЫЕ ИСКЛЮЧЕНИЯ ===

class BotError(Exception):
    """Базовое исключение для всех ошибок бота"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация ошибки в словарь"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class GroqApiError(BotError):
    """Ошибки при работе с Groq API"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, api_response: Optional[str] = None):
        details = {}
        if status_code:
            details['status_code'] = status_code
        if api_response:
            details['api_response'] = api_response
        
        super().__init__(message, details)
        self.status_code = status_code
        self.api_response = api_response


class InvalidUserInputError(BotError):
    """Ошибки валидации пользовательского ввода"""
    
    def __init__(self, message: str, user_input: Optional[str] = None, validation_rule: Optional[str] = None):
        details = {}
        if user_input:
            details['user_input'] = user_input
        if validation_rule:
            details['validation_rule'] = validation_rule
        
        super().__init__(message, details)
        self.user_input = user_input
        self.validation_rule = validation_rule


class TelegramApiError(BotError):
    """Ошибки при работе с Telegram API"""
    
    def __init__(self, message: str, method: Optional[str] = None, parameters: Optional[Dict] = None):
        details = {}
        if method:
            details['telegram_method'] = method
        if parameters:
            details['parameters'] = parameters
        
        super().__init__(message, details)
        self.method = method
        self.parameters = parameters


class ConfigurationError(BotError):
    """Ошибки конфигурации бота"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, expected_value: Optional[str] = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        if expected_value:
            details['expected_value'] = expected_value
        
        super().__init__(message, details)
        self.config_key = config_key
        self.expected_value = expected_value


class CacheError(BotError):
    """Ошибки при работе с кэшем"""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if cache_key:
            details['cache_key'] = cache_key
        if operation:
            details['operation'] = operation
        
        super().__init__(message, details)
        self.cache_key = cache_key
        self.operation = operation


class StateManagerError(BotError):
    """Ошибки при работе с StateManager"""
    
    def __init__(self, message: str, user_id: Optional[int] = None, key: Optional[str] = None):
        details = {}
        if user_id:
            details['user_id'] = user_id
        if key:
            details['key'] = key
        
        super().__init__(message, details)
        self.user_id = user_id
        self.key = key


# === УТИЛИТЫ ДЛЯ ОБРАБОТКИ ОШИБОК ===

class ErrorHandler:
    """Класс для централизованной обработки ошибок"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Универсальная обработка ошибок"""
        context = context or {}
        
        # Определяем тип ошибки и сообщение для пользователя
        if isinstance(error, GroqApiError):
            user_message = "Извините, сервис AI временно недоступен. Попробуйте позже."
            log_level = "error"
        elif isinstance(error, InvalidUserInputError):
            user_message = f"Некорректный ввод: {error.message}"
            log_level = "warning"
        elif isinstance(error, TelegramApiError):
            user_message = "Произошла ошибка при отправке сообщения. Попробуйте еще раз."
            log_level = "error"
        elif isinstance(error, ConfigurationError):
            user_message = "Бот временно недоступен из-за ошибки конфигурации."
            log_level = "critical"
        elif isinstance(error, (CacheError, StateManagerError)):
            user_message = "Произошла внутренняя ошибка. Попробуйте позже."
            log_level = "error"
        else:
            user_message = "Произошла неожиданная ошибка. Наша команда уже работает над решением."
            log_level = "error"
        
        # Формируем детали для логирования
        log_details = {
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context
        }
        
        # Если это кастомная ошибка, добавляем её детали
        if isinstance(error, BotError):
            log_details.update(error.to_dict())
        
        # Логируем ошибку
        if self.logger:
            if log_level == "critical":
                self.logger.log_error(f"CRITICAL ERROR: {error}", extra_data=log_details)
            elif log_level == "error":
                self.logger.log_error(f"ERROR: {error}", extra_data=log_details)
            elif log_level == "warning":
                self.logger.log_warning(f"WARNING: {error}", extra_data=log_details)
        
        return {
            'user_message': user_message,
            'log_level': log_level,
            'log_details': log_details,
            'should_retry': log_level != "critical"
        }


# === ДЕКОРАТОРЫ ДЛЯ ОБРАБОТКИ ОШИБОК ===

def handle_bot_errors(logger=None, default_message: str = "Произошла ошибка. Попробуйте позже."):
    """Декоратор для автоматической обработки ошибок в методах бота"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler = ErrorHandler(logger)
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],  # Ограничиваем длину для безопасности
                    'kwargs': str(kwargs)[:200]
                }
                
                result = error_handler.handle_error(e, context)
                
                # Возвращаем результат для обработки в коде
                return {
                    'success': False,
                    'error': e,
                    'user_message': result['user_message'],
                    'should_retry': result['should_retry']
                }
        
        return wrapper
    return decorator


# === ВАЛИДАТОРЫ ДЛЯ ПРЕДОТВРАЩЕНИЯ ОШИБОК ===

class InputValidator:
    """Валидаторы для пользовательского ввода"""
    
    @staticmethod
    def validate_message_length(text: str, max_length: int = 1000) -> None:
        """Валидация длины сообщения"""
        if not text or not text.strip():
            raise InvalidUserInputError(
                "Сообщение не может быть пустым",
                user_input=text,
                validation_rule=f"message_not_empty"
            )
        
        if len(text) > max_length:
            raise InvalidUserInputError(
                f"Сообщение слишком длинное (максимум {max_length} символов)",
                user_input=text[:100] + "..." if len(text) > 100 else text,
                validation_rule=f"max_length_{max_length}"
            )
    
    @staticmethod
    def validate_user_id(user_id: Any) -> int:
        """Валидация user_id"""
        if not user_id:
            raise InvalidUserInputError("User ID не может быть пустым")
        
        try:
            user_id_int = int(user_id)
            if user_id_int <= 0:
                raise InvalidUserInputError("User ID должен быть положительным числом")
            return user_id_int
        except (ValueError, TypeError):
            raise InvalidUserInputError(
                "User ID должен быть числом",
                user_input=str(user_id),
                validation_rule="user_id_numeric"
            )
    
    @staticmethod
    def validate_style(style: str) -> str:
        """Валидация стиля ответа"""
        valid_styles = ['friendly', 'flirty', 'passionate', 'romantic', 'professional']
        
        if not style:
            raise InvalidUserInputError("Стиль не может быть пустым")
        
        if style not in valid_styles:
            raise InvalidUserInputError(
                f"Недопустимый стиль. Доступные: {', '.join(valid_styles)}",
                user_input=style,
                validation_rule="valid_style_enum"
            )
        
        return style


# === УТИЛИТЫ ДЛЯ БЕЗОПАСНОГО ВЫПОЛНЕНИЯ ===

async def safe_execute(func, *args, logger=None, context=None, **kwargs):
    """Безопасное выполнение функции с обработкой ошибок"""
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    except Exception as e:
        error_handler = ErrorHandler(logger)
        result = error_handler.handle_error(e, context)
        return {
            'success': False,
            'error': e,
            'user_message': result['user_message']
        }


# === ЭКСПОРТ ОСНОВНЫХ КЛАССОВ ===

__all__ = [
    'BotError',
    'GroqApiError', 
    'InvalidUserInputError',
    'TelegramApiError',
    'ConfigurationError',
    'CacheError',
    'StateManagerError',
    'ErrorHandler',
    'InputValidator',
    'handle_bot_errors',
    'safe_execute'
] 