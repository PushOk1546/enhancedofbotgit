"""
Тесты для расширенного логирования
"""

import pytest
from unittest.mock import patch, Mock
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path

@pytest.fixture
def log_dir(tmp_path):
    """Фикстура для создания временной директории логов"""
    log_path = tmp_path / "logs"
    log_path.mkdir()
    return log_path

@pytest.fixture
def logger(log_dir):
    """Фикстура для создания логгера"""
    from enhanced_logging import BotLogger
    return BotLogger(str(log_dir))

@pytest.mark.asyncio
async def test_log_user_activity(logger, log_dir):
    """Тест логирования активности пользователя"""
    user_id = 123
    action = "test_action"
    details = {"test": "data"}
    
    await logger.log_user_activity(user_id, action, details)
    
    # Проверяем создание файла лога
    log_files = list(log_dir.glob("user_activity_*.json"))
    assert len(log_files) == 1
    
    # Проверяем содержимое лога
    with open(log_files[0], 'r', encoding='utf-8') as f:
        log_data = json.load(f)
        assert log_data["user_id"] == user_id
        assert log_data["action"] == action
        assert log_data["details"] == details
        assert "timestamp" in log_data

@pytest.mark.asyncio
async def test_log_error(logger, log_dir):
    """Тест логирования ошибок"""
    error_msg = "Test error"
    error_type = "TestError"
    context = {"test": "context"}
    
    await logger.log_error(error_msg, error_type, context)
    
    # Проверяем создание файла лога
    log_files = list(log_dir.glob("error_*.json"))
    assert len(log_files) == 1
    
    # Проверяем содержимое лога
    with open(log_files[0], 'r', encoding='utf-8') as f:
        log_data = json.load(f)
        assert log_data["error_message"] == error_msg
        assert log_data["error_type"] == error_type
        assert log_data["context"] == context
        assert "timestamp" in log_data

@pytest.mark.asyncio
async def test_log_performance(logger, log_dir):
    """Тест логирования производительности"""
    operation = "test_operation"
    duration = 1.5
    metrics = {"cpu": 50, "memory": 100}
    
    await logger.log_performance(operation, duration, metrics)
    
    # Проверяем создание файла лога
    log_files = list(log_dir.glob("performance_*.json"))
    assert len(log_files) == 1
    
    # Проверяем содержимое лога
    with open(log_files[0], 'r', encoding='utf-8') as f:
        log_data = json.load(f)
        assert log_data["operation"] == operation
        assert log_data["duration"] == duration
        assert log_data["metrics"] == metrics
        assert "timestamp" in log_data

@pytest.mark.asyncio
async def test_log_rotation(logger, log_dir):
    """Тест ротации логов"""
    # Создаем несколько логов
    for i in range(10):
        await logger.log_user_activity(123, f"action_{i}", {})
    
    # Проверяем количество файлов логов
    log_files = list(log_dir.glob("user_activity_*.json"))
    assert len(log_files) <= 5  # Проверяем ограничение на количество файлов

@pytest.mark.asyncio
async def test_log_formatting(logger, log_dir):
    """Тест форматирования логов"""
    # Тест с разными типами данных
    test_data = {
        "string": "test",
        "number": 123,
        "boolean": True,
        "list": [1, 2, 3],
        "dict": {"key": "value"},
        "none": None
    }
    
    await logger.log_user_activity(123, "test_action", test_data)
    
    # Проверяем содержимое лога
    log_files = list(log_dir.glob("user_activity_*.json"))
    with open(log_files[0], 'r', encoding='utf-8') as f:
        log_data = json.load(f)
        assert log_data["details"] == test_data

@pytest.mark.asyncio
async def test_concurrent_logging(logger, log_dir):
    """Тест конкурентного логирования"""
    async def log_activity(i):
        await logger.log_user_activity(i, f"action_{i}", {"index": i})
    
    # Запускаем несколько логов конкурентно
    tasks = [log_activity(i) for i in range(5)]
    await asyncio.gather(*tasks)
    
    # Проверяем, что все логи созданы
    log_files = list(log_dir.glob("user_activity_*.json"))
    assert len(log_files) == 5

@pytest.mark.asyncio
async def test_log_cleanup(logger, log_dir):
    """Тест очистки старых логов"""
    # Создаем старые логи
    old_date = datetime.now().strftime("%Y%m%d")
    for i in range(3):
        log_file = log_dir / f"user_activity_{old_date}_{i}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({"test": "data"}, f)
    
    # Запускаем очистку
    await logger.cleanup_old_logs(days=0)  # Очищаем все логи
    
    # Проверяем, что старые логи удалены
    log_files = list(log_dir.glob("user_activity_*.json"))
    assert len(log_files) == 0

@pytest.mark.asyncio
async def test_log_aggregation(logger, log_dir):
    """Тест агрегации логов"""
    # Создаем несколько логов
    for i in range(3):
        await logger.log_user_activity(123, "test_action", {"index": i})
    
    # Запускаем агрегацию
    await logger.aggregate_logs()
    
    # Проверяем создание агрегированного файла
    agg_files = list(log_dir.glob("aggregated_*.json"))
    assert len(agg_files) == 1
    
    # Проверяем содержимое агрегированного файла
    with open(agg_files[0], 'r', encoding='utf-8') as f:
        agg_data = json.load(f)
        assert "user_activity" in agg_data
        assert len(agg_data["user_activity"]) == 3 