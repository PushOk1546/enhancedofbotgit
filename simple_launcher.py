#!/usr/bin/env python3
"""
🚀 SIMPLE LAUNCHER FOR UNIFIED BOT 🚀
Единый простой запускающий скрипт
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Простой launcher для unified бота"""
    print("🚀 OF Assistant Bot Simple Launcher")
    print("=" * 50)
    
    # Переходим в корневую директорию проекта
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"📂 Рабочая директория: {project_root}")
    
    # Проверяем наличие основных файлов
    required_files = ["unified_bot_deepseek.py", "config.py", "deepseek_integration.py"]
    missing_files = []
    
    for file_name in required_files:
        if not (project_root / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print("❌ Отсутствуют необходимые файлы:")
        for file_name in missing_files:
            print(f"   • {file_name}")
        print("\n💡 Убедитесь, что все файлы проекта находятся в правильном месте")
        return 1
    
    print("✅ Все необходимые файлы найдены")
    
    # Выбор режима запуска
    print("\n🔥 Выберите режим запуска:")
    print("1. DeepSeek Bot (рекомендуется) - с поддержкой NSFW контента")
    print("2. Unified Bot - оригинальная версия с Groq")
    print("3. Main Bot - базовая версия")
    print("4. Выход")
    
    try:
        choice = input("\nВведите номер (1-4): ").strip()
        
        if choice == "1":
            print("\n🔥 Запуск DeepSeek Bot...")
            print("🎭 Поддержка NSFW контента активна!")
            return subprocess.run([sys.executable, "unified_bot_deepseek.py"]).returncode
            
        elif choice == "2":
            if (project_root / "unified_bot.py").exists():
                print("\n🚀 Запуск Unified Bot (Groq)...")
                return subprocess.run([sys.executable, "unified_bot.py"]).returncode
            else:
                print("❌ Файл unified_bot.py не найден")
                return 1
            
        elif choice == "3":
            if (project_root / "main_bot.py").exists():
                print("\n🚀 Запуск Main Bot...")
                return subprocess.run([sys.executable, "main_bot.py"]).returncode
            else:
                print("❌ Файл main_bot.py не найден")
                return 1
                
        elif choice == "4":
            print("👋 До свидания!")
            return 0
            
        else:
            print("❌ Неверный выбор")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Запуск отменен пользователем")
        return 0
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 