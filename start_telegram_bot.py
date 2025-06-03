#!/usr/bin/env python3
"""
Простой стартер для Telegram Stars/TON бота
Демонстрирует интеграцию с новой системой оплаты
"""

import os
import sys
from datetime import datetime

def print_startup_banner():
    """Красивый баннер при запуске"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                🔥 TELEGRAM STARS & TON BOT 🔥                ║
║              Монетизированный OF Бот v2.0                    ║
╠══════════════════════════════════════════════════════════════╣
║  ⭐ Telegram Stars - мгновенная оплата в приложении          ║
║  💎 TON Криптовалюта - децентрализованные платежи            ║
║  🎯 50 бесплатных сообщений для привлечения                  ║
║  💰 3 премиум тарифа с прогрессивным контентом               ║
║  🔞 Эксплицитный контент для взрослых                        ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"🕐 Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_environment():
    """Проверка переменных окружения"""
    required_vars = {
        'BOT_TOKEN': 'Токен Telegram бота',
        'TON_WALLET': 'TON кошелек для приема платежей (опционально)',
        'ADMIN_USER_IDS': 'ID администраторов (опционально)'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value and var == 'BOT_TOKEN':
            missing_vars.append(f"❌ {var}: {description}")
        elif value:
            if var == 'BOT_TOKEN':
                print(f"✅ {var}: {'*' * (len(value)-8) + value[-8:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: не установлен (будет использоваться значение по умолчанию)")
    
    if missing_vars:
        print("\n🚨 КРИТИЧЕСКИЕ ОШИБКИ:")
        for error in missing_vars:
            print(error)
        print("\nПример настройки:")
        print("export BOT_TOKEN='7843350631:AAHQ6h_BKAH3J4sNkh9ypNt1jih4yKYM_gs'")
        print("export TON_WALLET='UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB'")
        print("export ADMIN_USER_IDS='377917978'")
        return False
    
    return True

def check_dependencies():
    """Проверка зависимостей"""
    required_modules = [
        'telebot',
        'json',
        'datetime',
        'os'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}")
    
    if missing_modules:
        print(f"\n🚨 Установите недостающие модули:")
        print(f"pip install pyTelegramBotAPI")
        return False
    
    return True

def show_configuration():
    """Показать текущую конфигурацию"""
    print("\n📋 КОНФИГУРАЦИЯ СИСТЕМЫ:")
    print("=" * 50)
    
    # Импорт конфигурации
    try:
        from monetization_config import config
        
        print(f"💰 Бесплатный пробный период: {config.FREE_TRIAL_MESSAGES} сообщений на {config.FREE_TRIAL_DAYS} дней")
        print(f"⭐ Premium Daily: ⭐{config.STARS_PRICING['premium']['daily']} Stars")
        print(f"💎 VIP Daily: ⭐{config.STARS_PRICING['vip']['daily']} Stars") 
        print(f"👑 Ultimate Daily: ⭐{config.STARS_PRICING['ultimate']['daily']} Stars")
        print(f"🔐 TON Кошелек: {config.TON_WALLET_ADDRESS}")
        print(f"🎯 Лимиты сообщений: Premium({config.MESSAGE_LIMITS['premium']}), VIP({config.MESSAGE_LIMITS['vip']}), Ultimate({config.MESSAGE_LIMITS['ultimate']})")
        
    except ImportError as e:
        print(f"⚠️ Не удалось загрузить конфигурацию: {e}")

def show_usage_examples():
    """Показать примеры использования"""
    print("\n🎮 КОМАНДЫ БОТА:")
    print("=" * 50)
    print("👤 Для пользователей:")
    print("  /start - начать работу с ботом")
    print("  /status - показать статус подписки")
    print("  /payment - открыть меню оплаты")
    print("  /pricing - показать все тарифы")
    print()
    print("🔧 Для администраторов:")
    print("  /revenue - статистика доходов")
    print("  /cache_stats - эффективность кеширования")
    print()
    print("💳 Методы оплаты:")
    print("  ⭐ Telegram Stars - встроенная оплата")
    print("  💎 TON Crypto - криптовалютные платежи")

def main():
    """Главная функция запуска"""
    # Красивый баннер
    print_startup_banner()
    
    # Проверка зависимостей
    print("🔍 ПРОВЕРКА ЗАВИСИМОСТЕЙ:")
    print("-" * 30)
    if not check_dependencies():
        sys.exit(1)
    
    print()
    
    # Проверка окружения
    print("🌍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print("-" * 40)
    if not check_environment():
        sys.exit(1)
    
    # Показать конфигурацию
    show_configuration()
    
    # Показать примеры использования
    show_usage_examples()
    
    print("\n🚀 ЗАПУСК БОТА...")
    print("=" * 50)
    
    try:
        # Импорт и запуск бота
        from monetized_bot import MonetizedBot
        
        print("✅ Модули успешно загружены")
        print("⭐ Telegram Stars система: АКТИВНА")
        print("💎 TON платежи: АКТИВНЫ")
        print("🔞 Эксплицитный контент: ЗАГРУЖЕН")
        print("💾 Кеширование: ОПТИМИЗИРОВАНО")
        print()
        print("🔥 Бот запущен! Нажмите Ctrl+C для остановки")
        print("📱 Начните чат с ботом в Telegram")
        print()
        
        # Запуск бота
        bot = MonetizedBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n🚨 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("Проверьте конфигурацию и попробуйте снова")
        sys.exit(1)

if __name__ == "__main__":
    main() 