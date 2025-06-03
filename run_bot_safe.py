#!/usr/bin/env python3
"""
БЕЗОПАСНЫЙ ЗАПУСК TELEGRAM STARS/TON БОТА
Решает все известные проблемы автоматически
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def print_header():
    """Вывести заголовок"""
    print("=" * 70)
    print("🔥 БЕЗОПАСНЫЙ ЗАПУСК TELEGRAM STARS/TON БОТА 🔥")
    print("=" * 70)
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_python_version():
    """Проверить версию Python"""
    print("🐍 ПРОВЕРКА PYTHON:")
    print(f"✅ Версия Python: {sys.version}")
    
    if sys.version_info < (3, 7):
        print("❌ Требуется Python 3.7 или выше!")
        return False
    return True

def install_missing_packages():
    """Установить недостающие пакеты"""
    print("\n📦 ПРОВЕРКА И УСТАНОВКА ПАКЕТОВ:")
    print("-" * 40)
    
    packages_to_check = [
        ("telebot", "pyTelegramBotAPI==4.14.0"),
        ("requests", "requests==2.31.0"),
        ("dotenv", "python-dotenv==1.0.0"),
        ("psutil", "psutil")
    ]
    
    for module, package in packages_to_check:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - УСТАНАВЛИВАЕМ...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True, text=True)
                print(f"✅ {package} - УСТАНОВЛЕН")
            except subprocess.CalledProcessError:
                print(f"⚠️ {package} - НЕ УДАЛОСЬ УСТАНОВИТЬ")

def check_bot_token():
    """Проверить токен бота"""
    print("\n🔑 ПРОВЕРКА ТОКЕНА БОТА:")
    print("-" * 30)
    
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ BOT_TOKEN не установлен!")
        print("📝 Установите токен:")
        print("   set BOT_TOKEN=ваш_токен_здесь")
        return False
    
    # Базовая проверка формата токена
    if ':' not in token or len(token) < 30:
        print("❌ Неверный формат токена!")
        return False
    
    print(f"✅ Токен найден: ...{token[-8:]}")
    return True

def kill_conflicting_processes():
    """Остановить конфликтующие процессы"""
    print("\n🔪 ОСТАНОВКА КОНФЛИКТУЮЩИХ ПРОЦЕССОВ:")
    print("-" * 45)
    
    try:
        import psutil
        current_pid = os.getpid()
        killed = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('bot' in str(arg).lower() or 'telegram' in str(arg).lower() for arg in cmdline):
                        if proc.info['pid'] != current_pid:
                            print(f"🔪 Останавливаем PID {proc.info['pid']}")
                            proc.terminate()
                            killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed > 0:
            print(f"✅ Остановлено {killed} процессов")
            time.sleep(3)  # Дать время на завершение
        else:
            print("ℹ️ Конфликтующие процессы не найдены")
            
    except ImportError:
        print("⚠️ psutil недоступен, пропускаем проверку процессов")

def test_telegram_api():
    """Тестировать подключение к Telegram API"""
    print("\n📡 ТЕСТИРОВАНИЕ TELEGRAM API:")
    print("-" * 35)
    
    try:
        import telebot
        
        token = os.getenv('BOT_TOKEN')
        if not token:
            return False
        
        bot = telebot.TeleBot(token)
        
        # Очистка webhook
        try:
            bot.remove_webhook()
            print("✅ Webhook очищен")
        except:
            pass
        
        # Тест API
        me = bot.get_me()
        print(f"✅ API работает: @{me.username}")
        print(f"✅ Bot ID: {me.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return False

def create_env_file():
    """Создать .env файл с базовыми настройками"""
    print("\n📄 СОЗДАНИЕ .ENV ФАЙЛА:")
    print("-" * 25)
    
    env_content = f"""# Telegram Bot Configuration
BOT_TOKEN={os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')}
ADMIN_USER_IDS={os.getenv('ADMIN_USER_IDS', '377917978')}

# TON Wallet for payments
TON_WALLET=UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB

# Monetization Settings
TEMPLATE_USAGE_RATIO=0.85
FREE_TRIAL_MESSAGES=50
EXPLICIT_CONTENT_ENABLED=true

# Cache Settings
CACHE_SIZE=15000
CACHE_TTL_HOURS=336

# Revenue Targets
DAILY_REVENUE_TARGET=100.0
MONTHLY_REVENUE_TARGET=3000.0
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ .env файл создан")
    except Exception as e:
        print(f"⚠️ Не удалось создать .env: {e}")

def run_bot():
    """Запустить бота"""
    print("\n🚀 ЗАПУСК БОТА:")
    print("-" * 15)
    
    try:
        # Импортируем улучшенный стартер
        exec(open('start_telegram_bot_fixed.py').read())
        
    except FileNotFoundError:
        print("❌ start_telegram_bot_fixed.py не найден!")
        print("🔄 Запускаем обычную версию...")
        
        try:
            from monetized_bot import MonetizedBot
            bot = MonetizedBot()
            
            print("✅ Бот создан успешно")
            print("🔥 Запуск бота...")
            print("📱 Начните чат в Telegram!")
            print("⏹️ Нажмите Ctrl+C для остановки")
            
            bot.bot.polling(none_stop=True, timeout=60)
            
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False
    
    return True

def main():
    """Главная функция"""
    print_header()
    
    # Проверки перед запуском
    checks = [
        ("Python версия", check_python_version),
        ("Пакеты", lambda: (install_missing_packages(), True)[1]),
        ("Токен бота", check_bot_token),
        ("Процессы", lambda: (kill_conflicting_processes(), True)[1]),
        ("Telegram API", test_telegram_api),
        (".env файл", lambda: (create_env_file(), True)[1]),
    ]
    
    print("🔍 ПРЕДЗАПУСКОВЫЕ ПРОВЕРКИ:")
    print("=" * 30)
    
    all_passed = True
    for name, check_func in checks:
        try:
            result = check_func()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"❌ {name}: Ошибка - {e}")
            all_passed = False
    
    if not all_passed:
        print("\n🚨 ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("📝 Исправьте ошибки выше и запустите снова")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    
    print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("🎉 Готов к запуску!")
    
    # Небольшая пауза перед запуском
    for i in range(3, 0, -1):
        print(f"🚀 Запуск через {i}...")
        time.sleep(1)
    
    # Запуск бота
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"\n🚨 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("\n📞 Обратитесь за поддержкой если проблема повторяется")
    
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main() 