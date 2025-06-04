#!/usr/bin/env python3
"""
Быстрый тест основной функциональности бота для релиза.
Проверяет что все ключевые компоненты работают без запуска Telegram.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_core_imports():
    """Тест импорта основных модулей"""
    print("🔍 Тестируем импорты...")
    
    try:
        # Core modules
        from src.core.exceptions import BotException, ValidationError
        from src.core.validators import ValidatedUser, ValidatedMessage
        from src.core.rate_limiter import RateLimiter
        from src.core.error_handlers import ErrorHandler
        from src.core.logging_config import setup_logging
        from src.models.improved_models import UserState, UserPreferences
        print("✅ Все core модули импортированы успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_user_validation():
    """Тест валидации пользователей"""
    print("🔍 Тестируем валидацию пользователей...")
    
    try:
        from src.core.validators import ValidatedUser
        
        # Валидный пользователь
        user = ValidatedUser(
            user_id=123456789,
            username="test_user",
            first_name="Test"
        )
        
        print(f"✅ Создан пользователь: {user.user_id} - {user.username}")
        return True
    except Exception as e:
        print(f"❌ Ошибка валидации: {e}")
        return False

def test_user_state():
    """Тест состояния пользователя"""
    print("🔍 Тестируем состояние пользователя...")
    
    try:
        from src.models.improved_models import UserState
        
        # Создаем состояние пользователя
        user_state = UserState(user_id=123456789, username="test_user")
        
        # Добавляем сообщение
        user_state.add_message_to_history("user", "Привет!")
        user_state.add_message_to_history("assistant", "Привет! Как дела?")
        
        # Проверяем метрики
        assert user_state.conversation_metrics.total_messages == 2
        assert user_state.conversation_metrics.user_messages == 1
        assert user_state.conversation_metrics.bot_messages == 1
        
        print(f"✅ Состояние пользователя работает. Сообщений: {user_state.conversation_metrics.total_messages}")
        return True
    except Exception as e:
        print(f"❌ Ошибка состояния: {e}")
        return False

def test_rate_limiter():
    """Тест rate limiter"""
    print("🔍 Тестируем rate limiter...")
    
    try:
        from src.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        # Тестируем несколько запросов
        for i in range(5):
            result = limiter.check_rate_limit(123456789, 'message')
            assert result == True
        
        print("✅ Rate limiter работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка rate limiter: {e}")
        return False

def test_error_handling():
    """Тест обработки ошибок"""
    print("🔍 Тестируем обработку ошибок...")
    
    try:
        from src.core.error_handlers import ErrorHandler
        from src.core.exceptions import ValidationError
        
        handler = ErrorHandler()
        
        # Симулируем ошибку
        test_error = ValidationError("Test error")
        result = handler.handle_error(test_error)
        
        assert result['handled'] == True
        assert result['severity'] == 'low'
        
        print("✅ Обработка ошибок работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка обработки ошибок: {e}")
        return False

def test_logging():
    """Тест системы логирования"""
    print("🔍 Тестируем систему логирования...")
    
    try:
        from src.core.logging_config import setup_logging, get_logger
        
        # Настраиваем логирование в тестовом режиме
        setup_logging(
            log_level="INFO",
            log_dir="test_logs",
            enable_console=False,
            enable_file=False
        )
        
        logger = get_logger("test")
        logger.info("Test log message")
        
        print("✅ Система логирования работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка логирования: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🚀 БЫСТРЫЙ ТЕСТ ГОТОВНОСТИ К РЕЛИЗУ")
    print("=" * 50)
    
    tests = [
        test_core_imports,
        test_user_validation,
        test_user_state,
        test_rate_limiter,
        test_error_handling,
        test_logging
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 РЕЗУЛЬТАТ: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! БОТ ГОТОВ К РЕЛИЗУ!")
        print("\n🚀 ДЛЯ ЗАПУСКА:")
        print("1. Настройте переменные окружения в .env")
        print("2. Запустите: python bot.py")
        return True
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ! НЕ ГОТОВ К РЕЛИЗУ!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 