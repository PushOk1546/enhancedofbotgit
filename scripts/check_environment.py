#!/usr/bin/env python3
"""
Скрипт проверки окружения для OF Assistant Bot
Проверяет совместимость зависимостей с Python 3.11+
"""

import sys
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

def check_python_version():
    """Проверка версии Python"""
    print(f"🐍 Python версия: {sys.version}")
    if sys.version_info >= (3, 11):
        print("✅ Python версия совместима")
        return True
    else:
        print("❌ Требуется Python 3.11+")
        return False

def check_virtual_environment():
    """Проверка виртуального окружения"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Виртуальное окружение активировано")
        return True
    else:
        print("⚠️ Виртуальное окружение не активировано")
        return False

def check_dependencies():
    """Проверка основных зависимостей"""
    required_packages = [
        ('pyTelegramBotAPI', 'telebot'),
        ('groq', 'groq'),
        ('aiofiles', 'aiofiles'),
        ('asyncio-throttle', 'asyncio_throttle'),
        ('psutil', 'psutil'),
        ('pytest', 'pytest'),
        ('aiohttp', 'aiohttp'),
        ('pydantic', 'pydantic'),
        ('python-dotenv', 'dotenv'),
        ('loguru', 'loguru'),
    ]
    
    success_count = 0
    for package_name, module_name in required_packages:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
            success_count += 1
        except ImportError:
            print(f"❌ {package_name} - не установлен")
    
    print(f"📦 Установлено: {success_count}/{len(required_packages)} пакетов")
    return success_count == len(required_packages)

def check_project_structure():
    """Проверка структуры проекта"""
    required_files = [
        'main_bot.py',
        'groq_integration.py',
        'enhanced_logging.py',
        'utils.py',
        'models.py',
        'requirements.txt',
        'app/core/state.py',
        'app/core/cache.py',
        'app/core/queue.py',
        'app/core/monitoring.py',
        'app/core/error_handler.py'
    ]
    
    success_count = 0
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
            success_count += 1
        else:
            print(f"❌ {file_path} - отсутствует")
    
    print(f"📁 Найдено: {success_count}/{len(required_files)} файлов")
    return success_count == len(required_files)

def check_environment_variables():
    """Проверка переменных окружения"""
    import os
    
    env_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GROQ_API_KEY'
    ]
    
    success_count = 0
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var} установлена")
            success_count += 1
        else:
            print(f"⚠️ {var} не установлена")
    
    print(f"🔐 Переменных окружения: {success_count}/{len(env_vars)}")
    return success_count > 0  # Хотя бы одна должна быть установлена

async def check_async_functionality():
    """Проверка асинхронной функциональности"""
    try:
        await asyncio.sleep(0.1)
        print("✅ Асинхронность работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка асинхронности: {e}")
        return False

def run_quick_test():
    """Быстрый тест основных компонентов"""
    try:
        # Проверка импорта основных модулей
        import telebot
        import groq
        import aiofiles
        print("✅ Основные модули импортируются корректно")
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def main():
    """Основная функция"""
    print("🔧 Проверка окружения OF Assistant Bot")
    print("=" * 60)
    print(f"📅 Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Версия Python", check_python_version),
        ("Виртуальное окружение", check_virtual_environment),
        ("Зависимости", check_dependencies),
        ("Структура проекта", check_project_structure),
        ("Переменные окружения", check_environment_variables),
        ("Быстрый тест", run_quick_test),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append(False)
    
    # Асинхронный тест
    print(f"\n🔍 Асинхронность:")
    try:
        async_result = asyncio.run(check_async_functionality())
        results.append(async_result)
    except Exception as e:
        print(f"❌ Ошибка асинхронного теста: {e}")
        results.append(False)
    
    # Итоговый результат
    success_count = sum(results)
    total_tests = len(results)
    
    print("\n" + "=" * 60)
    print(f"📊 Результат: {success_count}/{total_tests} проверок прошли успешно")
    
    if success_count == total_tests:
        print("🎉 Окружение полностью готово к работе!")
        status = "ГОТОВО"
    elif success_count >= total_tests * 0.8:
        print("⚠️ Окружение готово с небольшими замечаниями")
        status = "ГОТОВО С ЗАМЕЧАНИЯМИ"
    else:
        print("❌ Окружение требует доработки")
        status = "ТРЕБУЕТ ДОРАБОТКИ"
    
    print(f"🏷️ Статус: {status}")
    print("=" * 60)
    
    return success_count >= total_tests * 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 