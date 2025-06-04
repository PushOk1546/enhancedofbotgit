#!/usr/bin/env python3
"""
🧪 ТЕСТ ПОКРЫТИЯ ВСЕХ CALLBACK ОБРАБОТЧИКОВ
Проверяет что все кнопки имеют соответствующие обработчики
"""

import sys
import re
from pathlib import Path

def extract_callback_data_from_utils():
    """Извлекает все callback_data из utils.py"""
    utils_file = Path("utils.py")
    
    if not utils_file.exists():
        print("❌ Файл utils.py не найден")
        return []
    
    content = utils_file.read_text(encoding='utf-8')
    
    # Ищем все callback_data="..." 
    callback_pattern = r'callback_data=["\'](.*?)["\']'
    callbacks = re.findall(callback_pattern, content)
    
    # Фильтруем динамические callback (содержащие f-строки и переменные)
    static_callbacks = []
    for callback in callbacks:
        # Пропускаем те что содержат переменные
        if not any(char in callback for char in ['{', '}', '_', 'f"', "f'"]):
            static_callbacks.append(callback)
        # Добавляем статические части из шаблонов
        elif callback.startswith(('model_', 'flirt_style_', 'ppv_style_', 'survey_', 'chat_')):
            continue  # Эти обрабатываются через startswith
        else:
            static_callbacks.append(callback)
    
    return static_callbacks

def extract_handlers_from_bot():
    """Извлекает все обработчики callback из bot.py"""
    bot_file = Path("bot.py")
    
    if not bot_file.exists():
        print("❌ Файл bot.py не найден")
        return []
    
    content = bot_file.read_text(encoding='utf-8')
    
    # Ищем все elif data == "..." и data == "..."
    handler_pattern = r'data == ["\'](.*?)["\']'
    handlers = re.findall(handler_pattern, content)
    
    # Также ищем startswith обработчики
    startswith_pattern = r'data\.startswith\(["\'](.*?)["\']'
    startswith_handlers = re.findall(startswith_pattern, content)
    
    return handlers, startswith_handlers

def main():
    """Главная функция тестирования покрытия callback"""
    print("🧪 ТЕСТ ПОКРЫТИЯ CALLBACK ОБРАБОТЧИКОВ")
    print("=" * 55)
    
    # Извлекаем callback из utils.py
    callback_data = extract_callback_data_from_utils()
    print(f"\n📋 Найдено callback в utils.py: {len(callback_data)}")
    for callback in sorted(callback_data):
        print(f"   📄 {callback}")
    
    # Извлекаем обработчики из bot.py
    handlers, startswith_handlers = extract_handlers_from_bot()
    print(f"\n🔧 Найдено обработчиков в bot.py: {len(handlers)}")
    for handler in sorted(handlers):
        print(f"   ⚙️ {handler}")
    
    print(f"\n🔧 Startswith обработчики: {len(startswith_handlers)}")
    for handler in sorted(startswith_handlers):
        print(f"   ⚙️ {handler}*")
    
    # Проверяем покрытие
    print(f"\n🔍 АНАЛИЗ ПОКРЫТИЯ:")
    missing_handlers = []
    covered_handlers = []
    
    for callback in callback_data:
        # Проверяем точное совпадение
        if callback in handlers:
            covered_handlers.append(callback)
            print(f"   ✅ {callback}")
        # Проверяем startswith совпадения
        elif any(callback.startswith(prefix) for prefix in startswith_handlers):
            covered_handlers.append(callback)
            matching_prefix = next(prefix for prefix in startswith_handlers if callback.startswith(prefix))
            print(f"   ✅ {callback} (через {matching_prefix}*)")
        else:
            missing_handlers.append(callback)
            print(f"   ❌ {callback}")
    
    # Итоги
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"✅ Покрыто: {len(covered_handlers)}/{len(callback_data)}")
    print(f"❌ Отсутствует: {len(missing_handlers)}")
    print(f"📈 Покрытие: {(len(covered_handlers)/len(callback_data)*100):.1f}%")
    
    if missing_handlers:
        print(f"\n⚠️ НЕДОСТАЮЩИЕ ОБРАБОТЧИКИ:")
        for missing in missing_handlers:
            print(f"   🚨 {missing}")
        return False
    else:
        print(f"\n🎉 ВСЕ CALLBACK ПОКРЫТЫ ОБРАБОТЧИКАМИ!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 