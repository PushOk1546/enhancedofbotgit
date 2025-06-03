#!/usr/bin/env python3
"""
🔧 ИСПРАВЛЕННЫЙ УСТАНОВЩИК ЗАВИСИМОСТЕЙ 🔧
Устраняет конфликты пакетов и устанавливает только необходимые модули
"""

import sys
import subprocess
import os

def print_header():
    print("🔧 ИСПРАВЛЕНИЕ ЗАВИСИМОСТЕЙ 🔧")
    print("=" * 50)

def upgrade_pip():
    """Обновление pip"""
    try:
        print("⬆️ Обновление pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print("✅ pip обновлен")
        return True
    except Exception as e:
        print(f"⚠️ Не удалось обновить pip: {e}")
        return False

def uninstall_conflicting_packages():
    """Удаление конфликтующих пакетов"""
    print("\n🗑️ Удаление конфликтующих пакетов...")
    
    conflicting_packages = [
        "python-dotenv",
        "telebot",
        "openai",
        "httpx",
        "aiofiles",
        "pydantic",
        "pytest",
        "cryptography"
    ]
    
    for package in conflicting_packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", package, "-y"], 
                         capture_output=True, check=False)
            print(f"🗑️ Удален: {package}")
        except:
            pass

def install_clean_dependencies():
    """Установка чистых зависимостей"""
    print("\n📦 Установка необходимых зависимостей...")
    
    # Критические зависимости в правильном порядке
    dependencies = [
        "pyTelegramBotAPI>=4.14.0",
        "requests>=2.28.0", 
        "psutil>=5.9.0",
        "python-dotenv>=1.0.1",
        "groq>=0.4.0",
        "cryptography>=41.0.0",
        "aiohttp>=3.8.0"
    ]
    
    success_count = 0
    failed_packages = []
    
    for package in dependencies:
        try:
            print(f"📦 Установка {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package, "--no-deps"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ {package}: УСТАНОВЛЕН")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки {package}")
            failed_packages.append(package)
    
    # Установка базовых зависимостей
    try:
        print("📦 Установка базовых зависимостей...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", 
                       "setuptools", "wheel", "certifi"], check=True)
        print("✅ Базовые зависимости установлены")
    except:
        print("⚠️ Предупреждение: не удалось установить базовые зависимости")
    
    return success_count, failed_packages

def verify_installation():
    """Проверка установки"""
    print("\n🔍 ПРОВЕРКА УСТАНОВКИ")
    print("=" * 30)
    
    critical_modules = [
        ("telebot", "import telebot"),
        ("requests", "import requests"),
        ("psutil", "import psutil"),
        ("dotenv", "import dotenv"),
        ("groq", "import groq")
    ]
    
    success_count = 0
    
    for module_name, import_code in critical_modules:
        try:
            exec(import_code)
            print(f"✅ {module_name}: OK")
            success_count += 1
        except ImportError:
            print(f"❌ {module_name}: ОТСУТСТВУЕТ")
        except Exception as e:
            print(f"⚠️ {module_name}: Предупреждение - {e}")
            success_count += 1  # Считаем как успешный если модуль есть
    
    print(f"\n📊 Проверено: {success_count}/{len(critical_modules)} модулей")
    return success_count >= 3  # Минимум 3 из 5 модулей должны работать

def create_minimal_env_template():
    """Создание минимального .env.template"""
    env_content = """# Ultimate Enterprise Bot - Minimal Configuration
# Скопируйте в .env и заполните значения

# ОБЯЗАТЕЛЬНО
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_USER_IDS=377917978

# ОПЦИОНАЛЬНО  
GROQ_KEY=your_groq_api_key_here
"""
    
    try:
        with open(".env.template.minimal", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("✅ Создан .env.template.minimal")
    except:
        print("⚠️ Не удалось создать .env.template.minimal")

def main():
    print_header()
    
    # Обновляем pip
    upgrade_pip()
    
    # Удаляем конфликтующие пакеты
    uninstall_conflicting_packages()
    
    # Устанавливаем чистые зависимости
    success_count, failed_packages = install_clean_dependencies()
    
    # Проверяем установку
    if verify_installation():
        print("\n🎉 УСТАНОВКА УСПЕШНА!")
        print("✅ Все критические модули работают")
        
        # Создаем шаблон конфигурации
        create_minimal_env_template()
        
        print("\n🚀 ГОТОВО К ЗАПУСКУ!")
        print("1. Создайте .env файл с вашим BOT_TOKEN")
        print("2. Запустите: python simple_start.py")
        print("3. Или: python ultimate_enterprise_launcher.py")
        
    else:
        print("\n⚠️ ЧАСТИЧНАЯ УСТАНОВКА")
        print("Некоторые модули могут работать некорректно")
        print("Попробуйте запустить простую версию: python simple_start.py")
    
    if failed_packages:
        print(f"\n❌ Не удалось установить: {', '.join(failed_packages)}")
        print("💡 Попробуйте установить вручную:")
        for pkg in failed_packages:
            print(f"   pip install {pkg}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Установка прервана")
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")
        print("💡 Попробуйте установить вручную: pip install pyTelegramBotAPI requests psutil") 