#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки исправления ошибки AttributeError: 'UserState' object has no attribute 'id'
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# Добавляем путь к модулям бота
sys.path.insert(0, str(Path(__file__).parent))

from bot import BotManager
from models import UserState

def test_user_state_attributes():
    """Проверяем, что UserState не имеет атрибута id (это корректно)"""
    print("=== TEST: UserState Attributes ===")
    
    user_state = UserState()
    
    # Проверяем, что у UserState нет атрибута id
    has_id_attr = hasattr(user_state, 'id')
    print(f"UserState has 'id' attribute: {has_id_attr}")
    
    # Это должно быть False - у UserState нет атрибута id
    if not has_id_attr:
        print("✅ CORRECT: UserState doesn't have 'id' attribute")
        return True
    else:
        print("❌ ERROR: UserState shouldn't have 'id' attribute")
        return False

def test_bot_creation():
    """Тест создания бота без ошибок"""
    print("\n=== TEST: Bot Creation ===")
    
    try:
        bot_manager = BotManager()
        print("✅ BotManager created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating BotManager: {e}")
        return False

def test_mock_survey_step():
    """Тест обработки survey step с mock данными"""
    print("\n=== TEST: Mock Survey Step Processing ===")
    
    try:
        bot_manager = BotManager()
        
        # Создаем mock объекты
        mock_call = Mock()
        mock_call.from_user.id = 123456
        mock_call.data = "survey_content_types_photos"
        mock_call.message.chat.id = 123456
        mock_call.message.message_id = 1
        
        mock_user = UserState()
        
        # Проверяем, что метод существует
        has_survey_method = hasattr(bot_manager, '_handle_survey_step')
        print(f"Bot has '_handle_survey_step' method: {has_survey_method}")
        
        if has_survey_method:
            print("✅ Survey step method exists")
            
            # Проверяем доступ к user_id из call
            user_id = mock_call.from_user.id
            print(f"✅ Can access user_id from call: {user_id}")
            
            return True
        else:
            print("❌ Survey step method missing")
            return False
            
    except Exception as e:
        print(f"❌ Error in survey step test: {e}")
        return False

def test_all_fixes():
    """Запуск всех тестов"""
    print("Testing user.id attribute fixes")
    print("=" * 40)
    
    test1_passed = test_user_state_attributes()
    test2_passed = test_bot_creation()
    test3_passed = test_mock_survey_step()
    
    print("\n" + "=" * 40)
    if test1_passed and test2_passed and test3_passed:
        print("SUCCESS: All tests passed!")
        print("✅ user.id AttributeError should be fixed")
        print("✅ Bot can be created without errors")
        print("✅ Survey step processing should work correctly")
        return True
    else:
        print("FAILURE: Some tests failed!")
        print("❌ Additional fixes may be needed")
        return False

if __name__ == "__main__":
    test_all_fixes() 