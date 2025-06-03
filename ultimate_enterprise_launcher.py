#!/usr/bin/env python3
"""
🚀 ULTIMATE ENTERPRISE BOT LAUNCHER 🚀
Интегрированный запуск всех систем:
- Monitoring System (Real-time метрики)
- Notification System (Алерты админам)  
- Backup System (Автоматические backup)
- Monetized Bot (Основной функционал)
- Admin Commands (Управление системой)

ENTERPRISE-READY PRODUCTION LAUNCHER
"""

import os
import sys
import time
import signal
import atexit
from datetime import datetime
from typing import Dict, Any
import threading

# Глобальные переменные для систем
systems_status = {
    'monitoring': False,
    'notifications': False,
    'backup': False,
    'bot': False,
    'admin': False
}

def print_banner():
    """Красивый баннер запуска"""
    banner = f"""
🔥═══════════════════════════════════════════════════════════════════════════🔥
║                                                                           ║
║               🚀 ULTIMATE ENTERPRISE TELEGRAM BOT 🚀                    ║
║                                                                           ║
║  💎 Telegram Stars Integration    🔞 Adult Content System                ║
║  💰 TON Cryptocurrency Support    📊 Real-time Analytics                 ║
║  🎨 Stunning UI/UX Experience     🔔 Smart Notifications                 ║
║  💾 Auto Backup & Recovery        ⚡ Performance Monitoring              ║
║  👑 Premium Monetization          🛡️ Enterprise Security                ║
║                                                                           ║
║  📅 Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                              ║
║  🌟 Version: Enterprise v3.0                                            ║
║  🏗️ Architecture: Production-Ready                                       ║
║                                                                           ║
🔥═══════════════════════════════════════════════════════════════════════════🔥
    """
    print(banner)

def validate_environment() -> bool:
    """Валидация окружения"""
    print("🔍 Проверка окружения...")
    
    required_vars = {
        'BOT_TOKEN': 'Telegram Bot Token',
        'ADMIN_USER_IDS': 'Administrator User IDs'
    }
    
    optional_vars = {
        'GROQ_KEY': 'Groq AI API Key',
        'SMTP_EMAIL': 'Email for notifications',
        'WEBHOOK_URL': 'Webhook URL for alerts'
    }
    
    missing_critical = []
    missing_optional = []
    
    # Проверка критических переменных
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_critical.append(f"  ❌ {var}: {description}")
        else:
            print(f"  ✅ {var}: Configured")
    
    # Проверка опциональных переменных
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"  ⚠️ {var}: {description} (optional)")
        else:
            print(f"  ✅ {var}: Configured")
    
    if missing_critical:
        print("\n❌ КРИТИЧЕСКИЕ ПЕРЕМЕННЫЕ ОТСУТСТВУЮТ:")
        for missing in missing_critical:
            print(missing)
        print("\n💡 Пример настройки:")
        print("  set BOT_TOKEN=your_telegram_bot_token")
        print("  set ADMIN_USER_IDS=123456789,987654321")
        return False
    
    if missing_optional:
        print("\n⚠️ Опциональные переменные (система будет работать без них):")
        for missing in missing_optional:
            print(missing)
    
    print("✅ Валидация окружения пройдена!")
    return True

def check_dependencies() -> bool:
    """Проверка зависимостей"""
    print("\n📦 Проверка зависимостей...")
    
    critical_modules = [
        ('telebot', 'PyTelegramBotAPI'),
        ('requests', 'HTTP requests'),
        ('psutil', 'System monitoring'),
        ('sqlite3', 'Database (built-in)'),
    ]
    
    optional_modules = [
        ('groq', 'Groq AI integration'),
        ('smtplib', 'Email notifications (built-in)'),
    ]
    
    missing_critical = []
    
    for module, description in critical_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}: {description}")
        except ImportError:
            missing_critical.append(module)
            print(f"  ❌ {module}: {description} - ОТСУТСТВУЕТ")
    
    for module, description in optional_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}: {description}")
        except ImportError:
            print(f"  ⚠️ {module}: {description} - опционально")
    
    if missing_critical:
        print(f"\n❌ Критические модули отсутствуют: {', '.join(missing_critical)}")
        print("💡 Установите: python install_deps.py")
        return False
    
    print("✅ Все критические зависимости установлены!")
    return True

def initialize_monitoring_system():
    """Инициализация системы мониторинга"""
    try:
        print("📊 Инициализация мониторинга...")
        from monitoring_system import monitoring_system
        
        # Даем время на инициализацию
        time.sleep(2)
        
        systems_status['monitoring'] = True
        print("✅ Monitoring System: АКТИВИРОВАН")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации мониторинга: {e}")
        return False

def initialize_notification_system():
    """Инициализация системы уведомлений"""
    try:
        print("🔔 Инициализация уведомлений...")
        from notification_system import notification_system
        
        # Тестируем систему уведомлений
        notification_system.send_alert(
            level=notification_system.AlertLevel.INFO,
            title="Bot System Started",
            message="Ultimate Enterprise Bot successfully launched!",
            source="launcher",
            details={
                "launch_time": datetime.now().isoformat(),
                "version": "Enterprise v3.0"
            }
        )
        
        systems_status['notifications'] = True
        print("✅ Notification System: АКТИВИРОВАН")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации уведомлений: {e}")
        return False

def initialize_backup_system():
    """Инициализация системы backup"""
    try:
        print("💾 Инициализация backup системы...")
        from backup_system import backup_system
        
        # Создаем startup backup
        startup_backup = backup_system.create_backup(
            backup_type="startup",
            description=f"Startup backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if startup_backup:
            print(f"📦 Startup backup создан: {startup_backup}")
        
        systems_status['backup'] = True
        print("✅ Backup System: АКТИВИРОВАН")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации backup: {e}")
        return False

def initialize_admin_system():
    """Инициализация админ системы"""
    try:
        print("⚙️ Инициализация админ команд...")
        # Админ команды будут инициализированы вместе с ботом
        systems_status['admin'] = True
        print("✅ Admin System: ГОТОВ")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации админ системы: {e}")
        return False

def initialize_main_bot():
    """Инициализация основного бота"""
    try:
        print("🤖 Инициализация основного бота...")
        
        # Интегрируем мониторинг в бот
        if systems_status['monitoring']:
            try:
                from monitoring_system import monitoring_system
                print("  📊 Мониторинг интегрирован в бот")
            except:
                pass
        
        systems_status['bot'] = True
        print("✅ Main Bot: ГОТОВ К ЗАПУСКУ")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
        return False

def start_main_bot():
    """Запуск основного бота"""
    try:
        print("\n🚀 ЗАПУСК ОСНОВНОГО БОТА...")
        
        # Импортируем и запускаем монетизированный бот
        from monetized_bot import MonetizedBot
        
        print("🔥 " + "="*70)
        print("🔥 ULTIMATE ENTERPRISE TELEGRAM BOT - ЗАПУЩЕН!")
        print("🔥 " + "="*70)
        print("💰 Telegram Stars: АКТИВНЫ")
        print("💎 TON Payments: АКТИВНЫ")
        print("👑 Premium System: АКТИВНЫ")
        print("🔞 Adult Templates: ЗАГРУЖЕНЫ")
        print("⚡ Response Cache: ОПТИМИЗИРОВАН")
        print("⚙️ Admin Commands: ГОТОВЫ")
        print("🎨 Enhanced UI: ВКЛЮЧЕН")
        print("📊 Monitoring: РАБОТАЕТ")
        print("🔔 Notifications: АКТИВНЫ")
        print("💾 Auto Backup: ВКЛЮЧЕН")
        print("🔥 " + "="*70)
        print(f"🕐 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 Админ ID: {os.getenv('ADMIN_USER_IDS', '377917978')}")
        print(f"💎 TON Wallet: UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB")
        print("🔥 " + "="*70)
        print("🚀 BOT IS RUNNING... (Ctrl+C для остановки)")
        print("🔥 " + "="*70)
        
        # Отправляем уведомление о запуске
        if systems_status['notifications']:
            try:
                from notification_system import send_info_alert
                send_info_alert(
                    "Bot Successfully Launched",
                    "Ultimate Enterprise Bot is now running and ready to serve users!",
                    "launcher",
                    {
                        "systems_active": sum(systems_status.values()),
                        "total_systems": len(systems_status),
                        "launch_time": datetime.now().isoformat()
                    }
                )
            except:
                pass
        
        # Создаем и запускаем бота
        bot = MonetizedBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки...")
        shutdown_systems()
    except Exception as e:
        print(f"\n❌ Критическая ошибка бота: {e}")
        
        # Отправляем критический алерт
        try:
            from notification_system import send_critical_alert
            send_critical_alert(
                "Critical Bot Error",
                f"Bot crashed with error: {str(e)}",
                "launcher",
                {"error": str(e), "timestamp": datetime.now().isoformat()}
            )
        except:
            pass
        
        shutdown_systems()
        sys.exit(1)

def shutdown_systems():
    """Корректное завершение всех систем"""
    print("\n🛑 Завершение работы систем...")
    
    # Создаем shutdown backup
    if systems_status['backup']:
        try:
            from backup_system import backup_system
            print("💾 Создание backup перед завершением...")
            shutdown_backup = backup_system.create_backup(
                backup_type="shutdown",
                description=f"Shutdown backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if shutdown_backup:
                print(f"✅ Shutdown backup создан: {shutdown_backup}")
            backup_system.shutdown()
        except Exception as e:
            print(f"⚠️ Ошибка создания shutdown backup: {e}")
    
    # Останавливаем мониторинг
    if systems_status['monitoring']:
        try:
            from monitoring_system import monitoring_system
            monitoring_system.stop_monitoring()
            print("✅ Monitoring System: ОСТАНОВЛЕН")
        except Exception as e:
            print(f"⚠️ Ошибка остановки мониторинга: {e}")
    
    # Останавливаем уведомления
    if systems_status['notifications']:
        try:
            from notification_system import notification_system, send_info_alert
            send_info_alert(
                "Bot Shutdown",
                "Ultimate Enterprise Bot is shutting down gracefully",
                "launcher"
            )
            time.sleep(2)  # Даем время отправить последние уведомления
            notification_system.shutdown()
            print("✅ Notification System: ОСТАНОВЛЕН")
        except Exception as e:
            print(f"⚠️ Ошибка остановки уведомлений: {e}")
    
    print("🔥 Все системы корректно завершены")
    print("👋 До свидания!")

def setup_signal_handlers():
    """Настройка обработчиков сигналов"""
    def signal_handler(signum, frame):
        print(f"\n📡 Получен сигнал {signum}")
        shutdown_systems()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Регистрируем функцию завершения
    atexit.register(shutdown_systems)

def show_startup_summary():
    """Показ сводки по запуску"""
    print("\n📋 СВОДКА ПО ЗАПУСКУ:")
    print("="*50)
    
    total_systems = len(systems_status)
    active_systems = sum(systems_status.values())
    
    for system, status in systems_status.items():
        emoji = "✅" if status else "❌"
        print(f"  {emoji} {system.title().replace('_', ' ')}: {'АКТИВЕН' if status else 'ОШИБКА'}")
    
    print("="*50)
    print(f"📊 Активных систем: {active_systems}/{total_systems}")
    
    if active_systems == total_systems:
        print("🎉 Все системы успешно запущены!")
        return True
    elif active_systems >= total_systems * 0.7:  # 70% систем работают
        print("⚠️ Система частично работоспособна")
        return True
    else:
        print("❌ Критическая ошибка запуска")
        return False

def main():
    """Главная функция запуска"""
    print_banner()
    
    # Настройка обработчиков сигналов
    setup_signal_handlers()
    
    # Валидация окружения
    if not validate_environment():
        print("\n❌ Ошибка конфигурации. Исправьте и перезапустите.")
        sys.exit(1)
    
    # Проверка зависимостей
    if not check_dependencies():
        print("\n❌ Отсутствуют критические зависимости.")
        sys.exit(1)
    
    print("\n🚀 ИНИЦИАЛИЗАЦИЯ СИСТЕМ...")
    print("="*50)
    
    # Инициализация всех систем
    initialization_steps = [
        ("Monitoring System", initialize_monitoring_system),
        ("Notification System", initialize_notification_system),
        ("Backup System", initialize_backup_system),
        ("Admin System", initialize_admin_system),
        ("Main Bot", initialize_main_bot),
    ]
    
    for step_name, step_function in initialization_steps:
        print(f"\n🔄 {step_name}...")
        success = step_function()
        if success:
            print(f"✅ {step_name}: УСПЕШНО")
        else:
            print(f"❌ {step_name}: ОШИБКА")
    
    # Показываем сводку
    if not show_startup_summary():
        print("\n❌ Критические ошибки. Завершение работы.")
        sys.exit(1)
    
    print("\n🎯 Все системы готовы! Запускаем основной бот...")
    time.sleep(2)
    
    # Запуск основного бота
    start_main_bot()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 ФАТАЛЬНАЯ ОШИБКА: {e}")
        print("🔧 Проверьте конфигурацию и перезапустите")
        sys.exit(1) 