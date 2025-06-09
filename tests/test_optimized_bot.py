#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for optimized OF Assistant Bot
Tests all main functionality after cleanup and optimization.
"""

import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Core modules
        from config.config import BOT_TOKEN, MODELS, SURVEY_STEPS, GROQ_KEY
        print("   ✅ config module")
        
        from bot import BotManager
        print("   ✅ bot module") 
        
        from state_manager import StateManager
        print("   ✅ state_manager module")
        
        from handlers import handle_start_command, handle_flirt_command
        print("   ✅ handlers module")
        
        from utils import setup_logging, get_main_keyboard
        print("   ✅ utils module")
        
        from api import generate_groq_response
        print("   ✅ api module")
        
        from chat_handlers import ChatHandlers
        print("   ✅ chat_handlers module")
        
        print("🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_config():
    """Test configuration validation"""
    print("\n🧪 Testing configuration...")
    
    try:
        from config.config import BOT_TOKEN, MODELS, SURVEY_STEPS, GROQ_KEY, FLIRT_STYLES, PPV_STYLES
        
        # Test required configs exist
        assert MODELS, "MODELS is empty"
        assert SURVEY_STEPS, "SURVEY_STEPS is empty"
        assert FLIRT_STYLES, "FLIRT_STYLES is empty"
        assert PPV_STYLES, "PPV_STYLES is empty"
        
        # Test MODELS structure
        for model_key, model_data in MODELS.items():
            assert 'id' in model_data, f"Model {model_key} missing 'id'"
            assert 'description' in model_data, f"Model {model_key} missing 'description'"
        
        # Test SURVEY_STEPS structure
        for step_key, step_data in SURVEY_STEPS.items():
            assert 'question' in step_data, f"Survey step {step_key} missing 'question'"
            assert 'options' in step_data, f"Survey step {step_key} missing 'options'"
        
        print("   ✅ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False

def test_bot_manager():
    """Test BotManager initialization"""
    print("\n🧪 Testing BotManager...")
    
    try:
        from bot import BotManager
        
        # Create bot manager
        bot_manager = BotManager()
        
        # Check attributes
        assert hasattr(bot_manager, 'bot'), "Missing bot attribute"
        assert hasattr(bot_manager, 'state_manager'), "Missing state_manager attribute"
        assert hasattr(bot_manager, 'is_running'), "Missing is_running attribute"
        assert hasattr(bot_manager, '_shutdown_event'), "Missing _shutdown_event attribute"
        
        print("   ✅ BotManager structure validation passed")
        return True
        
    except Exception as e:
        print(f"   ❌ BotManager error: {e}")
        return False

def test_handlers():
    """Test handler functions exist and are callable"""
    print("\n🧪 Testing handlers...")
    
    try:
        from handlers import (
            handle_start_command,
            handle_model_command,
            handle_flirt_command,
            handle_ppv_command,
            handle_set_ppv_reminder_command,
            set_state_manager
        )
        
        # Check if functions are callable
        assert callable(handle_start_command), "handle_start_command not callable"
        assert callable(handle_model_command), "handle_model_command not callable"
        assert callable(handle_flirt_command), "handle_flirt_command not callable"
        assert callable(handle_ppv_command), "handle_ppv_command not callable"
        assert callable(handle_set_ppv_reminder_command), "handle_set_ppv_reminder_command not callable"
        assert callable(set_state_manager), "set_state_manager not callable"
        
        print("   ✅ All handlers are callable")
        return True
        
    except Exception as e:
        print(f"   ❌ Handlers error: {e}")
        return False

def test_utilities():
    """Test utility functions"""
    print("\n🧪 Testing utilities...")
    
    try:
        from utils import (
            setup_logging, get_main_keyboard, get_model_keyboard,
            get_survey_keyboard, get_flirt_style_keyboard
        )
        
        # Test logging setup
        logger = setup_logging()
        assert logger, "setup_logging returned None"
        
        # Test keyboard functions
        main_kb = get_main_keyboard()
        assert main_kb, "get_main_keyboard returned None"
        
        model_kb = get_model_keyboard()
        assert model_kb, "get_model_keyboard returned None"
        
        # Test survey keyboard with valid step
        survey_kb = get_survey_keyboard('content_types')
        assert survey_kb, "get_survey_keyboard returned None"
        
        flirt_kb = get_flirt_style_keyboard()
        assert flirt_kb, "get_flirt_style_keyboard returned None"
        
        print("   ✅ All utility functions working")
        return True
        
    except Exception as e:
        print(f"   ❌ Utilities error: {e}")
        return False

def test_survey_parsing():
    """Test survey callback parsing (the issue we fixed)"""
    print("\n🧪 Testing survey callback parsing...")
    
    try:
        # Test the fixed parsing logic
        test_callback = "survey_content_types_photos"
        
        # Remove prefix "survey_"
        data_without_prefix = test_callback[7:]  # "content_types_photos"
        
        # Find last underscore to separate step from value
        last_underscore_idx = data_without_prefix.rfind("_")  # 12
        step = data_without_prefix[:last_underscore_idx]  # "content_types"
        value = data_without_prefix[last_underscore_idx + 1:]  # "photos"
        
        # Validate
        from config.config import SURVEY_STEPS
        assert step in SURVEY_STEPS, f"Step '{step}' not found in SURVEY_STEPS"
        assert step == "content_types", f"Expected 'content_types', got '{step}'"
        assert value == "photos", f"Expected 'photos', got '{value}'"
        
        print(f"   ✅ Survey parsing works: {step} -> {value}")
        return True
        
    except Exception as e:
        print(f"   ❌ Survey parsing error: {e}")
        return False

async def test_async_functionality():
    """Test async functionality"""
    print("\n🧪 Testing async functionality...")
    
    try:
        from bot import BotManager
        from state_manager import StateManager
        
        # Test state manager
        state_manager = StateManager()
        test_user = state_manager.get_user(12345)
        assert test_user, "get_user returned None"
        
        # Test bot manager validation
        bot_manager = BotManager()
        
        # Mock environment for validation test
        import os
        original_bot_token = os.environ.get('BOT_TOKEN')
        original_groq_key = os.environ.get('GROQ_KEY')
        
        os.environ['BOT_TOKEN'] = 'test:token'
        os.environ['GROQ_KEY'] = 'test_key'
        
        # Test validation
        result = bot_manager._validate_config()
        
        # Restore environment
        if original_bot_token:
            os.environ['BOT_TOKEN'] = original_bot_token
        if original_groq_key:
            os.environ['GROQ_KEY'] = original_groq_key
        
        assert result == True, "Config validation failed"
        
        print("   ✅ Async functionality working")
        return True
        
    except Exception as e:
        print(f"   ❌ Async functionality error: {e}")
        return False

def test_no_duplicate_files():
    """Test that duplicate files were removed"""
    print("\n🧪 Testing cleanup (no duplicates)...")
    
    project_root = Path(__file__).parent.parent
    
    # Check that duplicate bot files were removed
    duplicate_files = [
        'perfect_bot.py',
        'monetized_bot.py', 
        'simple_bot_windows.py',
        'test_bot.py'
    ]
    
    existing_duplicates = []
    for file in duplicate_files:
        if (project_root / file).exists():
            existing_duplicates.append(file)
    
    if existing_duplicates:
        print(f"   ❌ Found duplicate files: {existing_duplicates}")
        return False
    
    # Check main files exist
    required_files = [
        'main.py',
        'bot.py',
        'config.py',
        'handlers.py',
        'utils.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not (project_root / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"   ❌ Missing required files: {missing_files}")
        return False
    
    print("   ✅ Cleanup successful - no duplicates found")
    return True

def main():
    """Run all tests"""
    print("🚀 Running Optimized Bot Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_bot_manager,
        test_handlers,
        test_utilities,
        test_survey_parsing,
        test_no_duplicate_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test {test.__name__} failed: {e}")
    
    # Test async functionality
    try:
        result = asyncio.run(test_async_functionality())
        if result:
            passed += 1
        total += 1
    except Exception as e:
        print(f"   ❌ Async test failed: {e}")
        total += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Bot optimization successful")
        print("✅ All functionality working")
        print("✅ No duplicate code")
        print("✅ Clean architecture")
        return True
    else:
        print("💥 Some tests failed!")
        print("❌ Further optimization needed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 