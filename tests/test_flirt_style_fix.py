#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки исправления ошибки "Unknown callback data: flirt_style_*"
"""

import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Добавляем путь к модулям бота
sys.path.insert(0, str(Path(__file__).parent))

from bot import BotManager
from config.config import FLIRT_STYLES

def test_flirt_styles_config():
    """Проверяем конфигурацию стилей флирта"""
    print("=== TEST: Flirt Styles Configuration ===")
    
    print(f"Available flirt styles: {list(FLIRT_STYLES.keys())}")
    
    # Проверяем структуру каждого стиля
    for style_name, style_info in FLIRT_STYLES.items():
        print(f"Style '{style_name}': {style_info}")
        
        # Проверяем обязательные поля
        required_fields = ['id', 'description', 'emoji']
        for field in required_fields:
            if field not in style_info:
                print(f"❌ Missing field '{field}' in style '{style_name}'")
                return False
    
    print("✅ All flirt styles have required fields")
    return True

def test_bot_has_flirt_handler():
    """Тест наличия обработчика flirt_style в боте"""
    print("\n=== TEST: Bot Flirt Style Handler ===")
    
    try:
        bot_manager = BotManager()
        
        # Проверяем наличие метода _handle_flirt_style
        has_flirt_handler = hasattr(bot_manager, '_handle_flirt_style')
        print(f"Bot has '_handle_flirt_style' method: {has_flirt_handler}")
        
        if has_flirt_handler:
            print("✅ Flirt style handler exists")
            
            # Проверяем наличие вспомогательных методов
            has_generate_method = hasattr(bot_manager, '_generate_flirt_message')
            has_create_prompt_method = hasattr(bot_manager, '_create_flirt_prompt')
            
            print(f"Has '_generate_flirt_message' method: {has_generate_method}")
            print(f"Has '_create_flirt_prompt' method: {has_create_prompt_method}")
            
            if has_generate_method and has_create_prompt_method:
                print("✅ All flirt handling methods exist")
                return True
            else:
                print("❌ Missing some flirt handling methods")
                return False
        else:
            print("❌ Flirt style handler missing")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bot flirt handler: {e}")
        return False

def test_callback_data_format():
    """Тест формата callback данных для стилей флирта"""
    print("\n=== TEST: Callback Data Format ===")
    
    expected_callbacks = []
    for style_name, style_info in FLIRT_STYLES.items():
        callback_data = f"flirt_style_{style_info['id']}"
        expected_callbacks.append(callback_data)
        print(f"Style '{style_name}' -> callback: '{callback_data}'")
    
    # Проверяем, что callback данные из логов совпадают с ожидаемыми
    log_callbacks = [
        "flirt_style_playful",
        "flirt_style_passionate", 
        "flirt_style_tender"
    ]
    
    print(f"\nExpected callbacks: {expected_callbacks}")
    print(f"Log callbacks: {log_callbacks}")
    
    missing_handlers = []
    for callback in log_callbacks:
        if callback not in expected_callbacks:
            missing_handlers.append(callback)
    
    if missing_handlers:
        print(f"❌ Missing handlers for: {missing_handlers}")
        return False
    else:
        print("✅ All callback data formats match")
        return True

def test_flirt_prompt_creation():
    """Тест создания промптов для флирта"""
    print("\n=== TEST: Flirt Prompt Creation ===")
    
    try:
        bot_manager = BotManager()
        
        # Создаем mock объекты
        mock_user = Mock()
        mock_user.model = 'smart'
        
        # Тестируем создание промптов для каждого стиля
        for style_name, style_info in FLIRT_STYLES.items():
            try:
                prompt = bot_manager._create_flirt_prompt(style_name, style_info['id'], mock_user)
                print(f"✅ Prompt created for style '{style_name}' (length: {len(prompt)})")
                
                # Проверяем, что промпт содержит нужные элементы
                if style_info['description'] in prompt and style_info['emoji'] in prompt:
                    print(f"   ✅ Prompt contains style description and emoji")
                else:
                    print(f"   ❌ Prompt missing style info")
                    return False
                    
            except Exception as e:
                print(f"❌ Error creating prompt for style '{style_name}': {e}")
                return False
        
        print("✅ All flirt prompts created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in prompt creation test: {e}")
        return False

def test_all_flirt_fixes():
    """Запуск всех тестов исправления flirt_style"""
    print("Testing flirt_style callback fixes")
    print("=" * 50)
    
    test1_passed = test_flirt_styles_config()
    test2_passed = test_bot_has_flirt_handler()
    test3_passed = test_callback_data_format()
    test4_passed = test_flirt_prompt_creation()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed and test3_passed and test4_passed:
        print("SUCCESS: All flirt_style tests passed!")
        print("✅ Flirt styles configuration is correct")
        print("✅ Bot has flirt_style callback handler")
        print("✅ Callback data formats match expectations")
        print("✅ Flirt prompts can be created successfully")
        print("\n🎉 The 'Unknown callback data: flirt_style_*' error should be fixed!")
        return True
    else:
        print("FAILURE: Some flirt_style tests failed!")
        print("❌ Additional fixes may be needed")
        return False

if __name__ == "__main__":
    test_all_flirt_fixes() 