"""
Конфигурация тестов и общие фикстуры для MVP
"""

import os
import pytest
import asyncio
import sys
from typing import Generator
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Добавляем путь к корню проекта для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создаем event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

class MockUser:
    """Мок пользователя Telegram"""
    def __init__(self, id: int, username: str = None, first_name: str = None):
        self.id = id
        self.username = username
        self.first_name = first_name

class MockChat:
    """Мок чата Telegram"""
    def __init__(self, id: int, type: str = "private"):
        self.id = id
        self.type = type

class MockMessage:
    """Мок сообщения Telegram"""
    def __init__(self, text: str, from_user: MockUser = None, chat: MockChat = None):
        self.text = text
        self.from_user = from_user or MockUser(123, "test_user", "Test")
        self.chat = chat or MockChat(123)

class MockCallbackQuery:
    """Мок callback query Telegram"""
    def __init__(self, data: str, from_user: MockUser = None, message: MockMessage = None):
        self.data = data
        self.from_user = from_user or MockUser(123, "test_user", "Test")
        self.message = message or MockMessage("", from_user)
        self.id = "test_callback_id"

@pytest.fixture
def mock_message():
    """Фикстура для создания мок-сообщения"""
    return MockMessage(
        text="/reply Test message",
        from_user=MockUser(123, "test_user", "Test"),
        chat=MockChat(123)
    )

@pytest.fixture
def mock_callback():
    """Фикстура для создания мок-callback"""
    return MockCallbackQuery(
        data="style_friendly",
        from_user=MockUser(123, "test_user", "Test"),
        message=MockMessage("", MockUser(123, "test_user", "Test"))
    )

@pytest.fixture
def mock_bot():
    with patch('main_bot.AsyncTeleBot') as mock:
        bot = mock.return_value
        bot.send_message = Mock()
        bot.send_chat_action = Mock()
        bot.edit_message_text = Mock()
        bot.answer_callback_query = Mock()
        yield bot

@pytest.fixture
def mock_groq():
    with patch('groq_integration.generate_reply_variants') as mock:
        mock.return_value = [
            "Test reply 1",
            "Test reply 2",
            "Test reply 3"
        ]
        yield mock

@pytest.fixture
def mock_logger():
    with patch('enhanced_logging.BotLogger') as mock:
        logger = mock.return_value
        logger.log_error = Mock()
        logger.log_user_activity = Mock()
        logger.log_performance = Mock()
        yield logger

@pytest.fixture
def test_user_stats():
    """Фикстура с тестовыми статистиками пользователя"""
    return {
        "reply_requests": 10,
        "replies_selected": 5,
        "join_date": datetime.now().isoformat()
    }

@pytest.fixture
def test_styles():
    """Фикстура с доступными стилями ответов"""
    return {
        "friendly": "Дружелюбный",
        "flirty": "Флиртующий", 
        "passionate": "Страстный",
        "romantic": "Романтичный",
        "professional": "Профессиональный"
    } 