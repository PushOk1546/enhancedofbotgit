"""
Тесты производительности и нагрузки
"""

import pytest
from unittest.mock import patch, Mock
import asyncio
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import time

@pytest.fixture
def test_data_dir(tmp_path):
    """Фикстура для создания временной директории данных"""
    data_path = tmp_path / "data"
    data_path.mkdir()
    return data_path

@pytest.fixture
def test_log_dir(tmp_path):
    """Фикстура для создания временной директории логов"""
    log_path = tmp_path / "logs"
    log_path.mkdir()
    return log_path

@pytest.mark.asyncio
async def test_concurrent_requests(mock_bot, mock_groq, mock_logger):
    """Тест конкурентных запросов"""
    from main_bot import handle_reply
    
    # Создаем несколько сообщений
    messages = [
        MockMessage(f"/reply Test message {i}", 
                   from_user=MockUser(123, f"test_user_{i}"),
                   chat=MockChat(123))
        for i in range(10)
    ]
    
    # Запускаем обработку конкурентно
    start_time = time.time()
    tasks = [handle_reply(msg, mock_bot) for msg in messages]
    await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Проверяем время выполнения
    execution_time = end_time - start_time
    assert execution_time < 5.0  # Максимальное время выполнения
    
    # Проверяем количество вызовов
    assert mock_bot.send_message.call_count == 10
    assert mock_logger.log_user_activity.call_count == 10

@pytest.mark.asyncio
async def test_memory_usage(mock_bot, mock_message, mock_groq, mock_logger):
    """Тест использования памяти"""
    import psutil
    import os
    
    from main_bot import handle_reply
    from utils import Cache, MessageQueue
    from app.core.state import StateManager
    
    # Инициализируем компоненты
    cache = Cache()
    queue = MessageQueue()
    manager = StateManager("test_state.json")
    await manager.initialize()
    
    # Измеряем начальное использование памяти
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Выполняем множество операций
    for i in range(100):
        await cache.set(f"key_{i}", f"value_{i}")
        await queue.add_message(123, f"message_{i}")
        await manager.set(f"state_{i}", f"value_{i}")
    
    # Измеряем конечное использование памяти
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Проверяем, что увеличение памяти в разумных пределах
    assert memory_increase < 50 * 1024 * 1024  # 50 MB

@pytest.mark.asyncio
async def test_response_time(mock_bot, mock_message, mock_groq, mock_logger):
    """Тест времени отклика"""
    from main_bot import handle_reply
    
    # Настраиваем мок для Groq
    mock_groq.return_value = ["Test reply"]
    
    # Измеряем время отклика
    start_time = time.time()
    await handle_reply(mock_message, mock_bot)
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 1.0  # Максимальное время отклика

@pytest.mark.asyncio
async def test_cache_performance():
    """Тест производительности кэша"""
    from utils import Cache
    
    cache = Cache()
    
    # Тест скорости записи
    start_time = time.time()
    for i in range(1000):
        await cache.set(f"key_{i}", f"value_{i}")
    write_time = time.time() - start_time
    assert write_time < 1.0  # Максимальное время записи
    
    # Тест скорости чтения
    start_time = time.time()
    for i in range(1000):
        value = await cache.get(f"key_{i}")
        assert value == f"value_{i}"
    read_time = time.time() - start_time
    assert read_time < 1.0  # Максимальное время чтения

@pytest.mark.asyncio
async def test_queue_performance():
    """Тест производительности очереди"""
    from utils import MessageQueue
    
    queue = MessageQueue()
    
    # Тест скорости добавления
    start_time = time.time()
    for i in range(1000):
        await queue.add_message(123, f"message_{i}")
    add_time = time.time() - start_time
    assert add_time < 1.0  # Максимальное время добавления
    
    # Тест скорости получения
    start_time = time.time()
    for i in range(1000):
        message = await queue.get_message(123)
        assert message == f"message_{i}"
    get_time = time.time() - start_time
    assert get_time < 1.0  # Максимальное время получения

@pytest.mark.asyncio
async def test_state_performance():
    """Тест производительности состояния"""
    from app.core.state import StateManager
    
    manager = StateManager("test_state.json")
    await manager.initialize()
    
    # Тест скорости записи
    start_time = time.time()
    for i in range(1000):
        await manager.set(f"key_{i}", f"value_{i}")
    write_time = time.time() - start_time
    assert write_time < 1.0  # Максимальное время записи
    
    # Тест скорости чтения
    start_time = time.time()
    for i in range(1000):
        value = await manager.get(f"key_{i}")
        assert value == f"value_{i}"
    read_time = time.time() - start_time
    assert read_time < 1.0  # Максимальное время чтения

@pytest.mark.asyncio
async def test_logging_performance(mock_logger):
    """Тест производительности логирования"""
    # Тест скорости логирования
    start_time = time.time()
    for i in range(1000):
        await mock_logger.log_user_activity(123, "test_action", {"index": i})
    log_time = time.time() - start_time
    assert log_time < 1.0  # Максимальное время логирования

@pytest.mark.asyncio
async def test_groq_performance(mock_groq_client):
    """Тест производительности Groq"""
    from groq_integration import generate_reply_variants
    
    # Настраиваем мок для Groq
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test reply"))]
    mock_groq_client.chat.completions.create.return_value = mock_response
    
    # Тест скорости генерации
    start_time = time.time()
    for i in range(10):
        await generate_reply_variants(f"Test message {i}", "friendly")
    gen_time = time.time() - start_time
    assert gen_time < 5.0  # Максимальное время генерации

@pytest.mark.asyncio
async def test_full_load_test(mock_bot, mock_groq, mock_logger):
    """Тест полной нагрузки"""
    from main_bot import handle_reply
    from utils import Cache, MessageQueue, PerformanceMonitor
    from app.core.state import StateManager
    
    # Инициализируем компоненты
    cache = Cache()
    queue = MessageQueue()
    monitor = PerformanceMonitor()
    manager = StateManager("test_state.json")
    await manager.initialize()
    
    # Настраиваем мок для Groq
    mock_groq.return_value = ["Test reply"]
    
    # Создаем множество сообщений
    messages = [
        MockMessage(f"/reply Test message {i}", 
                   from_user=MockUser(123, f"test_user_{i}"),
                   chat=MockChat(123))
        for i in range(50)
    ]
    
    # Выполняем нагрузочное тестирование
    start_time = time.time()
    tasks = []
    for msg in messages:
        tasks.append(handle_reply(msg, mock_bot))
        tasks.append(cache.set(f"key_{msg.text}", "value"))
        tasks.append(queue.add_message(msg.from_user.id, msg.text))
        tasks.append(manager.set(f"state_{msg.text}", "value"))
    
    await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Проверяем общее время выполнения
    execution_time = end_time - start_time
    assert execution_time < 10.0  # Максимальное время выполнения
    
    # Проверяем метрики
    metrics = monitor.get_metrics()
    assert "full_load_test" in metrics
    assert metrics["full_load_test"]["count"] == 1
    assert metrics["full_load_test"]["total_time"] < 10.0 