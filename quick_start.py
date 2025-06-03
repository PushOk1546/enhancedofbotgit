#!/usr/bin/env python3
"""
🚀 БЫСТРЫЙ СТАРТ - ULTIMATE ENTERPRISE BOT 🚀
Простой запуск без лишних зависимостей
"""

import os
import sys

def print_banner():
    print("""
🔥 QUICK START - ULTIMATE ENTERPRISE BOT 🔥
════════════════════════════════════════════
    """)

def check_environment():
    """Проверка переменных окружения"""
    bot_token = os.getenv('BOT_TOKEN')
    admin_ids = os.getenv('ADMIN_USER_IDS', '377917978')
    
    if not bot_token:
        print("❌ BOT_TOKEN не найден!")
        print("\n💡 Установите токен бота:")
        print("   set BOT_TOKEN=your_telegram_bot_token")
        print("   set ADMIN_USER_IDS=377917978")
        print("\n🤖 Получить токен: https://t.me/BotFather")
        return False
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ ADMIN_IDS: {admin_ids}")
    return True

def check_dependencies():
    """Проверка критических зависимостей"""
    critical_modules = ['telebot', 'requests']
    missing = []
    
    for module in critical_modules:
        try:
            __import__(module)
            print(f"✅ {module}: OK")
        except ImportError:
            missing.append(module)
            print(f"❌ {module}: ОТСУТСТВУЕТ")
    
    if missing:
        print(f"\n❌ Установите: pip install {' '.join(missing)}")
        print("💡 Или запустите: python install_dependencies_fixed.py")
        return False
    
    return True

def start_simple_bot():
    """Запуск простой версии бота"""
    try:
        print("\n🚀 Запуск Simple Start...")
        import simple_start
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска simple_start: {e}")
        return False

def start_monetized_bot():
    """Запуск монетизированного бота"""
    try:
        print("\n💰 Запуск Monetized Bot...")
        from monetized_bot import MonetizedBot
        bot = MonetizedBot()
        bot.run()
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска monetized_bot: {e}")
        return False

def start_enterprise_launcher():
    """Запуск enterprise лаунчера"""
    try:
        print("\n🏢 Запуск Enterprise Launcher...")
        import ultimate_enterprise_launcher
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска enterprise launcher: {e}")
        return False

def main():
    print_banner()
    
    # Проверка окружения
    if not check_environment():
        sys.exit(1)
    
    # Проверка зависимостей
    if not check_dependencies():
        sys.exit(1)
    
    print("\n🎯 Выберите режим запуска:")
    print("1. 🚀 Simple Start (базовый функционал)")
    print("2. 💰 Monetized Bot (полный функционал)")
    print("3. 🏢 Enterprise Launcher (максимум возможностей)")
    print("4. ⚡ Авто-выбор")
    
    try:
        choice = input("\nВведите номер (1-4): ").strip()
        
        if choice == "1":
            success = start_simple_bot()
        elif choice == "2":
            success = start_monetized_bot()
        elif choice == "3":
            success = start_enterprise_launcher()
        elif choice == "4" or choice == "":
            # Авто-выбор: пробуем от простого к сложному
            success = (start_simple_bot() or 
                      start_monetized_bot() or 
                      start_enterprise_launcher())
        else:
            print("❌ Неверный выбор")
            sys.exit(1)
        
        if not success:
            print("\n❌ Не удалось запустить ни одну версию бота")
            print("💡 Проверьте:")
            print("   1. BOT_TOKEN корректный")
            print("   2. Установлены зависимости: pip install pyTelegramBotAPI requests")
            print("   3. Интернет соединение работает")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Запуск прерван пользователем")
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        print("💡 Попробуйте простой запуск: python simple_start.py")

if __name__ == "__main__":
    main() 