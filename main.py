#!/usr/bin/env python3
"""
🤖 OF Assistant Bot - Главная точка входа
Powered by DeepSeek-R1

Telegram бот для управления OnlyFans с продвинутым AI
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем текущую директорию в Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from telebot.async_telebot import AsyncTeleBot
    from telebot import asyncio_filters
    from config import config
    from handlers import setup_handlers
    from enhanced_logging import BotLogger
    from api_handler import deepseek_handler
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)

# Инициализация логгера
logger = BotLogger(
    log_dir="logs",
    log_file="main.log", 
    logger_name="MainBot"
)

class OFAssistantBot:
    """Главный класс OF Assistant Bot"""
    
    def __init__(self):
        """Инициализация бота"""
        self.bot = None
        self.handlers = None
        
    async def initialize(self):
        """Инициализация всех компонентов"""
        try:
            logger.log_info("🚀 Запуск OF Assistant Bot...")
            
            # Проверка конфигурации
            if not config.TELEGRAM_BOT_TOKEN:
                logger.log_error("❌ TELEGRAM_BOT_TOKEN не найден!")
                print("❌ Добавьте TELEGRAM_BOT_TOKEN в файл .env")
                return False
                
            if not config.DEEPSEEK_API_KEY:
                logger.log_error("❌ DEEPSEEK_API_KEY не найден!")
                print("❌ Добавьте DEEPSEEK_API_KEY в файл .env")
                return False
            
            # Создание бота
            self.bot = AsyncTeleBot(
                token=config.TELEGRAM_BOT_TOKEN,
                parse_mode='HTML'
            )
            logger.log_info("✅ Telegram bot инициализирован")
            
            # Настройка обработчиков
            self.handlers = setup_handlers(self.bot)
            logger.log_info("✅ Обработчики настроены")
            
            # Тест DeepSeek
            test_response = await deepseek_handler.ask_deepseek("Тест подключения")
            if test_response:
                logger.log_info("✅ DeepSeek API подключен успешно")
            else:
                logger.log_warning("⚠️ Проблемы с DeepSeek API")
            
            return True
            
        except Exception as e:
            logger.log_error(f"💥 Ошибка инициализации: {e}")
            return False
    
    async def start_polling(self):
        """Запуск бота в режиме polling"""
        try:
            logger.log_info("🔄 Запуск polling...")
            
            # Информация о боте
            bot_info = await self.bot.get_me()
            logger.log_info(f"🤖 Бот @{bot_info.username} готов к работе!")
            print(f"\n🔥 OF Assistant Bot запущен!")
            print(f"🤖 Бот: @{bot_info.username}")
            print(f"🧠 AI: DeepSeek-R1")
            print(f"💕 Готов к соблазнению!")
            print(f"\n📱 Начните диалог: /start")
            print("🛑 Остановка: Ctrl+C\n")
            
            # Запуск
            await self.bot.polling(non_stop=True, timeout=60)
            
        except KeyboardInterrupt:
            logger.log_info("⏹️ Получен сигнал остановки")
            await self.shutdown()
        except Exception as e:
            logger.log_error(f"💥 Ошибка polling: {e}")
            await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы"""
        try:
            logger.log_info("🔄 Завершение работы...")
            
            if hasattr(self.handlers, 'scheduler'):
                self.handlers.scheduler.shutdown()
                logger.log_info("⏹️ Планировщик остановлен")
            
            if self.bot:
                await self.bot.close_session()
                logger.log_info("🔌 Сессия Telegram закрыта")
            
            logger.log_info("✅ Бот корректно завершил работу")
            print("\n👋 OF Assistant Bot остановлен")
            
        except Exception as e:
            logger.log_error(f"💥 Ошибка при завершении: {e}")

async def main():
    """Главная функция"""
    print("🔥 DeepSeek-R1 OF Assistant Bot")
    print("=" * 40)
    
    # Создание и запуск бота
    bot_instance = OFAssistantBot()
    
    if await bot_instance.initialize():
        await bot_instance.start_polling()
    else:
        print("❌ Не удалось инициализировать бота")
        print("💡 Проверьте настройки в файле .env")
        sys.exit(1)

def check_environment():
    """Проверка окружения перед запуском"""
    print("🔍 Проверка окружения...")
    
    # Проверка Python версии
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8+")
        sys.exit(1)
    
    # Проверка .env файла
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ Файл .env не найден")
        print("💡 Создайте .env файл с настройками:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token")
        print("DEEPSEEK_API_KEY=your_deepseek_key")
        return False
    
    return True

if __name__ == "__main__":
    try:
        # Проверки перед запуском
        if not check_environment():
            sys.exit(1)
        
        # Запуск бота
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Пока!")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1) 