"""
Система обработки ошибок для OF Assistant Bot.
Обеспечивает централизованную обработку, логирование и восстановление после ошибок.
"""

import functools
import traceback
import asyncio
import sys
from typing import Callable, Optional, Dict, Any, Type, Union, List
from datetime import datetime, timedelta
import logging
from enum import Enum

from .exceptions import (
    BotException, ValidationError, StateManagerError, ChatManagerError,
    APIError, GroqAPIError, TelegramAPIError, RateLimitError,
    ConfigurationError, DatabaseError, CacheError, SerializationError
)
from .logging_config import get_logger, log_user_activity
from .async_helpers import retry_async


class ErrorSeverity(str, Enum):
    """Уровни серьезности ошибок"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Категории ошибок"""
    VALIDATION = "validation"
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class ErrorContext:
    """Контекст ошибки для дополнительной информации"""
    
    def __init__(self):
        self.user_id: Optional[int] = None
        self.chat_id: Optional[int] = None
        self.message_id: Optional[int] = None
        self.operation: Optional[str] = None
        self.request_id: Optional[str] = None
        self.additional_data: Dict[str, Any] = {}
    
    def set_user_context(self, user_id: int, chat_id: Optional[int] = None, message_id: Optional[int] = None):
        """Установка пользовательского контекста"""
        self.user_id = user_id
        self.chat_id = chat_id
        self.message_id = message_id
    
    def set_operation(self, operation: str):
        """Установка текущей операции"""
        self.operation = operation
    
    def add_data(self, key: str, value: Any):
        """Добавление дополнительных данных"""
        self.additional_data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'operation': self.operation,
            'request_id': self.request_id,
            'additional_data': self.additional_data
        }


class ErrorHandler:
    """Основной класс для обработки ошибок"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._error_stats: Dict[str, int] = {}
        self._last_errors: List[Dict[str, Any]] = []
        self._max_error_history = 100
        
        # Маппинг исключений на категории и серьезность
        self._exception_mapping = {
            ValidationError: (ErrorCategory.VALIDATION, ErrorSeverity.LOW),
            StateManagerError: (ErrorCategory.DATABASE, ErrorSeverity.MEDIUM),
            ChatManagerError: (ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.MEDIUM),
            GroqAPIError: (ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH),
            TelegramAPIError: (ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH),
            RateLimitError: (ErrorCategory.API, ErrorSeverity.MEDIUM),
            ConfigurationError: (ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
            DatabaseError: (ErrorCategory.DATABASE, ErrorSeverity.HIGH),
            CacheError: (ErrorCategory.CACHE, ErrorSeverity.LOW),
            SerializationError: (ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM),
            ConnectionError: (ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH),
            TimeoutError: (ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.MEDIUM),
            KeyError: (ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM),
            ValueError: (ErrorCategory.VALIDATION, ErrorSeverity.LOW),
            TypeError: (ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM),
        }
    
    def _classify_error(self, exception: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Классификация ошибки по типу"""
        exc_type = type(exception)
        
        # Прямое соответствие
        if exc_type in self._exception_mapping:
            return self._exception_mapping[exc_type]
        
        # Проверяем иерархию классов
        for exc_class, (category, severity) in self._exception_mapping.items():
            if isinstance(exception, exc_class):
                return category, severity
        
        # По умолчанию
        return ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM
    
    def _record_error(self, exception: Exception, context: Optional[ErrorContext] = None):
        """Запись ошибки в статистику"""
        exc_name = type(exception).__name__
        self._error_stats[exc_name] = self._error_stats.get(exc_name, 0) + 1
        
        category, severity = self._classify_error(exception)
        
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'exception_type': exc_name,
            'message': str(exception),
            'category': category.value,
            'severity': severity.value,
            'traceback': traceback.format_exc(),
            'context': context.to_dict() if context else {}
        }
        
        self._last_errors.append(error_record)
        if len(self._last_errors) > self._max_error_history:
            self._last_errors = self._last_errors[-self._max_error_history:]
    
    def handle_error(
        self,
        exception: Exception,
        context: Optional[ErrorContext] = None,
        user_message: Optional[str] = None,
        should_raise: bool = False
    ) -> Dict[str, Any]:
        """
        Обработка ошибки.
        
        Args:
            exception: Исключение для обработки
            context: Контекст ошибки
            user_message: Сообщение для пользователя
            should_raise: Поднимать ли исключение после обработки
            
        Returns:
            Словарь с результатом обработки
        """
        category, severity = self._classify_error(exception)
        self._record_error(exception, context)
        
        # Логирование
        log_method = {
            ErrorSeverity.LOW: self.logger.info,
            ErrorSeverity.MEDIUM: self.logger.warning,
            ErrorSeverity.HIGH: self.logger.error,
            ErrorSeverity.CRITICAL: self.logger.critical
        }.get(severity, self.logger.error)
        
        extra_data = {
            'category': category.value,
            'severity': severity.value,
            'exception_type': type(exception).__name__
        }
        
        if context:
            extra_data.update(context.to_dict())
        
        log_method(f"Error handled: {str(exception)}", extra=extra_data)
        
        # Логирование активности пользователя при наличии контекста
        if context and context.user_id:
            log_user_activity(
                user_id=context.user_id,
                action="error_occurred",
                message=f"Error in {context.operation}: {type(exception).__name__}",
                error_type=type(exception).__name__,
                error_category=category.value,
                error_severity=severity.value
            )
        
        # Определение действий по восстановлению
        recovery_actions = self._get_recovery_actions(exception, severity)
        
        result = {
            'handled': True,
            'severity': severity.value,
            'category': category.value,
            'user_message': user_message or self._get_user_message(exception, severity),
            'recovery_actions': recovery_actions,
            'should_retry': self._should_retry(exception),
            'timestamp': datetime.now().isoformat()
        }
        
        # Уведомление для критических ошибок
        if severity == ErrorSeverity.CRITICAL:
            self._notify_critical_error(exception, context)
        
        if should_raise:
            raise exception
        
        return result
    
    def _get_recovery_actions(self, exception: Exception, severity: ErrorSeverity) -> List[str]:
        """Получение действий по восстановлению"""
        actions = []
        
        if isinstance(exception, ValidationError):
            actions.append("validate_input")
        elif isinstance(exception, RateLimitError):
            actions.append("wait_and_retry")
        elif isinstance(exception, (GroqAPIError, TelegramAPIError)):
            actions.append("retry_with_exponential_backoff")
            if severity == ErrorSeverity.HIGH:
                actions.append("switch_to_fallback_service")
        elif isinstance(exception, DatabaseError):
            actions.append("retry_database_operation")
            actions.append("check_database_connection")
        elif isinstance(exception, CacheError):
            actions.append("clear_cache")
            actions.append("continue_without_cache")
        
        return actions
    
    def _should_retry(self, exception: Exception) -> bool:
        """Определение необходимости повторной попытки"""
        retry_exceptions = (
            GroqAPIError,
            TelegramAPIError,
            DatabaseError,
            ConnectionError,
            TimeoutError
        )
        return isinstance(exception, retry_exceptions)
    
    def _get_user_message(self, exception: Exception, severity: ErrorSeverity) -> str:
        """Получение сообщения для пользователя"""
        if isinstance(exception, ValidationError):
            return "Пожалуйста, проверьте введенные данные и попробуйте снова."
        elif isinstance(exception, RateLimitError):
            return "Слишком много запросов. Пожалуйста, подождите немного перед следующим запросом."
        elif isinstance(exception, (GroqAPIError, TelegramAPIError)):
            return "Временные проблемы с сервисом. Попробуйте снова через несколько минут."
        elif severity == ErrorSeverity.CRITICAL:
            return "Произошла серьезная ошибка. Мы уже работаем над ее устранением."
        else:
            return "Произошла ошибка. Пожалуйста, попробуйте снова."
    
    def _notify_critical_error(self, exception: Exception, context: Optional[ErrorContext]):
        """Уведомление о критической ошибке"""
        # Здесь можно добавить отправку уведомлений администраторам
        self.logger.critical(
            f"CRITICAL ERROR: {type(exception).__name__}: {str(exception)}",
            extra={
                'traceback': traceback.format_exc(),
                'context': context.to_dict() if context else {},
                'requires_immediate_attention': True
            }
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Получение статистики ошибок"""
        return {
            'error_counts': self._error_stats.copy(),
            'recent_errors': self._last_errors[-10:],  # Последние 10 ошибок
            'total_errors': sum(self._error_stats.values())
        }
    
    def clear_stats(self):
        """Очистка статистики ошибок"""
        self._error_stats.clear()
        self._last_errors.clear()


# Глобальный экземпляр обработчика ошибок
error_handler = ErrorHandler()


def handle_errors(
    user_message: Optional[str] = None,
    should_raise: bool = False,
    context_operation: Optional[str] = None
):
    """
    Декоратор для автоматической обработки ошибок.
    
    Args:
        user_message: Сообщение для пользователя при ошибке
        should_raise: Поднимать ли исключение после обработки
        context_operation: Название операции для контекста
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                context = ErrorContext()
                if context_operation:
                    context.set_operation(context_operation)
                
                # Попытка извлечь user_id из аргументов
                try:
                    if args and hasattr(args[0], 'user_id'):
                        context.set_user_context(args[0].user_id)
                    elif 'user_id' in kwargs:
                        context.set_user_context(kwargs['user_id'])
                    elif args and isinstance(args[0], int) and args[0] > 0:
                        context.set_user_context(args[0])
                except:
                    pass
                
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    result = error_handler.handle_error(
                        e, context, user_message, should_raise
                    )
                    if not should_raise:
                        return result
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                context = ErrorContext()
                if context_operation:
                    context.set_operation(context_operation)
                
                # Попытка извлечь user_id из аргументов
                try:
                    if args and hasattr(args[0], 'user_id'):
                        context.set_user_context(args[0].user_id)
                    elif 'user_id' in kwargs:
                        context.set_user_context(kwargs['user_id'])
                    elif args and isinstance(args[0], int) and args[0] > 0:
                        context.set_user_context(args[0])
                except:
                    pass
                
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    result = error_handler.handle_error(
                        e, context, user_message, should_raise
                    )
                    if not should_raise:
                        return result
            
            return sync_wrapper
    
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return=None,
    operation_name: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Безопасное выполнение функции с обработкой ошибок.
    
    Args:
        func: Функция для выполнения
        *args: Аргументы функции
        default_return: Значение по умолчанию при ошибке
        operation_name: Название операции
        **kwargs: Keyword аргументы функции
        
    Returns:
        Результат выполнения функции или default_return при ошибке
    """
    context = ErrorContext()
    if operation_name:
        context.set_operation(operation_name)
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, context)
        return default_return


async def safe_execute_async(
    func: Callable,
    *args,
    default_return=None,
    operation_name: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Безопасное выполнение асинхронной функции с обработкой ошибок.
    
    Args:
        func: Асинхронная функция для выполнения
        *args: Аргументы функции
        default_return: Значение по умолчанию при ошибке
        operation_name: Название операции
        **kwargs: Keyword аргументы функции
        
    Returns:
        Результат выполнения функции или default_return при ошибке
    """
    context = ErrorContext()
    if operation_name:
        context.set_operation(operation_name)
    
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, context)
        return default_return


class ErrorRecovery:
    """Класс для восстановления после ошибок"""
    
    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        *args,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        **kwargs
    ):
        """Повторные попытки с экспоненциальной задержкой"""
        delay = base_delay
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == max_attempts - 1:
                    break
                
                await asyncio.sleep(min(delay, max_delay))
                delay *= 2
        
        if last_exception:
            raise last_exception
    
    @staticmethod
    def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
        """Circuit breaker паттерн для предотвращения каскадных отказов"""
        def decorator(func: Callable) -> Callable:
            failure_count = 0
            last_failure_time = None
            is_open = False
            
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                nonlocal failure_count, last_failure_time, is_open
                
                # Проверяем состояние circuit breaker
                if is_open:
                    if (datetime.now() - last_failure_time).seconds < recovery_timeout:
                        raise Exception("Circuit breaker is open")
                    else:
                        # Пробуем восстановиться
                        is_open = False
                        failure_count = 0
                
                try:
                    result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                    failure_count = 0  # Сброс при успехе
                    return result
                except Exception as e:
                    failure_count += 1
                    last_failure_time = datetime.now()
                    
                    if failure_count >= failure_threshold:
                        is_open = True
                    
                    raise e
            
            return wrapper
        return decorator 