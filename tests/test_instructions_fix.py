#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки исправления ошибки KeyError: 'history' в send_navigation_instructions
"""

import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import asyncio

# Добавляем путь к модулям бота
sys.path.insert(0, str(Path(__file__).parent))

from handlers import send_navigation_instructions
from state_manager import StateManager
from models import UserState

def test_instructions_template_placeholders():
    """Тест проверки плейсхолдеров в шаблоне instructions.txt"""
    print("=== TEST: Instructions Template Placeholders ===")
    
    try:
        instructions_file = Path("prompts/instructions.txt")
        if not instructions_file.exists():
            print("❌ instructions.txt file not found")
            return False
        
        with open(instructions_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие плейсхолдеров
        has_preferences = '{preferences}' in content
        has_history = '{history}' in content
        
        print(f"Template has {{preferences}} placeholder: {has_preferences}")
        print(f"Template has {{history}} placeholder: {has_history}")
        
        if has_preferences and has_history:
            print("✅ Both required placeholders found in template")
            return True
        else:
            print("❌ Missing required placeholders")
            return False
            
    except Exception as e:
        print(f"❌ Error checking template: {e}")
        return False

async def test_send_navigation_instructions():
    """Тест функции send_navigation_instructions с mock данными"""
    print("\n=== TEST: Send Navigation Instructions ===")
    
    try:
        # Создаем mock bot
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()
        
        # Создаем mock user_state
        mock_user_state = Mock()
        mock_user_state.preferences.completed_survey = True
        mock_user_state.preferences.content_types = ['photos', 'videos']
        mock_user_state.preferences.price_range = 'medium'
        mock_user_state.message_history = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there!'},
            {'role': 'user', 'content': 'How are you?'}
        ]
        mock_user_state.model = 'smart'
        
        # Тест 1: Проверяем, что функция существует
        import inspect
        if not callable(send_navigation_instructions):
            print("❌ send_navigation_instructions is not callable")
            return False
        
        print("✅ send_navigation_instructions function exists")
        
        # Тест 2: Проверяем количество параметров
        sig = inspect.signature(send_navigation_instructions)
        params = list(sig.parameters.keys())
        expected_params = ['bot', 'chat_id', 'user_state']
        
        if params == expected_params:
            print("✅ Function has correct parameters")
        else:
            print(f"❌ Expected params: {expected_params}, got: {params}")
            return False
        
        # Тест 3: Проверяем исходный код на наличие format с обоими параметрами
        source = inspect.getsource(send_navigation_instructions)
        has_format_call = 'format(preferences=preferences, history=history)' in source
        
        if has_format_call:
            print("✅ format() call includes both preferences and history")
            return True
        else:
            print("❌ format() call missing required parameters")
            # Дополнительная проверка
            if 'format(' in source:
                print("   Found format() call but with wrong parameters")
            else:
                print("   No format() call found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing navigation instructions: {e}")
        return False

def test_user_state_history_access():
    """Тест доступа к истории сообщений пользователя"""
    print("\n=== TEST: User State History Access ===")
    
    try:
        # Создаем реальный UserState объект
        user_state = UserState()
        
        # Проверяем наличие атрибута message_history
        if not hasattr(user_state, 'message_history'):
            print("❌ UserState has no message_history attribute")
            return False
        
        print("✅ UserState has message_history attribute")
        
        # Проверяем что это список
        if not isinstance(user_state.message_history, list):
            print(f"❌ message_history is not a list, got: {type(user_state.message_history)}")
            return False
        
        print("✅ message_history is a list")
        
        # Добавляем тестовое сообщение
        test_message = {
            'role': 'user',
            'content': 'test message',
            'timestamp': '2025-06-02T23:00:00'
        }
        user_state.message_history.append(test_message)
        
        if len(user_state.message_history) == 1:
            print("✅ Can add messages to history")
            return True
        else:
            print("❌ Failed to add message to history")
            return False
            
    except Exception as e:
        print(f"❌ Error testing user state history: {e}")
        return False

async def test_all_instructions_fixes():
    """Запуск всех тестов исправления instructions"""
    print("Testing instructions template formatting fixes")
    print("=" * 60)
    
    test1_passed = test_instructions_template_placeholders()
    test2_passed = await test_send_navigation_instructions()
    test3_passed = test_user_state_history_access()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed and test3_passed:
        print("SUCCESS: All instructions tests passed!")
        print("✅ Template has correct placeholders")
        print("✅ Function uses both preferences and history")
        print("✅ User state history access works")
        print("\n🎉 The KeyError: 'history' should be fixed!")
        return True
    else:
        print("FAILURE: Some tests failed!")
        print("❌ Additional fixes may be needed")
        return False

if __name__ == "__main__":
    asyncio.run(test_all_instructions_fixes()) 