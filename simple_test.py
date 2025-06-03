#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест исправления парсинга survey steps без Unicode символов
"""

import sys
from pathlib import Path

# Добавляем путь к модулям бота
sys.path.insert(0, str(Path(__file__).parent))

from config import SURVEY_STEPS

def test_survey_parsing():
    """Простой тест парсинга callback данных"""
    print("=== TEST: Survey Step Parsing ===")
    
    def parse_callback(callback_data):
        """Новый исправленный метод парсинга"""
        if not callback_data.startswith("survey_"):
            raise ValueError(f"Invalid format: {callback_data}")
        
        # Убираем префикс "survey_"
        data_part = callback_data[7:]
        
        # Ищем последний underscore
        last_idx = data_part.rfind("_")
        if last_idx == -1:
            raise ValueError(f"Invalid format: {callback_data}")
        
        step = data_part[:last_idx]
        value = data_part[last_idx + 1:]
        
        return step, value
    
    # Тестовые случаи
    test_cases = [
        "survey_content_types_photos",
        "survey_content_types_all",
        "survey_price_range_budget",
        "survey_communication_style_flirty",
        "survey_notification_frequency_often"
    ]
    
    print("Testing callback parsing:")
    success = 0
    total = len(test_cases)
    
    for callback in test_cases:
        try:
            step, value = parse_callback(callback)
            
            if step in SURVEY_STEPS:
                print(f"  OK: {callback} -> step='{step}', value='{value}'")
                success += 1
            else:
                print(f"  FAIL: {callback} -> step='{step}' not found in SURVEY_STEPS")
        except Exception as e:
            print(f"  ERROR: {callback} -> {e}")
    
    print(f"\nResult: {success}/{total} tests passed")
    return success == total

def test_old_vs_new():
    """Сравнение старого и нового методов"""
    print("\n=== TEST: Old vs New Parsing ===")
    
    test_data = "survey_content_types_photos"
    print(f"Test data: {test_data}")
    
    # Старый метод (с ошибкой)
    parts = test_data.split("_", 2)
    old_step = parts[1] if len(parts) > 1 else ""
    old_value = parts[2] if len(parts) > 2 else ""
    
    print(f"Old method: step='{old_step}', value='{old_value}'")
    print(f"Old method result: step '{old_step}' in SURVEY_STEPS = {old_step in SURVEY_STEPS}")
    
    # Новый метод (исправленный)
    data_part = test_data[7:]  # Убираем "survey_"
    last_idx = data_part.rfind("_")
    new_step = data_part[:last_idx]
    new_value = data_part[last_idx + 1:]
    
    print(f"New method: step='{new_step}', value='{new_value}'")
    print(f"New method result: step '{new_step}' in SURVEY_STEPS = {new_step in SURVEY_STEPS}")
    
    return new_step in SURVEY_STEPS and old_step not in SURVEY_STEPS

if __name__ == "__main__":
    print("Survey Step Parsing Fix Test")
    print("=" * 40)
    
    test1_passed = test_old_vs_new()
    test2_passed = test_survey_parsing()
    
    print("\n" + "=" * 40)
    if test1_passed and test2_passed:
        print("SUCCESS: All tests passed!")
        print("The 'Unknown survey step: content' error should be fixed.")
    else:
        print("FAILURE: Some tests failed!")
        print("Additional fixes may be needed.") 