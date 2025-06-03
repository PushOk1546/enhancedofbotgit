#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки исправлений:
1. HTML парсинг в _handle_ppv_button
2. Загрузка промптов с fallback
"""

import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import asyncio

# Добавляем путь к модулям бота
sys.path.insert(0, str(Path(__file__).parent))

from bot import BotManager
from state_manager import StateManager

def test_ppv_button_text():
    """Тест текста в кнопке PPV на корректность HTML"""
    print("=== TEST: PPV Button HTML Parsing ===")
    
    try:
        bot_manager = BotManager()
        
        # Проверяем, что метод существует
        if not hasattr(bot_manager, '_handle_ppv_button'):
            print("❌ _handle_ppv_button method not found")
            return False
        
        print("✅ _handle_ppv_button method exists")
        
        # Проверяем, что в коде нет опасных HTML тегов
        import inspect
        source = inspect.getsource(bot_manager._handle_ppv_button)
        
        # Ищем проблемные HTML теги
        dangerous_tags = ['<цена>', '<стиль>', '<команда>']
        found_issues = []
        
        for tag in dangerous_tags:
            if tag in source:
                found_issues.append(tag)
        
        if found_issues:
            print(f"❌ Found dangerous HTML tags: {found_issues}")
            return False
        else:
            print("✅ No dangerous HTML tags found in PPV button text")
            
        # Проверяем, что используются безопасные символы
        if '[цена]' in source and '[стиль]' in source:
            print("✅ Safe bracket notation used for parameters")
            return True
        else:
            print("❌ Parameters notation not found or incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Error testing PPV button: {e}")
        return False

async def test_prompt_loading():
    """Тест загрузки промптов с fallback"""
    print("\n=== TEST: Prompt Loading with Fallback ===")
    
    try:
        state_manager = StateManager()
        
        # Тест 1: Загрузка существующего файла
        existing_prompt = await state_manager.load_prompt('instructions')
        if existing_prompt:
            print("✅ Successfully loaded existing prompt: instructions.txt")
            print(f"   Length: {len(existing_prompt)} characters")
        else:
            print("⚠️ Could not load instructions.txt, but handled gracefully")
        
        # Тест 2: Загрузка несуществующего файла
        missing_prompt = await state_manager.load_prompt('nonexistent')
        if missing_prompt is None:
            print("✅ Correctly handled missing prompt file")
        else:
            print("❌ Should return None for missing prompt file")
            return False
        
        # Тест 3: Проверка возвращаемого типа
        welcome_prompt = await state_manager.load_prompt('welcome')
        if welcome_prompt is None or isinstance(welcome_prompt, str):
            print("✅ Correct return type (str or None)")
        else:
            print(f"❌ Incorrect return type: {type(welcome_prompt)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing prompt loading: {e}")
        return False

def test_state_manager_methods():
    """Тест методов StateManager"""
    print("\n=== TEST: StateManager Methods ===")
    
    try:
        state_manager = StateManager()
        
        # Проверяем наличие ключевых методов
        required_methods = ['load_prompt', 'get_user', 'add_to_history', 'save_data']
        missing_methods = []
        
        for method in required_methods:
            if not hasattr(state_manager, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        else:
            print("✅ All required methods exist")
        
        # Проверяем создание пользователя
        user = state_manager.get_user(12345)
        if user:
            print("✅ User creation works")
        else:
            print("❌ User creation failed")
            return False
        
        # Проверяем добавление в историю
        state_manager.add_to_history(12345, 'user', 'test message')
        if len(user.message_history) > 0:
            print("✅ Message history works")
        else:
            print("❌ Message history failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing StateManager: {e}")
        return False

async def test_all_fixes():
    """Запуск всех тестов исправлений"""
    print("Testing HTML parsing and prompt loading fixes")
    print("=" * 55)
    
    test1_passed = test_ppv_button_text()
    test2_passed = await test_prompt_loading()
    test3_passed = test_state_manager_methods()
    
    print("\n" + "=" * 55)
    if test1_passed and test2_passed and test3_passed:
        print("SUCCESS: All fixes tests passed!")
        print("✅ PPV button HTML parsing fixed")
        print("✅ Prompt loading with fallback works")
        print("✅ StateManager methods functional")
        print("\n🎉 Both critical errors should be fixed!")
        return True
    else:
        print("FAILURE: Some tests failed!")
        print("❌ Additional fixes may be needed")
        return False

if __name__ == "__main__":
    asyncio.run(test_all_fixes()) 