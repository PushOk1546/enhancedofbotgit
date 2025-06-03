#!/usr/bin/env python3
"""
Улучшенный стартер для Telegram Stars/TON бота
Автоматически решает проблемы с конфликтами API и другие распространенные ошибки
"""

import os
import sys
import time
import signal
from datetime import datetime

def print_startup_banner():
    """Красивый баннер при запуске"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║            🔥 TELEGRAM STARS & TON BOT v2.1 🔥               ║
║           Монетизированный OF Бот (Исправленный)             ║
╠══════════════════════════════════════════════════════════════╣
║  ⭐ Telegram Stars - мгновенная оплата в приложении          ║
║  💎 TON Криптовалюта - децентрализованные платежи            ║
║  🛠️ Автоматическое исправление API конфликтов               ║
║  🔧 Улучшенная обработка ошибок                             ║
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
        return False
    
    return True

def kill_existing_bots():
    """Остановить существующие процессы ботов"""
    print("🔍 Поиск существующих процессов ботов...")
    
    try:
        import psutil
        
        current_pid = os.getpid()
        killed_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Проверяем Python процессы с нашими скриптами
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('bot' in arg.lower() for arg in cmdline):
                        if proc.info['pid'] != current_pid:  # Не убиваем текущий процесс
                            print(f"🔪 Остановка процесса: PID {proc.info['pid']}")
                            proc.terminate()
                            killed_processes.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed_processes:
            print(f"✅ Остановлено {len(killed_processes)} процессов")
            time.sleep(2)  # Дать время на завершение
        else:
            print("ℹ️ Конфликтующие процессы не найдены")
            
    except ImportError:
        print("⚠️ psutil не установлен, пропускаем проверку процессов")

def setup_signal_handlers():
    """Настройка обработчиков сигналов для корректного завершения"""
    def signal_handler(sig, frame):
        print("\n\n⏹️ Получен сигнал завершения...")
        print("🔄 Корректное завершение бота...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)

def create_fixed_bot():
    """Создать бота с исправлениями конфликтов API"""
    try:
        from monetized_bot import MonetizedBot
        import telebot
        
        # Создаем бота с улучшенной обработкой ошибок
        class FixedMonetizedBot(MonetizedBot):
            def __init__(self):
                super().__init__()
                self.max_retries = 3
                self.retry_delay = 5
            
            def run_with_error_handling(self):
                """Запуск с обработкой ошибок API"""
                for attempt in range(self.max_retries):
                    try:
                        print(f"🚀 Попытка запуска #{attempt + 1}...")
                        
                        # Очистка webhook перед запуском polling
                        try:
                            self.bot.remove_webhook()
                            print("✅ Webhook очищен")
                            time.sleep(1)
                        except Exception as e:
                            print(f"⚠️ Не удалось очистить webhook: {e}")
                        
                        # Тест подключения к API
                        try:
                            me = self.bot.get_me()
                            print(f"✅ Подключение к API успешно: @{me.username}")
                        except Exception as e:
                            print(f"❌ Ошибка подключения к API: {e}")
                            if attempt < self.max_retries - 1:
                                print(f"⏳ Повтор через {self.retry_delay} секунд...")
                                time.sleep(self.retry_delay)
                                continue
                            else:
                                raise
                        
                        # Запуск polling с повторными попытками
                        print("🔄 Запуск polling...")
                        self.bot.polling(
                            none_stop=True,
                            timeout=60,
                            long_polling_timeout=60,
                            interval=1
                        )
                        
                    except telebot.apihelper.ApiTelegramException as e:
                        if "409" in str(e) or "Conflict" in str(e):
                            print(f"⚠️ Конфликт API (409) - попытка {attempt + 1}")
                            if attempt < self.max_retries - 1:
                                print(f"⏳ Ожидание {self.retry_delay * (attempt + 1)} секунд...")
                                time.sleep(self.retry_delay * (attempt + 1))
                                continue
                            else:
                                print("❌ Не удалось разрешить конфликт API после всех попыток")
                                raise
                        else:
                            print(f"❌ Ошибка Telegram API: {e}")
                            raise
                    
                    except KeyboardInterrupt:
                        print("\n⏹️ Остановка по запросу пользователя")
                        break
                    
                    except Exception as e:
                        print(f"❌ Неожиданная ошибка: {e}")
                        if attempt < self.max_retries - 1:
                            print(f"⏳ Повтор через {self.retry_delay} секунд...")
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            raise
                    
                    # Если дошли сюда - успешный запуск
                    break
        
        return FixedMonetizedBot()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return None

def main():
    """Главная функция запуска"""
    # Красивый баннер
    print_startup_banner()
    
    # Настройка обработчиков сигналов
    setup_signal_handlers()
    
    # Остановка существующих ботов
    kill_existing_bots()
    
    # Проверка окружения
    print("🌍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print("-" * 40)
    if not check_environment():
        print("\n🚨 Настройте переменные окружения:")
        print("set BOT_TOKEN=ваш_токен")
        print("set ADMIN_USER_IDS=377917978")
        sys.exit(1)
    
    print("\n🚀 ЗАПУСК БОТА С ИСПРАВЛЕНИЯМИ...")
    print("=" * 50)
    
    try:
        # Создание и запуск бота
        bot = create_fixed_bot()
        if not bot:
            print("❌ Не удалось создать бота")
            sys.exit(1)
        
        print("✅ Бот создан успешно")
        print("⭐ Telegram Stars система: АКТИВНА")
        print("💎 TON платежи: АКТИВНЫ") 
        print("🔞 Эксплицитный контент: ЗАГРУЖЕН")
        print("💾 Кеширование: ОПТИМИЗИРОВАНО")
        print("🛠️ Обработка ошибок: УЛУЧШЕНА")
        print()
        print("🔥 Бот запущен! Нажмите Ctrl+C для остановки")
        print("📱 Начните чат с ботом в Telegram")
        print()
        
        # Запуск с обработкой ошибок
        bot.run_with_error_handling()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n🚨 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("📝 Попробуйте:")
        print("1. Подождать 30 секунд и запустить снова")
        print("2. Проверить токен бота")
        print("3. Убедиться, что нет других запущенных ботов")
        sys.exit(1)

if __name__ == "__main__":
    main() 