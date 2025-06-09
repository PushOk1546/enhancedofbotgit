"""
OF Assistant Bot Package

Пакет для создания Telegram-бота помощника OnlyFans моделей.
Использует pyTelegramBotAPI и Groq API для генерации контента.
"""

__version__ = "1.0.0"
__author__ = "OF Assistant Bot Team"

# Основные модули пакета
from .config.config import BOT_TOKEN, MODELS, FLIRT_STYLES
from .models import UserState, PPVReminder, UserPreferences
from .state_manager import StateManager
from .utils import setup_logging, get_main_keyboard
from .api import generate_groq_response
from .chat_handlers import ChatHandlers
from .bot import BotManager

__all__ = [
    'BOT_TOKEN',
    'MODELS', 
    'FLIRT_STYLES',
    'UserState',
    'PPVReminder', 
    'UserPreferences',
    'StateManager',
    'setup_logging',
    'get_main_keyboard',
    'generate_groq_response',
    'ChatHandlers',
    'BotManager'
] 