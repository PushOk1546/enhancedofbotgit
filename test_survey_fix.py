#!/usr/bin/env python3
"""
Тест для проверки исправления обработки шагов опроса.
Этот скрипт проверяет правильность парсинга callback данных.
"""

import sys
import os
from pathlib import Path

# Добавляем путь к модулям бота
sys.path.insert(0, str(Path(__file__).parent))

from config import SURVEY_STEPS
from utils import get_survey_keyboard

def test_survey_parsing():
    """Тестирование парсинга данных опроса"""
    print("🧪 Тестирование исправления парсинга шагов опроса\n")
    
    def parse_survey_callback(callback_data):
        """Имитация исправленного парсинга из _handle_survey_step"""
        print(f"📥 Обрабатываем callback: '{callback_data}'")
        
        if not callback_data.startswith("survey_"):
            raise ValueError(f"Invalid survey callback format: {callback_data}")
        
        # Убираем префикс "survey_"
        data_without_prefix = callback_data[7:]  # len("survey_") = 7
        
        # Ищем последний underscore чтобы отделить value от step
        last_underscore_idx = data_without_prefix.rfind("_")
        if last_underscore_idx == -1:
            raise ValueError(f"Invalid survey callback data format: {callback_data}")
        
        step = data_without_prefix[:last_underscore_idx]
        value = data_without_prefix[last_underscore_idx + 1:]
        
        print(f"   ✅ Step: '{step}'")
        print(f"   ✅ Value: '{value}'")
        
        if step not in SURVEY_STEPS:
            print(f"   ❌ Ошибка: неизвестный шаг '{step}'")
            print(f"   📋 Доступные шаги: {list(SURVEY_STEPS.keys())}")
            return False
        
        print(f"   ✅ Шаг '{step}' найден в конфигурации")
        return True
    
    # Тестируем все возможные callback данные
    test_cases = [
        "survey_content_types_photos",
        "survey_content_types_videos", 
        "survey_content_types_messages",
        "survey_content_types_all",
        "survey_price_range_budget",
        "survey_price_range_medium",
        "survey_price_range_premium", 
        "survey_price_range_various",
        "survey_communication_style_flirty",
        "survey_communication_style_friendly",
        "survey_communication_style_professional",
        "survey_communication_style_mixed",
        "survey_notification_frequency_often",
        "survey_notification_frequency_daily",
        "survey_notification_frequency_occasional",
        "survey_notification_frequency_rarely"
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for callback_data in test_cases:
        try:
            success = parse_survey_callback(callback_data)
            if success:
                success_count += 1
            print()
        except Exception as e:
            print(f"   ❌ Исключение: {e}\n")
    
    print(f"📊 Результаты тестирования:")
    print(f"   ✅ Успешно: {success_count}/{total_count}")
    print(f"   ❌ Ошибок: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 Все тесты прошли успешно!")
        return True
    else:
        print("💥 Некоторые тесты провалились!")
        return False

def test_keyboard_generation():
    """Тестирование генерации клавиатур для опроса"""
    print("\n🧪 Тестирование генерации клавиатур опроса\n")
    
    for step_name in SURVEY_STEPS.keys():
        print(f"📋 Генерируем клавиатуру для шага: '{step_name}'")
        try:
            keyboard = get_survey_keyboard(step_name)
            print(f"   ✅ Клавиатура создана с {len(keyboard.keyboard)} кнопками")
            
            # Проверяем callback данные в кнопках
            for row in keyboard.keyboard:
                for button in row:
                    callback_data = button.callback_data
                    print(f"      🔗 Callback: {callback_data}")
                    
                    # Проверяем формат
                    expected_prefix = f"survey_{step_name}_"
                    if not callback_data.startswith(expected_prefix):
                        print(f"      ❌ Неверный формат callback данных!")
                        return False
            
            print(f"   ✅ Все callback данные корректны\n")
            
        except Exception as e:
            print(f"   ❌ Ошибка при создании клавиатуры: {e}\n")
            return False
    
    print("🎉 Все клавиатуры сгенерированы корректно!")
    return True

def test_old_vs_new_parsing():
    """Сравнение старого и нового способа парсинга"""
    print("\n🔄 Сравнение старого и нового парсинга\n")
    
    test_callback = "survey_content_types_photos"
    
    print(f"📝 Тестовые данные: '{test_callback}'\n")
    
    # Старый способ (с ошибкой)
    print("❌ Старый способ парсинга:")
    parts = test_callback.split("_", 2)
    if len(parts) >= 3:
        old_step = parts[1]  # "content"
        old_value = parts[2]  # "types_photos"
        print(f"   Step: '{old_step}' (неверно)")
        print(f"   Value: '{old_value}' (неверно)")
        print(f"   Результат: '{old_step}' не найден в SURVEY_STEPS ❌\n")
    
    # Новый способ (исправленный)
    print("✅ Новый способ парсинга:")
    data_without_prefix = test_callback[7:]  # "content_types_photos"
    last_underscore_idx = data_without_prefix.rfind("_")  # 12
    new_step = data_without_prefix[:last_underscore_idx]  # "content_types"
    new_value = data_without_prefix[last_underscore_idx + 1:]  # "photos"
    
    print(f"   Step: '{new_step}' (верно)")
    print(f"   Value: '{new_value}' (верно)")
    
    if new_step in SURVEY_STEPS:
        print(f"   Результат: '{new_step}' найден в SURVEY_STEPS ✅")
        return True
    else:
        print(f"   Результат: '{new_step}' НЕ найден в SURVEY_STEPS ❌")
        return False

if __name__ == "__main__":
    print("🔧 Тестирование исправления ошибки 'ValueError: Unknown survey step: content'\n")
    
    all_tests_passed = True
    
    # Запускаем все тесты
    all_tests_passed &= test_old_vs_new_parsing()
    all_tests_passed &= test_keyboard_generation()
    all_tests_passed &= test_survey_parsing()
    
    print("\n" + "="*60)
    if all_tests_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Исправление работает корректно")
        print("✅ Ошибка 'Unknown survey step: content' должна быть устранена")
    else:
        print("💥 НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛИЛИСЬ!")
        print("❌ Требуются дополнительные исправления")
    
    print("="*60) 