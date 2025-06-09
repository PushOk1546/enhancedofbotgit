"""
Тесты интеграции компонентов
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

@pytest.fixture
def test_log_dir(tmp_path):
    """Фикстура для создания временной директории логов"""
    log_path = tmp_path / "logs"
    log_path.mkdir()
    return log_path

@pytest.mark.asyncio
async def test_bot_groq_integration(mock_bot, mock_message, mock_groq, mock_logger):
    """Тест интеграции бота с Groq"""
    from main_bot import handle_reply
    from groq_integration import generate_reply_variants
    
    # Настраиваем мок для Groq
    mock_groq.return_value = ["Test reply 1", "Test reply 2", "Test reply 3"]
    
    # Вызываем обработчик
    await handle_reply(mock_message, mock_bot)
    
    # Проверяем вызовы
    mock_groq.assert_called_once()
    mock_bot.send_message.assert_called()
    mock_logger.log_user_activity.assert_called_once()

@pytest.mark.asyncio
async def test_bot_logging_integration(mock_bot, mock_message, mock_logger):
    """Тест интеграции бота с логированием"""
    from main_bot import handle_start, handle_help, handle_reply
    
    # Тест команды /start
    await handle_start(mock_message, mock_bot)
    mock_logger.log_user_activity.assert_called_with(
        mock_message.from_user.id,
        "command",
        {"command": "start"}
    )
    
    # Тест команды /help
    await handle_help(mock_message, mock_bot)
    mock_logger.log_user_activity.assert_called_with(
        mock_message.from_user.id,
        "command",
        {"command": "help"}
    )
    
    # Тест команды /reply
    await handle_reply(mock_message, mock_bot)
    mock_logger.log_user_activity.assert_called_with(
        mock_message.from_user.id,
        "reply",
        {"message": mock_message.text}
    )

@pytest.mark.asyncio
async def test_groq_logging_integration(mock_groq_client, mock_logger):
    """Тест интеграции Groq с логированием"""
    from groq_integration import generate_reply_variants
    
    # Настраиваем мок для Groq
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test reply"))]
    mock_groq_client.chat.completions.create.return_value = mock_response
    
    # Вызываем генерацию
    await generate_reply_variants("Test message", "friendly")
    
    # Проверяем логирование
    mock_logger.log_performance.assert_called()

@pytest.mark.asyncio
async def test_state_logging_integration(mock_logger):
    """Тест интеграции состояния с логированием"""
    from app.core.state import StateManager
    
    # Создаем менеджер состояния
    manager = StateManager("test_state.json")
    await manager.initialize()
    
    # Выполняем операции
    await manager.set("test_key", "test_value")
    await manager.get("test_key")
    await manager.delete("test_key")
    
    # Проверяем логирование
    mock_logger.log_performance.assert_called()

@pytest.mark.asyncio
async def test_error_handling_integration(mock_bot, mock_message, mock_logger):
    """Тест интеграции обработки ошибок"""
    from main_bot import handle_reply
    from groq_integration import generate_reply_variants
    
    # Симулируем ошибку в Groq
    with patch('groq_integration.generate_reply_variants', side_effect=Exception("Test error")):
        await handle_reply(mock_message, mock_bot)
        
        # Проверяем логирование ошибки
        mock_logger.log_error.assert_called_with(
            "Test error",
            "Exception",
            {"user_id": mock_message.from_user.id}
        )

@pytest.mark.asyncio
async def test_cache_state_integration():
    """Тест интеграции кэша с состоянием"""
    from utils import Cache
    from app.core.state import StateManager
    
    # Создаем кэш и менеджер состояния
    cache = Cache()
    manager = StateManager("test_state.json")
    await manager.initialize()
    
    # Устанавливаем значение в кэш
    await cache.set("test_key", "test_value")
    
    # Проверяем значение в состоянии
    value = await manager.get("test_key")
    assert value == "test_value"

@pytest.mark.asyncio
async def test_queue_state_integration():
    """Тест интеграции очереди с состоянием"""
    from utils import MessageQueue
    from app.core.state import StateManager
    
    # Создаем очередь и менеджер состояния
    queue = MessageQueue()
    manager = StateManager("test_state.json")
    await manager.initialize()
    
    # Добавляем сообщение в очередь
    await queue.add_message(123, "test_message")
    
    # Проверяем состояние
    state = await manager.get("queue_123")
    assert state == "test_message"

@pytest.mark.asyncio
async def test_performance_monitoring_integration(mock_logger):
    """Тест интеграции мониторинга производительности"""
    from utils import PerformanceMonitor
    from app.core.state import StateManager
    
    # Создаем монитор и менеджер состояния
    monitor = PerformanceMonitor()
    manager = StateManager("test_state.json")
    await manager.initialize()
    
    # Выполняем операцию с измерением времени
    async with monitor.measure("test_operation"):
        await asyncio.sleep(0.1)
    
    # Проверяем метрики
    metrics = monitor.get_metrics()
    assert "test_operation" in metrics
    assert metrics["test_operation"]["count"] == 1
    assert metrics["test_operation"]["total_time"] >= 0.1

@pytest.mark.asyncio
async def test_full_workflow_integration(mock_bot, mock_message, mock_groq, mock_logger):
    """Тест полного рабочего процесса"""
    from main_bot import handle_reply
    from groq_integration import generate_reply_variants
    from utils import Cache, MessageQueue, PerformanceMonitor
    from app.core.state import StateManager
    
    # Инициализируем компоненты
    cache = Cache()
    queue = MessageQueue()
    monitor = PerformanceMonitor()
    manager = StateManager("test_state.json")
    await manager.initialize()
    
    # Настраиваем мок для Groq
    mock_groq.return_value = ["Test reply 1", "Test reply 2", "Test reply 3"]
    
    # Выполняем полный процесс
    async with monitor.measure("full_workflow"):
        # Добавляем сообщение в очередь
        await queue.add_message(mock_message.from_user.id, mock_message.text)
        
        # Обрабатываем сообщение
        await handle_reply(mock_message, mock_bot)
        
        # Проверяем кэш
        cached_reply = await cache.get(f"reply_{mock_message.text}")
        assert cached_reply is not None
        
        # Проверяем состояние
        state = await manager.get(f"user_{mock_message.from_user.id}")
        assert state is not None
    
    # Проверяем логирование
    mock_logger.log_user_activity.assert_called()
    mock_logger.log_performance.assert_called()
    
    # Проверяем метрики
    metrics = monitor.get_metrics()
    assert "full_workflow" in metrics
    assert metrics["full_workflow"]["count"] == 1 