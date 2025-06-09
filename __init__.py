"""
OF Assistant Bot Package

Пакет для создания Telegram-бота помощника OnlyFans моделей.
Использует DeepSeek AI для генерации контента без цензуры.

Основные возможности:
- Управление состоянием пользователей
- Генерация контента с помощью DeepSeek API
- Обработка PPV контента с планировщиком
- Система напоминаний и статистики
- Логирование и мониторинг
- Кэширование и оптимизация

Версия: 2.0.0
Автор: OF Assistant Bot Team
Лицензия: MIT
"""

__version__ = "2.0.0"
__author__ = "OF Assistant Bot Team"
__license__ = "MIT"
__description__ = "Telegram bot assistant for OnlyFans models with DeepSeek AI"
__keywords__ = ["telegram", "bot", "onlyfans", "deepseek", "ai", "assistant", "nsfw"]

# Основные модули пакета - импорты только если существуют
try:
    from .config import config
    from .main import OFAssistantBot
    from .handlers import BotHandlers, setup_handlers
    from .services.ai_integration import AIService, ai_service
    from .api_handler import deepseek_handler
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

__all__ = [
    "config",
    "OFAssistantBot", 
    "BotHandlers",
    "setup_handlers",
    "AIService",
    "ai_service",
    "deepseek_handler"
] if CONFIG_AVAILABLE else [] 