"""
Тесты для системы обработки ошибок
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from app.core.error_handler import ErrorHandler, RetryStrategy, ErrorRecovery

class TestError(Exception):
    """Тестовая ошибка"""
    pass

@pytest.fixture
def error_handler():
    """Фикстура для создания обработчика ошибок"""
    return ErrorHandler()

@pytest.fixture
def retry_strategy():
    """Фикстура для создания стратегии повторных попыток"""
    return RetryStrategy(max_retries=3, delay=0.1)

@pytest.fixture
def error_recovery(error_handler):
    """Фикстура для создания восстановления после ошибок"""
    return ErrorRecovery(error_handler)

@pytest.mark.asyncio
async def test_error_handling(error_handler):
    """Тест обработки ошибок"""
    error = TestError("Test error")
    context = {"test": "context"}
    
    await error_handler.handle_error(error, context)
    
    error_key = f"TestError:Test error"
    assert error_key in error_handler.error_counts
    assert error_handler.error_counts[error_key] == 1

@pytest.mark.asyncio
async def test_error_threshold(error_handler):
    """Тест превышения порога ошибок"""
    error = TestError("Test error")
    context = {"test": "context"}
    
    # Генерация ошибок до превышения порога
    for _ in range(error_handler.error_threshold):
        await error_handler.handle_error(error, context)
        
    error_key = f"TestError:Test error"
    assert error_handler.error_counts[error_key] >= error_handler.error_threshold

@pytest.mark.asyncio
async def test_error_recovery_strategy(error_handler):
    """Тест стратегии восстановления"""
    recovery_called = False
    
    async def recovery_strategy(error, context):
        nonlocal recovery_called
        recovery_called = True
        
    error_handler.register_recovery_strategy(TestError, recovery_strategy)
    
    error = TestError("Test error")
    context = {"test": "context"}
    
    # Генерация ошибок до превышения порога
    for _ in range(error_handler.error_threshold):
        await error_handler.handle_error(error, context)
        
    assert recovery_called

@pytest.mark.asyncio
async def test_retry_strategy(retry_strategy):
    """Тест стратегии повторных попыток"""
    attempt_count = 0
    
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise TestError("Test error")
        return "success"
        
    result = await retry_strategy.execute(failing_function)
    assert result == "success"
    assert attempt_count == 3

@pytest.mark.asyncio
async def test_error_recovery(error_recovery):
    """Тест восстановления после ошибок"""
    error = TestError("Test error")
    context = {"test": "context"}
    
    # Регистрация стратегии восстановления
    async def recovery_strategy(error, context):
        return True
        
    error_recovery.error_handler.register_recovery_strategy(TestError, recovery_strategy)
    
    # Проверка восстановления
    result = await error_recovery.recover_from_error(error, context)
    assert result

@pytest.mark.asyncio
async def test_error_stats(error_handler):
    """Тест статистики ошибок"""
    error = TestError("Test error")
    context = {"test": "context"}
    
    await error_handler.handle_error(error, context)
    stats = error_handler.get_error_stats()
    
    assert "error_counts" in stats
    assert "last_errors" in stats
    assert f"TestError:Test error" in stats["error_counts"]

@pytest.mark.asyncio
async def test_error_window(error_handler):
    """Тест окна времени для ошибок"""
    error = TestError("Test error")
    context = {"test": "context"}
    
    # Первая ошибка
    await error_handler.handle_error(error, context)
    error_key = f"TestError:Test error"
    initial_count = error_handler.error_counts[error_key]
    
    # Имитация прошедшего времени
    error_handler.last_errors[error_key] = datetime.now() - timedelta(seconds=error_handler.error_window + 1)
    
    # Вторая ошибка после окна
    await error_handler.handle_error(error, context)
    assert error_handler.error_counts[error_key] == 1  # Счетчик должен сброситься

@pytest.mark.asyncio
async def test_error_decorator(error_handler):
    """Тест декоратора обработки ошибок"""
    @error_handler.handle_errors
    async def test_function():
        raise TestError("Test error")
        
    with pytest.raises(TestError):
        await test_function()
        
    error_key = f"TestError:Test error"
    assert error_key in error_handler.error_counts 