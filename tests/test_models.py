"""
Тесты для моделей данных
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
async def test_user_model():
    """Тест модели пользователя"""
    from models import User
    
    # Создание пользователя
    user = User(
        id=123,
        username="test_user",
        first_name="Test",
        last_name="User",
        join_date=datetime.now()
    )
    
    # Проверка атрибутов
    assert user.id == 123
    assert user.username == "test_user"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert isinstance(user.join_date, datetime)
    
    # Проверка сериализации
    user_dict = user.to_dict()
    assert isinstance(user_dict, dict)
    assert user_dict["id"] == 123
    assert user_dict["username"] == "test_user"
    
    # Проверка десериализации
    new_user = User.from_dict(user_dict)
    assert new_user.id == user.id
    assert new_user.username == user.username

@pytest.mark.asyncio
async def test_message_model():
    """Тест модели сообщения"""
    from models import Message
    
    # Создание сообщения
    message = Message(
        id=456,
        user_id=123,
        text="Test message",
        timestamp=datetime.now()
    )
    
    # Проверка атрибутов
    assert message.id == 456
    assert message.user_id == 123
    assert message.text == "Test message"
    assert isinstance(message.timestamp, datetime)
    
    # Проверка сериализации
    message_dict = message.to_dict()
    assert isinstance(message_dict, dict)
    assert message_dict["id"] == 456
    assert message_dict["text"] == "Test message"
    
    # Проверка десериализации
    new_message = Message.from_dict(message_dict)
    assert new_message.id == message.id
    assert new_message.text == message.text

@pytest.mark.asyncio
async def test_reply_model():
    """Тест модели ответа"""
    from models import Reply
    
    # Создание ответа
    reply = Reply(
        id=789,
        message_id=456,
        text="Test reply",
        style="friendly",
        timestamp=datetime.now()
    )
    
    # Проверка атрибутов
    assert reply.id == 789
    assert reply.message_id == 456
    assert reply.text == "Test reply"
    assert reply.style == "friendly"
    assert isinstance(reply.timestamp, datetime)
    
    # Проверка сериализации
    reply_dict = reply.to_dict()
    assert isinstance(reply_dict, dict)
    assert reply_dict["id"] == 789
    assert reply_dict["text"] == "Test reply"
    
    # Проверка десериализации
    new_reply = Reply.from_dict(reply_dict)
    assert new_reply.id == reply.id
    assert new_reply.text == reply.text

@pytest.mark.asyncio
async def test_user_stats_model():
    """Тест модели статистики пользователя"""
    from models import UserStats
    
    # Создание статистики
    stats = UserStats(
        user_id=123,
        commands_used=10,
        replies_generated=5,
        ppv_created=2,
        last_active=datetime.now()
    )
    
    # Проверка атрибутов
    assert stats.user_id == 123
    assert stats.commands_used == 10
    assert stats.replies_generated == 5
    assert stats.ppv_created == 2
    assert isinstance(stats.last_active, datetime)
    
    # Проверка сериализации
    stats_dict = stats.to_dict()
    assert isinstance(stats_dict, dict)
    assert stats_dict["user_id"] == 123
    assert stats_dict["commands_used"] == 10
    
    # Проверка десериализации
    new_stats = UserStats.from_dict(stats_dict)
    assert new_stats.user_id == stats.user_id
    assert new_stats.commands_used == stats.commands_used

@pytest.mark.asyncio
async def test_error_model():
    """Тест модели ошибки"""
    from models import Error
    
    # Создание ошибки
    error = Error(
        id=1,
        error_type="TestError",
        message="Test error message",
        context={"test": "context"},
        timestamp=datetime.now()
    )
    
    # Проверка атрибутов
    assert error.id == 1
    assert error.error_type == "TestError"
    assert error.message == "Test error message"
    assert error.context == {"test": "context"}
    assert isinstance(error.timestamp, datetime)
    
    # Проверка сериализации
    error_dict = error.to_dict()
    assert isinstance(error_dict, dict)
    assert error_dict["error_type"] == "TestError"
    assert error_dict["message"] == "Test error message"
    
    # Проверка десериализации
    new_error = Error.from_dict(error_dict)
    assert new_error.error_type == error.error_type
    assert new_error.message == error.message

@pytest.mark.asyncio
async def test_performance_model():
    """Тест модели производительности"""
    from models import Performance
    
    # Создание метрики производительности
    perf = Performance(
        id=1,
        operation="test_operation",
        duration=1.5,
        metrics={"cpu": 50, "memory": 100},
        timestamp=datetime.now()
    )
    
    # Проверка атрибутов
    assert perf.id == 1
    assert perf.operation == "test_operation"
    assert perf.duration == 1.5
    assert perf.metrics == {"cpu": 50, "memory": 100}
    assert isinstance(perf.timestamp, datetime)
    
    # Проверка сериализации
    perf_dict = perf.to_dict()
    assert isinstance(perf_dict, dict)
    assert perf_dict["operation"] == "test_operation"
    assert perf_dict["duration"] == 1.5
    
    # Проверка десериализации
    new_perf = Performance.from_dict(perf_dict)
    assert new_perf.operation == perf.operation
    assert new_perf.duration == perf.duration

@pytest.mark.asyncio
async def test_model_validation():
    """Тест валидации моделей"""
    from models import User, Message, Reply
    
    # Тест валидации пользователя
    with pytest.raises(ValueError):
        User(id=None, username="test_user")
    
    with pytest.raises(ValueError):
        User(id=123, username=None)
    
    # Тест валидации сообщения
    with pytest.raises(ValueError):
        Message(id=None, user_id=123, text="test")
    
    with pytest.raises(ValueError):
        Message(id=456, user_id=None, text="test")
    
    # Тест валидации ответа
    with pytest.raises(ValueError):
        Reply(id=None, message_id=456, text="test", style="friendly")
    
    with pytest.raises(ValueError):
        Reply(id=789, message_id=None, text="test", style="friendly")

@pytest.mark.asyncio
async def test_model_persistence(test_data_dir):
    """Тест персистентности моделей"""
    from models import User, Message, Reply
    
    # Создание тестовых данных
    user = User(id=123, username="test_user")
    message = Message(id=456, user_id=123, text="test message")
    reply = Reply(id=789, message_id=456, text="test reply", style="friendly")
    
    # Сохранение в файл
    data = {
        "user": user.to_dict(),
        "message": message.to_dict(),
        "reply": reply.to_dict()
    }
    file_path = test_data_dir / "models.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    # Загрузка из файла
    with open(file_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    # Проверка загруженных данных
    loaded_user = User.from_dict(loaded_data["user"])
    loaded_message = Message.from_dict(loaded_data["message"])
    loaded_reply = Reply.from_dict(loaded_data["reply"])
    
    assert loaded_user.id == user.id
    assert loaded_message.id == message.id
    assert loaded_reply.id == reply.id 