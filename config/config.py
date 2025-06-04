"""
Модуль конфигурации бота.
Содержит все константы, настройки и конфигурационные параметры.
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токены и ключи API
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_IDS = set(map(int, filter(None, os.getenv('ADMIN_IDS', '').split(','))))

# Настройки логирования
LOG_DIR = "logs"
LOG_FILE = "bot.json"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Настройки истории сообщений
MAX_HISTORY_LENGTH = 10

# Настройки моделей
MODELS = {
    'eco': {
        'id': 'llama-3.1-8b-instant',
        'description': '💚 Эко - быстрая и доступная'
    },
    'fast': {
        'id': 'llama-3.3-70b-versatile',
        'description': '🧠 Умная - лучшие ответы'
    },
    'quick': {
        'id': 'llama-3.1-8b-instant',
        'description': '⚡ Быстрая - хорошие ответы'
    },
    'fastest': {
        'id': 'llama-3.1-8b-instant',
        'description': '🚀 Супербыстрая - простые ответы'
    }
}

# Настройки Groq API
GROQ_MAX_TOKENS = 120
GROQ_TEMPERATURE = 0.8

# Настройки повторных попыток
RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT = 4
RETRY_MAX_WAIT = 10

# Стили флирта
FLIRT_STYLES = {
    'игривый': {
        'id': 'playful',
        'description': '😋 Игривый и веселый',
        'emoji': '🌟'
    },
    'страстный': {
        'id': 'passionate',
        'description': '🔥 Страстный и интенсивный',
        'emoji': '💋'
    },
    'нежный': {
        'id': 'tender',
        'description': '🌸 Нежный и романтичный',
        'emoji': '💝'
    }
}

# Этапы отношений
RELATIONSHIP_STAGES = {
    'знакомство': {
        'description': '👋 Первое знакомство',
        'key_points': ['представление', 'интерес', 'открытость']
    },
    'поддержание': {
        'description': '💫 Поддержание интереса',
        'key_points': ['углубление связи', 'регулярность', 'вовлеченность']
    },
    'близость': {
        'description': '💖 Укрепление близости',
        'key_points': ['доверие', 'интимность', 'эксклюзивность']
    }
}

# Шаги опроса
SURVEY_STEPS = {
    'content_types': {
        'question': '📝 Какие типы контента вас интересуют больше всего?',
        'options': [
            ('photos', '📸 Фото'),
            ('videos', '🎥 Видео'),
            ('messages', '💌 Личные сообщения'),
            ('all', '✨ Всё вышеперечисленное')
        ]
    },
    'price_range': {
        'question': '💰 Какой ценовой диапазон для вас наиболее комфортен?',
        'options': [
            ('budget', '💝 До $10'),
            ('medium', '💎 $10-30'),
            ('premium', '👑 $30+'),
            ('various', '🌟 Разный, зависит от контента')
        ]
    },
    'communication_style': {
        'question': '💭 Какой стиль общения вы предпочитаете?',
        'options': [
            ('flirty', '😘 Флиртующий'),
            ('friendly', '🤗 Дружеский'),
            ('professional', '👔 Деловой'),
            ('mixed', '🎭 Смешанный')
        ]
    },
    'notification_frequency': {
        'question': '🔔 Как часто вы хотели бы получать уведомления о новом контенте?',
        'options': [
            ('often', '⚡ Часто (несколько раз в день)'),
            ('daily', '📅 Раз в день'),
            ('occasional', '🌙 Иногда (2-3 раза в неделю)'),
            ('rarely', '🌟 Редко (только особые предложения)')
        ]
    }
}

# Стили PPV контента
PPV_STYLES = {
    'провокационный': 'Дерзкий и провокационный контент',
    'романтичный': 'Романтичный и нежный контент',
    'игривый': 'Игривый и веселый контент',
    'интимный': 'Интимный и личный контент',
    'элегантный': 'Элегантный и изысканный контент'
}

#  
SECURITY_SETTINGS = {
    'max_retries': 3,
    'timeout': 30,
    'max_message_size': 4096
}
