#!/usr/bin/env python3
"""
🚀 АВТОМАТИЧЕСКИЙ УСТАНОВЩИК ЗАВИСИМОСТЕЙ 🚀
Ultimate Enterprise Bot - Dependency Installer

Автоматически устанавливает все необходимые модули и зависимости
для корректной работы Ultimate Enterprise Telegram Bot
"""

import sys
import os
import subprocess
import platform
from packaging import version

# Минимальная версия Python
MIN_PYTHON_VERSION = "3.8.0"

# Критические зависимости
CRITICAL_DEPENDENCIES = [
    "pyTelegramBotAPI>=4.14.0",
    "requests>=2.28.0", 
    "psutil>=5.9.0",
    "packaging>=21.0"
]

# Опциональные зависимости  
OPTIONAL_DEPENDENCIES = [
    "groq>=0.4.0",
    "python-dotenv>=0.19.0",
    "cryptography>=3.4.0",
    "aiohttp>=3.8.0"
]

def print_banner():
    """Красивый баннер"""
    banner = """
🔥═══════════════════════════════════════════════════════════════════════════🔥
║                                                                           ║
║             🚀 ULTIMATE ENTERPRISE BOT INSTALLER 🚀                     ║
║                                                                           ║
║  Автоматическая установка всех зависимостей для                          ║
║  корректной работы Enterprise Telegram Bot системы                       ║
║                                                                           ║
🔥═══════════════════════════════════════════════════════════════════════════🔥
    """
    print(banner)

def check_python_version():
    """Проверка версии Python"""
    current_version = platform.python_version()
    print(f"🐍 Проверка версии Python: {current_version}")
    
    if version.parse(current_version) < version.parse(MIN_PYTHON_VERSION):
        print(f"❌ Ошибка: Требуется Python {MIN_PYTHON_VERSION}+ (текущая версия: {current_version})")
        print("💡 Обновите Python: https://www.python.org/downloads/")
        return False
    
    print(f"✅ Python версия {current_version} поддерживается")
    return True

def check_pip():
    """Проверка pip"""
    try:
        import pip
        print(f"✅ pip обнаружен: версия {pip.__version__}")
        return True
    except ImportError:
        print("❌ pip не найден")
        print("💡 Установите pip: https://pip.pypa.io/en/stable/installation/")
        return False

def install_package(package_name):
    """Установка пакета через pip"""
    try:
        print(f"📦 Установка {package_name}...")
        
        # Используем subprocess для установки
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ {package_name}: УСТАНОВЛЕН")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package_name}: {e}")
        print(f"   Вывод: {e.stdout}")
        print(f"   Ошибки: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка при установке {package_name}: {e}")
        return False

def upgrade_pip():
    """Обновление pip"""
    try:
        print("⬆️ Обновление pip...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            check=True
        )
        print("✅ pip обновлен")
        return True
    except Exception as e:
        print(f"⚠️ Не удалось обновить pip: {e}")
        return False

def check_installed_packages():
    """Проверка уже установленных пакетов"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        installed_packages = {}
        for line in result.stdout.split('\n')[2:]:  # Пропускаем заголовки
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    installed_packages[parts[0].lower()] = parts[1]
        
        return installed_packages
    except Exception as e:
        print(f"⚠️ Не удалось получить список пакетов: {e}")
        return {}

def install_dependencies():
    """Установка всех зависимостей"""
    print("\n🔧 УСТАНОВКА ЗАВИСИМОСТЕЙ")
    print("="*50)
    
    # Обновляем pip
    upgrade_pip()
    
    # Получаем список установленных пакетов
    installed = check_installed_packages()
    
    success_count = 0
    failed_packages = []
    
    print("\n📦 Установка критических зависимостей...")
    for package in CRITICAL_DEPENDENCIES:
        package_name = package.split(">=")[0]
        
        if package_name.lower() in installed:
            print(f"⚡ {package_name}: УЖЕ УСТАНОВЛЕН (версия {installed[package_name.lower()]})")
            success_count += 1
        else:
            if install_package(package):
                success_count += 1
            else:
                failed_packages.append(package)
    
    print("\n📦 Установка опциональных зависимостей...")
    optional_success = 0
    for package in OPTIONAL_DEPENDENCIES:
        package_name = package.split(">=")[0]
        
        if package_name.lower() in installed:
            print(f"⚡ {package_name}: УЖЕ УСТАНОВЛЕН (версия {installed[package_name.lower()]})")
            optional_success += 1
        else:
            if install_package(package):
                optional_success += 1
            else:
                print(f"⚠️ {package_name}: не удалось установить (опционально)")
    
    # Отчет об установке
    print("\n" + "="*50)
    print("📊 ОТЧЕТ ОБ УСТАНОВКЕ:")
    print(f"✅ Критические зависимости: {success_count}/{len(CRITICAL_DEPENDENCIES)}")
    print(f"✅ Опциональные зависимости: {optional_success}/{len(OPTIONAL_DEPENDENCIES)}")
    
    if failed_packages:
        print("\n❌ Не удалось установить:")
        for package in failed_packages:
            print(f"  - {package}")
        return False
    
    if success_count == len(CRITICAL_DEPENDENCIES):
        print("\n🎉 Все критические зависимости установлены успешно!")
        return True
    else:
        print(f"\n❌ Установлено только {success_count}/{len(CRITICAL_DEPENDENCIES)} критических зависимостей")
        return False

def verify_installation():
    """Проверка корректности установки"""
    print("\n🔍 ПРОВЕРКА УСТАНОВКИ")
    print("="*50)
    
    verification_tests = [
        ("telebot", "import telebot; print('✅ PyTelegramBotAPI работает')"),
        ("requests", "import requests; print('✅ Requests работает')"),
        ("psutil", "import psutil; print('✅ PSUtil работает')"),
        ("json", "import json; print('✅ JSON работает')"),
        ("datetime", "import datetime; print('✅ DateTime работает')"),
        ("threading", "import threading; print('✅ Threading работает')"),
        ("sqlite3", "import sqlite3; print('✅ SQLite3 работает')"),
    ]
    
    success_count = 0
    
    for module_name, test_code in verification_tests:
        try:
            exec(test_code)
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}: {e}")
    
    print(f"\n📊 Проверено модулей: {success_count}/{len(verification_tests)}")
    
    if success_count == len(verification_tests):
        print("🎉 Все модули работают корректно!")
        return True
    else:
        print("⚠️ Некоторые модули работают некорректно")
        return False

def create_requirements_txt():
    """Создание requirements.txt файла"""
    print("\n📝 Создание requirements.txt...")
    
    requirements_content = """# Ultimate Enterprise Bot - Requirements
# Критические зависимости
pyTelegramBotAPI>=4.14.0
requests>=2.28.0
psutil>=5.9.0
packaging>=21.0

# Опциональные зависимости
groq>=0.4.0
python-dotenv>=0.19.0
cryptography>=3.4.0
aiohttp>=3.8.0

# Системные зависимости (встроенные в Python)
# sqlite3
# json
# datetime
# threading
# hashlib
# time
# os
# sys
"""
    
    try:
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
        print("✅ requirements.txt создан")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания requirements.txt: {e}")
        return False

def create_env_template():
    """Создание шаблона .env файла"""
    print("📝 Создание .env.template...")
    
    env_template = """# Ultimate Enterprise Bot - Environment Variables Template
# Скопируйте этот файл в .env и заполните значения

# === ОБЯЗАТЕЛЬНЫЕ НАСТРОЙКИ ===
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_USER_IDS=your_admin_user_id_here

# === ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ===
GROQ_KEY=your_groq_api_key_here

# Email уведомления
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ADMIN_EMAILS=admin@yourdomain.com

# Webhook для команды
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# TON интеграция  
TON_WALLET_ADDRESS=your_ton_wallet_address_here

# Дополнительные настройки
DEBUG=false
LOG_LEVEL=INFO
"""
    
    try:
        with open(".env.template", "w", encoding="utf-8") as f:
            f.write(env_template)
        print("✅ .env.template создан")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания .env.template: {e}")
        return False

def show_next_steps():
    """Показ следующих шагов"""
    print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("="*50)
    print("1. 📝 Настройте переменные окружения:")
    print("   - Скопируйте .env.template в .env")
    print("   - Заполните BOT_TOKEN и ADMIN_USER_IDS")
    print("   - Опционально: заполните остальные настройки")
    print("")
    print("2. 🚀 Запустите бота:")
    print("   python ultimate_enterprise_launcher.py")
    print("")
    print("3. 📚 Изучите документацию:")
    print("   - ULTIMATE_DEPLOYMENT_GUIDE.md")
    print("   - README.md")
    print("")
    print("4. 🔧 Для troubleshooting:")
    print("   - Проверьте логи в консоли")
    print("   - Используйте команду /health_check в боте")
    print("")
    print("🎉 Установка завершена! Удачного использования!")

def main():
    """Главная функция установщика"""
    print_banner()
    
    # Проверка системы
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    # Установка зависимостей
    if not install_dependencies():
        print("\n❌ Критическая ошибка установки зависимостей!")
        print("💡 Попробуйте установить вручную:")
        print("pip install pyTelegramBotAPI requests psutil")
        sys.exit(1)
    
    # Проверка установки
    if not verify_installation():
        print("\n⚠️ Некоторые модули работают некорректно")
        print("Система может работать нестабильно")
    
    # Создание конфигурационных файлов
    create_requirements_txt()
    create_env_template()
    
    # Показ следующих шагов
    show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Установка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка установщика: {e}")
        sys.exit(1) 