#!/usr/bin/env python3
"""
🔥 ULTIMATE MONETIZED BOT STARTER 🔥
Полностью интегрированный запуск бота с улучшенным UI и исправленными багами
"""

import os
import sys
from datetime import datetime

def validate_environment():
    """🔧 Проверка окружения перед запуском"""
    print("🔍 Проверка окружения...")
    
    required_vars = ['BOT_TOKEN', 'ADMIN_USER_IDS']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("📝 Пример настройки:")
        print("set BOT_TOKEN=your_bot_token_here")
        print("set ADMIN_USER_IDS=377917978")
        return False
    
    print("✅ Окружение настроено корректно")
    return True

def check_dependencies():
    """📦 Проверка зависимостей"""
    print("📦 Проверка зависимостей...")
    
    required_modules = [
        'telebot',
        'requests', 
        'datetime',
        'json',
        'os'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Отсутствуют модули: {', '.join(missing_modules)}")
        print("💡 Установите: python install_deps.py")
        return False
    
    print("✅ Все зависимости установлены")
    return True

def check_core_files():
    """📄 Проверка основных файлов"""
    print("📄 Проверка файлов системы...")
    
    required_files = [
        'monetized_bot.py',
        'premium_system.py', 
        'admin_commands.py',
        'telegram_payment_system.py',
        'adult_templates.py',
        'response_cache.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    print("✅ Все системные файлы на месте")
    return True

def start_bot():
    """🚀 Запуск бота"""
    print("🚀 Запуск Ultimate Monetized Bot...")
    
    try:
        # Импортируем и запускаем главный бот
        from monetized_bot import MonetizedBot
        
        print("🔥 " + "="*50)
        print("🔥 ULTIMATE MONETIZED OF BOT - ЗАПУЩЕН!")
        print("🔥 " + "="*50)
        print("💰 Telegram Stars: АКТИВНЫ")
        print("💎 TON Payments: АКТИВНЫ") 
        print("👑 Premium System: АКТИВНЫ")
        print("🔞 Adult Templates: ЗАГРУЖЕНЫ")
        print("⚡ Response Cache: ОПТИМИЗИРОВАН")
        print("⚙️ Admin Commands: ГОТОВЫ")
        print("🎨 Enhanced UI: ВКЛЮЧЕН")
        print("🔥 " + "="*50)
        print(f"🕐 Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 Админ ID: {os.getenv('ADMIN_USER_IDS', '377917978')}")
        print(f"💎 TON Wallet: UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB")
        print("🔥 " + "="*50)
        print("🚀 BOT IS RUNNING... (Ctrl+C для остановки)")
        print("🔥 " + "="*50)
        
        # Создаем и запускаем бота
        bot = MonetizedBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔧 Попробуйте перезапустить или проверьте логи")
        sys.exit(1)

def main():
    """🎯 Главная функция запуска"""
    print("🔥 " + "="*60)
    print("🔥      ULTIMATE MONETIZED OF BOT STARTUP      🔥")  
    print("🔥 " + "="*60)
    print("🎯 Версия: 3.0 Enhanced UI & Full Functionality")
    print("💰 Фокус: Максимальная монетизация + UX")
    print("🔥 " + "="*60)
    
    # Проверки перед запуском
    if not validate_environment():
        print("\n❌ Ошибка конфигурации окружения")
        sys.exit(1)
    
    if not check_dependencies():
        print("\n❌ Ошибка зависимостей")
        sys.exit(1)
    
    if not check_core_files():
        print("\n❌ Ошибка файлов системы")
        sys.exit(1)
    
    print("\n✅ Все проверки пройдены успешно!")
    print("🚀 Готов к запуску...")
    
    # Запуск бота
    start_bot()

if __name__ == "__main__":
    main() 