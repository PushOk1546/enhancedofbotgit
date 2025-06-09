"""
OF Assistant Bot Package

Пакет для создания Telegram-бота помощника OnlyFans моделей.
Использует pyTelegramBotAPI и Groq API для генерации контента.

Основные возможности:
- Управление состоянием пользователей
- Генерация контента с помощью Groq API
- Обработка PPV контента
- Система напоминаний
- Логирование и мониторинг
- Кэширование и оптимизация

Версия: 1.0.0
Автор: OF Assistant Bot Team
Лицензия: MIT
"""

__version__ = "1.0.0"
__author__ = "OF Assistant Bot Team"
__license__ = "MIT"
__description__ = "Telegram bot assistant for OnlyFans models"
__keywords__ = ["telegram", "bot", "onlyfans", "groq", "ai", "assistant"]

# Основные модули пакета
<<<<<<< HEAD
# from .config import (
#     BOT_TOKEN,
#     MODELS,
#     FLIRT_STYLES,
#     RELATIONSHIP_STAGES,
#     SURVEY_STEPS,
#     PPV_STYLES
# )
# from .models import (
#     UserState,
#     PPVReminder,
#     UserPreferences,
#     ConversationStage
# )
# from .state_manager import StateManager
# from .utils import (
#     setup_logging,
#     get_main_keyboard,
#     get_model_keyboard,
#     get_flirt_style_keyboard,
#     get_relationship_stage_keyboard,
#     get_survey_keyboard,
#     get_ppv_style_keyboard,
#     get_quick_continue_keyboard,
#     get_smart_continuation_keyboard
# )
# from .api import generate_groq_response
# from .chat_handlers import ChatHandlers
# from .bot import BotManager
=======
from .config.config import BOT_TOKEN, MODELS, FLIRT_STYLES
from .models import UserState, PPVReminder, UserPreferences
from .state_manager import StateManager
from .utils import setup_logging, get_main_keyboard
from .api import generate_groq_response
from .chat_handlers import ChatHandlers
from .bot import BotManager
>>>>>>> e70b13b82d79c7880bd4773edfd17a09645b5006

__all__ = [
    # Оставьте только реально существующие объекты, если они есть в проекте
] 