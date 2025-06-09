#!/usr/bin/env python3
"""
Тест запуска бота для проверки всех исправлений.
Проверяет инициализацию всех компонентов без реального запуска Telegram бота.
"""

import os
import sys
from pathlib import Path

def test_bot_startup():
    """Тестирует инициализацию бота"""
    print("🚀 ТЕСТ ЗАПУСКА БОТА")
    print("=" * 50)
    
    try:
        # 1. Проверяем конфигурацию
        print("🔍 Проверяем конфигурацию...")
        from config.config import BOT_TOKEN, GROQ_KEY, MODELS, FLIRT_STYLES, PPV_STYLES
        
        if not BOT_TOKEN:
            print("⚠️  BOT_TOKEN не установлен в .env")
        else:
            print("✅ BOT_TOKEN найден")
            
        if not GROQ_KEY:
            print("⚠️  GROQ_KEY не установлен в .env")
        else:
            print("✅ GROQ_KEY найден")
            
        print(f"✅ Моделей ИИ: {len(MODELS)}")
        print(f"✅ Стилей флирта: {len(FLIRT_STYLES)}")
        print(f"✅ Стилей PPV: {len(PPV_STYLES)}")
        
        # 2. Проверяем импорты основных модулей
        print("\n🔍 Проверяем импорты...")
        from state_manager import StateManager
        from models import UserState, PPVReminder
        from handlers import send_welcome_message, handle_start_command
        from utils import get_main_keyboard, get_ppv_style_keyboard
        from api import generate_groq_response
        print("✅ Все основные модули импортированы")
        
        # 3. Проверяем StateManager
        print("\n🔍 Тестируем StateManager...")
        sm = StateManager(data_file='data/test_users.json')
        user = sm.get_user(999999)
        print(f"✅ StateManager создан, тестовый пользователь: {user.user_id}")
        
        # 4. Проверяем создание клавиатур
        print("\n🔍 Тестируем клавиатуры...")
        main_kb = get_main_keyboard()
        ppv_kb = get_ppv_style_keyboard()
        print(f"✅ Основная клавиатура: {len(main_kb.keyboard)} рядов")
        print(f"✅ PPV клавиатура: {len(ppv_kb.keyboard)} кнопок")
        
        # 5. Проверяем async метод load_prompt
        print("\n🔍 Тестируем load_prompt...")
        import asyncio
        async def test_prompt():
            result = await sm.load_prompt('welcome')
            return result is None  # Нормально что None, файла ещё нет
        
        is_none = asyncio.run(test_prompt())
        if is_none:
            print("✅ load_prompt работает (файл не найден - это нормально)")
        else:
            print("✅ load_prompt работает (файл найден)")
        
        # 6. Попытка инициализации BotManager (без запуска)
        print("\n🔍 Тестируем инициализацию BotManager...")
        if BOT_TOKEN and BOT_TOKEN != "your_bot_token_here":
            from bot import BotManager
            bot_manager = BotManager()
            print("✅ BotManager создан успешно")
        else:
            print("⚠️  Пропускаем BotManager (нет валидного BOT_TOKEN)")
        
        print("\n" + "=" * 50)
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БОТ ГОТОВ К ЗАПУСКУ!")
        print("\n💡 Для запуска:")
        print("1. Убедитесь что BOT_TOKEN и GROQ_KEY установлены в .env")
        print("2. Запустите: python bot.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot_startup()
    sys.exit(0 if success else 1) 