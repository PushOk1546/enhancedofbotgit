"""
Конфигурация системы логирования для OF Assistant Bot.
Обеспечивает структурированное логирование с ротацией файлов и фильтрацией чувствительных данных.
"""

import logging
import logging.handlers
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class SensitiveDataFilter(logging.Filter):
    """Фильтр для удаления чувствительных данных из логов"""
    
    def __init__(self):
        super().__init__()
        # Паттерны для поиска чувствительных данных
        self.sensitive_patterns = [
            (re.compile(r'BOT_TOKEN["\s]*[:=]["\s]*([A-Za-z0-9_-]+)', re.IGNORECASE), 'BOT_TOKEN=***'),
            (re.compile(r'GROQ_KEY["\s]*[:=]["\s]*([A-Za-z0-9_-]+)', re.IGNORECASE), 'GROQ_KEY=***'),
            (re.compile(r'password["\s]*[:=]["\s]*([^\s"]+)', re.IGNORECASE), 'password=***'),
            (re.compile(r'token["\s]*[:=]["\s]*([A-Za-z0-9_-]{20,})', re.IGNORECASE), 'token=***'),
            (re.compile(r'api_key["\s]*[:=]["\s]*([A-Za-z0-9_-]+)', re.IGNORECASE), 'api_key=***'),
            # Обобщенный паттерн для банковских карт
            (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '****-****-****-****'),
            # Email (частично скрываем)
            (re.compile(r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'), r'\g<1>***@\g<2>'),
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Фильтрация чувствительных данных из записи лога"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for pattern, replacement in self.sensitive_patterns:
                record.msg = pattern.sub(replacement, record.msg)
        
        # Также обрабатываем аргументы
        if hasattr(record, 'args') and record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.sensitive_patterns:
                        arg = pattern.sub(replacement, arg)
                new_args.append(arg)
            record.args = tuple(new_args)
        
        return True


class StructuredFormatter(logging.Formatter):
    """Форматировщик для создания структурированных JSON логов"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирование записи в JSON"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Добавляем информацию об исключении если есть
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Добавляем дополнительные поля
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                              'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process', 'getMessage']:
                    log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class UserActivityFormatter(logging.Formatter):
    """Специальный форматировщик для логов активности пользователей"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирование записи активности пользователя"""
        if hasattr(record, 'user_id') and hasattr(record, 'action'):
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'user_id': record.user_id,
                'action': record.action,
                'message': record.getMessage(),
            }
            
            # Добавляем дополнительную информацию если есть
            for attr in ['chat_id', 'message_type', 'response_time', 'error']:
                if hasattr(record, attr):
                    log_entry[attr] = getattr(record, attr)
            
            return json.dumps(log_entry, ensure_ascii=False, default=str)
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True
) -> None:
    """
    Настройка системы логирования.
    
    Args:
        log_level: Уровень логирования
        log_dir: Директория для файлов логов
        max_file_size: Максимальный размер файла лога
        backup_count: Количество backup файлов
        enable_console: Включить вывод в консоль
        enable_file: Включить запись в файл
        enable_json: Включить JSON форматирование
    """
    # Создаем директорию для логов
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Основной логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие хендлеры
    root_logger.handlers.clear()
    
    # Создаем фильтр для чувствительных данных
    sensitive_filter = SensitiveDataFilter()
    
    # Консольный хендлер
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        if enable_json:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
        
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)
    
    # Файловый хендлер для общих логов
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / "bot.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        if enable_json:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
        
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)
    
    # Отдельный хендлер для ошибок
    if enable_file:
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "errors.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        error_handler.addFilter(sensitive_filter)
        root_logger.addHandler(error_handler)
    
    # Хендлер для активности пользователей
    if enable_file:
        activity_handler = logging.handlers.RotatingFileHandler(
            log_path / "user_activity.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        activity_handler.setLevel(logging.INFO)
        activity_handler.setFormatter(UserActivityFormatter())
        activity_handler.addFilter(sensitive_filter)
        
        # Создаем отдельный логгер для активности
        activity_logger = logging.getLogger('user_activity')
        activity_logger.addHandler(activity_handler)
        activity_logger.setLevel(logging.INFO)
        activity_logger.propagate = False
    
    # Настройка логгеров для внешних библиотек
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('telebot').setLevel(logging.WARNING)
    logging.getLogger('groq').setLevel(logging.WARNING)
    
    # Логирование старта системы
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized", extra={
        'log_level': log_level,
        'log_dir': str(log_path),
        'json_enabled': enable_json,
        'console_enabled': enable_console,
        'file_enabled': enable_file
    })


def get_logger(name: str) -> logging.Logger:
    """Получение логгера с заданным именем"""
    return logging.getLogger(name)


def log_user_activity(
    user_id: int,
    action: str,
    message: str,
    **kwargs
) -> None:
    """
    Логирование активности пользователя.
    
    Args:
        user_id: ID пользователя
        action: Тип действия
        message: Описание действия
        **kwargs: Дополнительные параметры
    """
    logger = logging.getLogger('user_activity')
    logger.info(message, extra={
        'user_id': user_id,
        'action': action,
        **kwargs
    })


def log_api_call(
    service: str,
    endpoint: str,
    user_id: Optional[int] = None,
    response_time: Optional[float] = None,
    status_code: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """
    Логирование вызовов внешних API.
    
    Args:
        service: Название сервиса
        endpoint: Конечная точка API
        user_id: ID пользователя (если применимо)
        response_time: Время ответа в секундах
        status_code: HTTP статус код
        error: Описание ошибки (если есть)
    """
    logger = logging.getLogger('api_calls')
    
    extra = {
        'service': service,
        'endpoint': endpoint,
        'response_time': response_time,
        'status_code': status_code
    }
    
    if user_id:
        extra['user_id'] = user_id
    
    if error:
        logger.error(f"API call failed: {service} {endpoint} - {error}", extra=extra)
    else:
        logger.info(f"API call: {service} {endpoint}", extra=extra)


class LoggingMixin:
    """Mixin для добавления логирования в классы"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_debug(self, message: str, **kwargs):
        """Логирование debug сообщения"""
        self.logger.debug(message, extra=kwargs)
    
    def log_info(self, message: str, **kwargs):
        """Логирование info сообщения"""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Логирование warning сообщения"""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Логирование error сообщения"""
        self.logger.error(message, extra=kwargs)
    
    def log_exception(self, message: str, **kwargs):
        """Логирование исключения"""
        self.logger.exception(message, extra=kwargs) 