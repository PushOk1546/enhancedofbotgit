"""
Тесты для утилитарных функций
"""

import pytest
from unittest.mock import patch, Mock
import asyncio
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

@pytest.fixture
def test_data_dir(tmp_path):
    """Фикстура для создания временной директории данных"""
    data_path = tmp_path / "data"
    data_path.mkdir()
    return data_path

@pytest.mark.asyncio
async def test_message_validation():
    """Тест валидации сообщений"""
    from utils import validate_message
    
    # Тест валидного сообщения
    assert validate_message("Test message") is True
    
    # Тест пустого сообщения
    assert validate_message("") is False
    
    # Тест слишком длинного сообщения
    long_message = "a" * 1000
    assert validate_message(long_message) is False

@pytest.mark.asyncio
async def test_rate_limiting():
    """Тест ограничения частоты запросов"""
    from utils import RateLimiter
    
    limiter = RateLimiter(max_requests=3, time_window=1)
    
    # Тест в пределах лимита
    assert await limiter.check_rate_limit(123) is True
    assert await limiter.check_rate_limit(123) is True
    assert await limiter.check_rate_limit(123) is True
    
    # Тест превышения лимита
    assert await limiter.check_rate_limit(123) is False
    
    # Тест разных пользователей
    assert await limiter.check_rate_limit(456) is True

@pytest.mark.asyncio
async def test_cache_operations():
    """Тест операций с кэшем"""
    from utils import Cache
    
    cache = Cache()
    
    # Тест установки и получения значения
    await cache.set("test_key", "test_value")
    value = await cache.get("test_key")
    assert value == "test_value"
    
    # Тест получения несуществующего значения
    value = await cache.get("non_existent")
    assert value is None
    
    # Тест удаления значения
    await cache.delete("test_key")
    value = await cache.get("test_key")
    assert value is None

@pytest.mark.asyncio
async def test_file_operations(test_data_dir):
    """Тест операций с файлами"""
    from utils import save_json, load_json
    
    test_data = {"test": "data"}
    file_path = test_data_dir / "test.json"
    
    # Тест сохранения
    await save_json(str(file_path), test_data)
    assert file_path.exists()
    
    # Тест загрузки
    loaded_data = await load_json(str(file_path))
    assert loaded_data == test_data

@pytest.mark.asyncio
async def test_error_handling():
    """Тест обработки ошибок"""
    from utils import handle_error
    
    # Тест с ошибкой
    error = Exception("Test error")
    result = await handle_error(error)
    assert "error" in result.lower()
    
    # Тест с контекстом
    context = {"test": "context"}
    result = await handle_error(error, context)
    assert "error" in result.lower()
    assert "context" in str(result)

@pytest.mark.asyncio
async def test_performance_monitoring():
    """Тест мониторинга производительности"""
    from utils import PerformanceMonitor
    
    monitor = PerformanceMonitor()
    
    # Тест измерения времени выполнения
    async with monitor.measure("test_operation"):
        await asyncio.sleep(0.1)
    
    metrics = monitor.get_metrics()
    assert "test_operation" in metrics
    assert metrics["test_operation"]["count"] == 1
    assert metrics["test_operation"]["total_time"] >= 0.1

@pytest.mark.asyncio
async def test_state_management():
    """Тест управления состоянием"""
    from utils import StateManager
    
    manager = StateManager()
    
    # Тест установки и получения состояния
    await manager.set_state(123, "test_state")
    state = await manager.get_state(123)
    assert state == "test_state"
    
    # Тест очистки состояния
    await manager.clear_state(123)
    state = await manager.get_state(123)
    assert state is None

@pytest.mark.asyncio
async def test_message_queue():
    """Тест очереди сообщений"""
    from utils import MessageQueue
    
    queue = MessageQueue()
    
    # Тест добавления и получения сообщения
    await queue.add_message(123, "test_message")
    message = await queue.get_message(123)
    assert message == "test_message"
    
    # Тест пустой очереди
    message = await queue.get_message(123)
    assert message is None

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Тест конкурентных операций"""
    from utils import Cache
    
    cache = Cache()
    
    async def update_value(key: str, value: str):
        await cache.set(key, value)
    
    # Запускаем конкурентные операции
    tasks = [
        update_value("test_key", f"value_{i}")
        for i in range(5)
    ]
    await asyncio.gather(*tasks)
    
    # Проверяем финальное значение
    value = await cache.get("test_key")
    assert value in [f"value_{i}" for i in range(5)]

@pytest.mark.asyncio
async def test_data_persistence(test_data_dir):
    """Тест персистентности данных"""
    from utils import save_json, load_json
    
    test_data = {
        "key1": "value1",
        "key2": "value2"
    }
    file_path = test_data_dir / "persistent.json"
    
    # Сохраняем данные
    await save_json(str(file_path), test_data)
    
    # Загружаем данные
    loaded_data = await load_json(str(file_path))
    assert loaded_data == test_data
    
    # Модифицируем и сохраняем снова
    test_data["key3"] = "value3"
    await save_json(str(file_path), test_data)
    
    # Проверяем обновленные данные
    loaded_data = await load_json(str(file_path))
    assert loaded_data == test_data 