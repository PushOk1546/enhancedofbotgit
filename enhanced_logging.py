#!/usr/bin/env python3
"""
Расширенная система логирования для OF Assistant Bot
Использует loguru для красивого и эффективного логирования
"""

import sys
import os
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime

try:
    from loguru import logger
except ImportError:
    print("❌ Ошибка: loguru не установлен. Установите: pip install loguru")
    sys.exit(1)

try:
    from config import config
except ImportError:
    print("⚠️ Предупреждение: config.py не найден. Используются настройки по умолчанию.")
    
    class DefaultConfig:
        LOG_LEVEL = "INFO"
        DEBUG = False
        
        def get_log_config(self):
            return {
                'level': 'INFO',
                'format': '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
                'rotation': '10 MB',
                'retention': '1 week',
                'compression': 'zip'
            }
    
    config = DefaultConfig()


class BotLogger:
    """
    Класс для логирования событий бота с поддержкой ротации файлов
    и различных уровней логирования
    """
    
    def __init__(self, 
                 log_dir: str = "logs", 
                 log_file: str = "bot.log",
                 logger_name: str = "BotLogger"):
        """
        Инициализация логгера
        
        Args:
            log_dir: Директория для логов
            log_file: Имя файла лога
            logger_name: Имя логгера
        """
        self.log_dir = Path(log_dir)
        self.log_file = log_file
        self.logger_name = logger_name
        
        # Создание директории для логов
        self.log_dir.mkdir(exist_ok=True)
        
        # Удаление стандартных обработчиков loguru
        logger.remove()
        
        # Настройка логгера
        self._setup_logger()
        
        # Сохранение экземпляра loguru для прямого доступа
        self.logger = logger
        
        self.log_info(f"🚀 Логгер {logger_name} инициализирован")
        self.log_info(f"📁 Директория логов: {self.log_dir.absolute()}")
        self.log_info(f"📊 Уровень логирования: {config.LOG_LEVEL}")
    
    def _setup_logger(self):
        """Настройка логгера с консольным и файловым выводом"""
        
        # Получение конфигурации логов
        log_config = config.get_log_config()
        
        # Настройка консольного вывода
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[logger_name]}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            sys.stdout,
            format=console_format,
            level=config.LOG_LEVEL,
            colorize=True,
            filter=lambda record: record["extra"].get("logger_name") == self.logger_name
        )
        
        # Настройка файлового вывода - основной лог
        main_log_path = self.log_dir / self.log_file
        logger.add(
            str(main_log_path),
            format=log_config['format'],
            level=config.LOG_LEVEL,
            rotation=log_config['rotation'],
            retention=log_config['retention'],
            compression=log_config['compression'],
            encoding="utf-8",
            filter=lambda record: record["extra"].get("logger_name") == self.logger_name
        )
        
        # Отдельный файл для ошибок
        error_log_path = self.log_dir / "errors.log"
        logger.add(
            str(error_log_path),
            format=log_config['format'],
            level="ERROR",
            rotation="5 MB",
            retention="2 weeks",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: (
                record["level"].name == "ERROR" and 
                record["extra"].get("logger_name") == self.logger_name
            )
        )
        
        # Отдельный файл для отладки (только если включен DEBUG)
        if config.DEBUG:
            debug_log_path = self.log_dir / "debug.log"
            logger.add(
                str(debug_log_path),
                format=log_config['format'],
                level="DEBUG",
                rotation="20 MB",
                retention="3 days",
                compression="zip",
                encoding="utf-8",
                filter=lambda record: (
                    record["level"].name == "DEBUG" and 
                    record["extra"].get("logger_name") == self.logger_name
                )
            )
    
    def _log(self, level: str, message: str, **kwargs):
        """Внутренний метод для логирования с дополнительными данными"""
        logger.bind(logger_name=self.logger_name).log(level, message, **kwargs)
    
    def log_info(self, message: str, **kwargs):
        """
        Логирование информационного сообщения
        
        Args:
            message: Сообщение для логирования
            **kwargs: Дополнительные параметры
        """
        self._log("INFO", message, **kwargs)
    
    def log_error(self, message: str, exc_info: bool = False, **kwargs):
        """
        Логирование ошибки
        
        Args:
            message: Сообщение об ошибке
            exc_info: Включать ли информацию об исключении
            **kwargs: Дополнительные параметры
        """
        if exc_info:
            logger.bind(logger_name=self.logger_name).exception(message, **kwargs)
        else:
            self._log("ERROR", message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """
        Логирование предупреждения
        
        Args:
            message: Сообщение предупреждения
            **kwargs: Дополнительные параметры
        """
        self._log("WARNING", message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """
        Логирование отладочного сообщения
        
        Args:
            message: Отладочное сообщение
            **kwargs: Дополнительные параметры
        """
        self._log("DEBUG", message, **kwargs)
    
    def log_user_activity(self, user_id: int, action: str, details: Optional[Dict[str, Any]] = None):
        """
        Логирование активности пользователя
        
        Args:
            user_id: ID пользователя
            action: Действие пользователя
            details: Дополнительные детали
        """
        details_str = f" | Детали: {details}" if details else ""
        message = f"👤 Пользователь {user_id} | Действие: {action}{details_str}"
        self.log_info(message)
    
    def log_api_call(self, api_name: str, endpoint: str, status: str, response_time: Optional[float] = None):
        """
        Логирование API вызовов
        
        Args:
            api_name: Название API (например, "Groq", "Telegram")
            endpoint: Конечная точка API
            status: Статус вызова
            response_time: Время ответа в секундах
        """
        time_str = f" | Время: {response_time:.2f}с" if response_time else ""
        message = f"🌐 API {api_name} | {endpoint} | Статус: {status}{time_str}"
        
        if status.lower() in ['error', 'failed', 'timeout']:
            self.log_error(message)
        else:
            self.log_info(message)
    
    def log_bot_event(self, event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Логирование событий бота
        
        Args:
            event_type: Тип события (start, stop, restart, etc.)
            description: Описание события
            metadata: Дополнительные метаданные
        """
        meta_str = f" | Метаданные: {metadata}" if metadata else ""
        message = f"🤖 Событие: {event_type} | {description}{meta_str}"
        self.log_info(message)
    
    def log_performance(self, operation: str, duration: float, success: bool = True):
        """
        Логирование производительности операций
        
        Args:
            operation: Название операции
            duration: Длительность в секундах
            success: Успешность выполнения
        """
        status = "✅ Успешно" if success else "❌ Ошибка"
        message = f"⏱️ Операция: {operation} | {status} | Время: {duration:.3f}с"
        
        if success:
            self.log_info(message)
        else:
            self.log_warning(message)
    
    def create_context_logger(self, context: str):
        """
        Создает контекстный логгер с префиксом
        
        Args:
            context: Контекст (например, "handler:start", "api:groq")
            
        Returns:
            Контекстный логгер
        """
        return ContextLogger(self, context)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику логирования
        
        Returns:
            Словарь со статистикой
        """
        log_files = list(self.log_dir.glob("*.log"))
        
        stats = {
            "log_directory": str(self.log_dir.absolute()),
            "log_files_count": len(log_files),
            "log_files": [],
            "total_size_mb": 0
        }
        
        for log_file in log_files:
            if log_file.exists():
                size_bytes = log_file.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                stats["total_size_mb"] += size_mb
                
                stats["log_files"].append({
                    "name": log_file.name,
                    "size_mb": round(size_mb, 2),
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats


class ContextLogger:
    """Контекстный логгер для добавления префиксов к сообщениям"""
    
    def __init__(self, parent_logger: BotLogger, context: str):
        self.parent = parent_logger
        self.context = context
    
    def _format_message(self, message: str) -> str:
        return f"[{self.context}] {message}"
    
    def info(self, message: str, **kwargs):
        self.parent.log_info(self._format_message(message), **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        self.parent.log_error(self._format_message(message), exc_info=exc_info, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.parent.log_warning(self._format_message(message), **kwargs)
    
    def debug(self, message: str, **kwargs):
        self.parent.log_debug(self._format_message(message), **kwargs)


# Создание глобального логгера для использования в других модулях
bot_logger = BotLogger()

# Экспорт для удобного импорта
__all__ = ['BotLogger', 'ContextLogger', 'bot_logger']

if __name__ == "__main__":
    # Демонстрация работы логгера
    demo_logger = BotLogger(logger_name="DemoLogger")
    
    demo_logger.log_info("Тестовое информационное сообщение")
    demo_logger.log_warning("Тестовое предупреждение")
    demo_logger.log_debug("Тестовое отладочное сообщение")
    demo_logger.log_error("Тестовая ошибка")
    
    demo_logger.log_user_activity(12345, "start_command", {"username": "test_user"})
    demo_logger.log_api_call("Groq", "/chat/completions", "success", 0.15)
    demo_logger.log_bot_event("startup", "Бот успешно запущен")
    demo_logger.log_performance("message_processing", 0.045, True)
    
    # Контекстный логгер
    handler_logger = demo_logger.create_context_logger("message_handler")
    handler_logger.info("Обработка входящего сообщения")
    
    # Статистика
    stats = demo_logger.get_log_stats()
    demo_logger.log_info(f"Статистика логов: {stats}") 