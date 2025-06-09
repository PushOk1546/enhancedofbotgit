"""
Конфигурационный файл для OF Assistant Bot
"""

import os
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️ python-dotenv не установлен. Переменные окружения читаются напрямую.")


class Config:
    """Класс конфигурации с настройками бота"""
    
    def __init__(self):
        """Инициализация конфигурации"""
        self._load_settings()
    
    def _load_settings(self):
        """Загрузка настроек из переменных окружения"""
        
        # Обязательные переменные
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        
        # AI API настройки - теперь поддерживаем DeepSeek вместо Groq
        self.DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
        # Для обратной совместимости - если GROQ_API_KEY установлен, но DEEPSEEK_API_KEY нет
        if not self.DEEPSEEK_API_KEY and os.getenv('GROQ_API_KEY'):
            print("⚠️ Найден GROQ_API_KEY. Рекомендуется использовать DEEPSEEK_API_KEY для лучшей поддержки NSFW контента")
            self.DEEPSEEK_API_KEY = os.getenv('GROQ_API_KEY', '')  # Временная совместимость
        
        # Настройки логирования
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes', 'on')
        
        # Настройки кэширования
        self.CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 час
        self.MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '1000'))
        
        # Дополнительные настройки
        self.REDIS_URL = os.getenv('REDIS_URL', '')
        self.DATABASE_URL = os.getenv('DATABASE_URL', '')
        
        # Настройки webhook (для продакшена)
        self.WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '')
        self.WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8080'))
        self.WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')
        
        # Валидация обязательных настроек
        self._validate_required_settings()
    
    def _validate_required_settings(self):
        """Валидация обязательных настроек"""
        required_vars = ['TELEGRAM_BOT_TOKEN', 'DEEPSEEK_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(self, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
            print("💡 Создайте файл .env с необходимыми переменными")
    
    def get_log_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию для логирования"""
        return {
            'level': self.LOG_LEVEL,
            'format': (
                '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
                '<level>{level: <8}</level> | '
                '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
                '<level>{message}</level>'
            ),
            'rotation': '10 MB',
            'retention': '1 week',
            'compression': 'zip'
        }
    
    def get_bot_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию для бота"""
        return {
            'token': self.TELEGRAM_BOT_TOKEN,
            'parse_mode': 'HTML',
            'timeout': 60,
            'threaded': False
        }
    
    def get_deepseek_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию для DeepSeek API"""
        return {
            'api_key': self.DEEPSEEK_API_KEY,
            'model': 'deepseek-chat',
            'temperature': 0.8,
            'max_tokens': 300,
            'base_url': 'https://api.deepseek.com/v1'
        }
    
    # Для обратной совместимости
    def get_groq_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию для DeepSeek API (обратная совместимость)"""
        print("⚠️ get_groq_config() устарел. Используйте get_deepseek_config()")
        return self.get_deepseek_config()
    
    def display_config(self):
        """Отображает текущую конфигурацию (без секретных данных)"""
        config_info = {
            'LOG_LEVEL': self.LOG_LEVEL,
            'DEBUG': self.DEBUG,
            'CACHE_TTL': self.CACHE_TTL,
            'MAX_MESSAGE_LENGTH': self.MAX_MESSAGE_LENGTH,
            'TELEGRAM_BOT_TOKEN': '***' if self.TELEGRAM_BOT_TOKEN else 'НЕ УСТАНОВЛЕН',
            'DEEPSEEK_API_KEY': '***' if self.DEEPSEEK_API_KEY else 'НЕ УСТАНОВЛЕН',
            'REDIS_URL': self.REDIS_URL or 'НЕ УСТАНОВЛЕН',
            'DATABASE_URL': self.DATABASE_URL or 'НЕ УСТАНОВЛЕН',
            'WEBHOOK_HOST': self.WEBHOOK_HOST or 'НЕ УСТАНОВЛЕН',
            'WEBHOOK_PORT': self.WEBHOOK_PORT,
            'WEBHOOK_PATH': self.WEBHOOK_PATH
        }
        
        print("\n📋 Текущая конфигурация:")
        print("=" * 40)
        for key, value in config_info.items():
            print(f"{key}: {value}")
        print("=" * 40)
        
        return config_info


# Создаем глобальный экземпляр конфигурации
config = Config()

# Экспорт для удобного импорта
__all__ = ['config', 'Config']

if __name__ == "__main__":
    # Демонстрация конфигурации
    print("🔧 Конфигурация OF Assistant Bot")
    config.display_config()
    
    # Проверка наличия обязательных переменных
    if config.TELEGRAM_BOT_TOKEN and config.DEEPSEEK_API_KEY:
        print("\n✅ Все обязательные переменные установлены")
    else:
        print("\n❌ Некоторые обязательные переменные отсутствуют")
        print("💡 Создайте файл .env с содержимым:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("DEEPSEEK_API_KEY=your_deepseek_api_key_here") 