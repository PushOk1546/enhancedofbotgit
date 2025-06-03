"""
Тесты для улучшенной системы OF Assistant Bot.
Проверяют валидацию, обработку ошибок, rate limiting и другие компоненты.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import uuid
from pydantic import ValidationError as PydanticValidationError

# Импортируем модули для тестирования
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.exceptions import (
    ValidationError, RateLimitError, GroqAPIError, 
    BotException, ConfigurationError
)
from src.core.validators import (
    ValidatedUser, ValidatedMessage, ValidatedCallback,
    validate_user_input, ContentType, UserRole
)
from src.core.rate_limiter import RateLimiter, rate_limiter
from src.core.error_handlers import ErrorHandler, error_handler, handle_errors
from src.core.logging_config import setup_logging
from src.core.async_helpers import (
    run_async, make_async, make_sync, AsyncBatch, AsyncCache
)
from src.models.improved_models import (
    UserState, UserPreferences, PPVReminder, ConversationMetrics,
    ConversationStage, CommunicationStyle, ModelType
)


class TestValidation:
    """Тесты системы валидации"""
    
    def test_validated_user_success(self):
        """Тест успешной валидации пользователя"""
        user_data = {
            'user_id': 123456789,
            'username': 'test_user',
            'first_name': 'Test',
            'last_name': 'User',
            'language_code': 'en'
        }
        
        validated_user = ValidatedUser(**user_data)
        
        assert validated_user.user_id == 123456789
        assert validated_user.username == 'test_user'
        assert validated_user.role == UserRole.USER
    
    def test_validated_user_invalid_id(self):
        """Тест валидации с невалидным user_id"""
        with pytest.raises(PydanticValidationError):
            ValidatedUser(user_id=-1)
        
        with pytest.raises(PydanticValidationError):
            ValidatedUser(user_id=0)
    
    def test_validated_message_success(self):
        """Тест успешной валидации сообщения"""
        user = ValidatedUser(user_id=123456789)
        message_data = {
            'message_id': 1,
            'text': 'Hello, world!',
            'user': user,
            'chat_id': 123456789
        }
        
        validated_message = ValidatedMessage(**message_data)
        
        assert validated_message.message_id == 1
        assert validated_message.text == 'Hello, world!'
        assert validated_message.content_type == ContentType.TEXT
    
    def test_validated_message_dangerous_content(self):
        """Тест обнаружения опасного контента"""
        user = ValidatedUser(user_id=123456789)
        
        with pytest.raises(ValidationError):
            ValidatedMessage(
                message_id=1,
                text='<script>alert("xss")</script>',
                user=user,
                chat_id=123456789
            )
    
    def test_validate_user_input_function(self):
        """Тест функции validate_user_input"""
        user_data = {
            'user_id': 123456789,
            'username': 'test_user'
        }
        
        result = validate_user_input(user_data, 'user')
        assert isinstance(result, ValidatedUser)
        assert result.user_id == 123456789


class TestRateLimiter:
    """Тесты системы rate limiting"""
    
    def setup_method(self):
        """Подготовка к каждому тесту"""
        self.rate_limiter = RateLimiter()
    
    def test_rate_limit_allows_requests(self):
        """Тест разрешения запросов в пределах лимита"""
        user_id = 123456789
        
        # Первые запросы должны проходить
        for i in range(5):
            assert self.rate_limiter.check_rate_limit(user_id, 'message') == True
    
    def test_rate_limit_blocks_excess_requests(self):
        """Тест блокировки превышения лимитов"""
        user_id = 123456789
        
        # Исчерпываем лимит
        limit_config = self.rate_limiter.limits['message']
        for i in range(limit_config.requests):
            self.rate_limiter.check_rate_limit(user_id, 'message')
        
        # Следующий запрос должен быть заблокирован
        with pytest.raises(RateLimitError):
            self.rate_limiter.check_rate_limit(user_id, 'message')
    
    def test_rate_limit_info(self):
        """Тест получения информации о лимитах"""
        user_id = 123456789
        
        info = self.rate_limiter.get_rate_limit_info(user_id, 'message')
        
        assert 'limit' in info
        assert 'window' in info
        assert 'remaining' in info
        assert 'blocked' in info
        assert info['blocked'] == False
    
    def test_rate_limit_decorator(self):
        """Тест декоратора rate limit"""
        
        @self.rate_limiter.rate_limit_decorator('test')
        def test_function(user_id):
            return f"Success for user {user_id}"
        
        # Первый вызов должен пройти успешно
        result = test_function(123456789)
        assert result == "Success for user 123456789"


class TestErrorHandling:
    """Тесты системы обработки ошибок"""
    
    def setup_method(self):
        """Подготовка к каждому тесту"""
        self.error_handler = ErrorHandler()
    
    def test_error_classification(self):
        """Тест классификации ошибок"""
        validation_error = ValidationError("Test validation error")
        rate_limit_error = RateLimitError(123, 10, 60)
        
        result1 = self.error_handler.handle_error(validation_error)
        result2 = self.error_handler.handle_error(rate_limit_error)
        
        assert result1['category'] == 'validation'
        assert result1['severity'] == 'low'
        assert result2['category'] == 'api'
        assert result2['severity'] == 'medium'
    
    def test_error_statistics(self):
        """Тест сбора статистики ошибок"""
        # Генерируем несколько ошибок
        self.error_handler.handle_error(ValidationError("Test 1"))
        self.error_handler.handle_error(ValidationError("Test 2"))
        self.error_handler.handle_error(RateLimitError(123, 10, 60))
        
        stats = self.error_handler.get_error_stats()
        
        assert stats['error_counts']['ValidationError'] == 2
        assert stats['error_counts']['RateLimitError'] == 1
        assert stats['total_errors'] == 3
    
    def test_handle_errors_decorator(self):
        """Тест декоратора handle_errors"""
        
        @handle_errors(user_message="Custom error message")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        
        assert result['handled'] == True
        assert result['user_message'] == "Custom error message"
        assert result['category'] == 'validation'
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Тест асинхронной обработки ошибок"""
        
        @handle_errors()
        async def async_failing_function():
            raise ValueError("Async test error")
        
        result = await async_failing_function()
        
        assert result['handled'] == True
        assert result['severity'] == 'low'


class TestAsyncHelpers:
    """Тесты вспомогательных асинхронных функций"""
    
    def test_run_async(self):
        """Тест выполнения корутины в синхронном контексте"""
        
        async def async_function():
            return "async result"
        
        result = run_async(async_function())
        assert result == "async result"
    
    def test_make_async(self):
        """Тест преобразования синхронной функции в асинхронную"""
        
        def sync_function(x):
            return x * 2
        
        async_function = make_async(sync_function)
        
        # Проверяем, что функция стала асинхронной
        import asyncio
        assert asyncio.iscoroutinefunction(async_function)
    
    def test_make_sync(self):
        """Тест преобразования асинхронной функции в синхронную"""
        
        async def async_function(x):
            return x * 2
        
        sync_function = make_sync(async_function)
        
        result = sync_function(5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_async_batch(self):
        """Тест пакетной обработки"""
        
        async def processor(item):
            return item * 2
        
        batch = AsyncBatch(batch_size=3, max_concurrency=2)
        items = [1, 2, 3, 4, 5]
        
        results = await batch.process_batch(items, processor)
        
        assert results == [2, 4, 6, 8, 10]
    
    @pytest.mark.asyncio
    async def test_async_cache(self):
        """Тест асинхронного кеша"""
        
        cache = AsyncCache(default_ttl=1.0)
        
        # Установка и получение значения
        await cache.set("test_key", "test_value")
        result = await cache.get("test_key")
        
        assert result == "test_value"
        
        # Проверка TTL
        await asyncio.sleep(1.1)
        result = await cache.get("test_key")
        
        assert result is None


class TestImprovedModels:
    """Тесты улучшенных моделей данных"""
    
    def test_user_preferences(self):
        """Тест модели предпочтений пользователя"""
        preferences = UserPreferences(
            content_types=[ContentType.PHOTO, ContentType.VIDEO],
            communication_style=CommunicationStyle.FRIENDLY,
            price_range="100-500"
        )
        
        assert len(preferences.content_types) == 2
        assert preferences.communication_style == CommunicationStyle.FRIENDLY
        assert preferences.price_range == "100-500"
    
    def test_ppv_reminder(self):
        """Тест модели PPV напоминания"""
        future_time = datetime.now() + timedelta(hours=1)
        
        reminder = PPVReminder(
            user_id=123456789,
            message="Test reminder",
            scheduled_time=future_time,
            priority=3,
            tags=["urgent", "special"]
        )
        
        assert reminder.user_id == 123456789
        assert reminder.priority == 3
        assert len(reminder.tags) == 2
        assert not reminder.is_sent
    
    def test_ppv_reminder_validation(self):
        """Тест валидации PPV напоминания"""
        # Время в прошлом должно вызывать ошибку
        past_time = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(ValidationError):
            PPVReminder(
                user_id=123456789,
                message="Test",
                scheduled_time=past_time
            )
    
    def test_conversation_metrics(self):
        """Тест метрик разговора"""
        metrics = ConversationMetrics()
        
        # Добавляем сообщения
        metrics.update_message_count(True)  # От пользователя
        metrics.update_message_count(False)  # От бота
        metrics.update_message_count(True)  # От пользователя
        
        assert metrics.total_messages == 3
        assert metrics.user_messages == 2
        assert metrics.bot_messages == 1
        
        # Проверяем расчет engagement score
        score = metrics.calculate_engagement_score()
        assert score > 0
    
    def test_user_state(self):
        """Тест состояния пользователя"""
        user_state = UserState(
            user_id=123456789,
            username="test_user",
            model=ModelType.SMART,
            conversation_stage=ConversationStage.INITIAL
        )
        
        assert user_state.user_id == 123456789
        assert user_state.is_active == True
        assert user_state.is_blocked == False
        
        # Добавляем сообщение в историю
        user_state.add_message_to_history("user", "Hello", {"test": True})
        
        assert len(user_state.message_history) == 1
        assert user_state.conversation_metrics.total_messages == 1
    
    def test_user_state_serialization(self):
        """Тест сериализации/десериализации состояния пользователя"""
        user_state = UserState(
            user_id=123456789,
            username="test_user"
        )
        
        # Сериализация
        data = user_state.to_dict()
        assert isinstance(data, dict)
        assert data['user_id'] == 123456789
        
        # Десериализация
        restored_state = UserState.from_dict(data)
        assert restored_state.user_id == 123456789
        assert restored_state.username == "test_user"
    
    def test_user_state_blocking(self):
        """Тест блокировки пользователя"""
        user_state = UserState(user_id=123456789)
        
        # Блокируем пользователя
        user_state.block_user("spam")
        
        assert user_state.is_blocked == True
        assert user_state.is_active == False
        assert user_state.conversation_stage == ConversationStage.BLOCKED
        
        # Разблокируем
        user_state.unblock_user()
        
        assert user_state.is_blocked == False
        assert user_state.is_active == True
    
    def test_ppv_reminder_management(self):
        """Тест управления PPV напоминаниями"""
        user_state = UserState(user_id=123456789)
        
        # Добавляем напоминание
        future_time = datetime.now() + timedelta(minutes=1)
        reminder = user_state.add_ppv_reminder(
            "Test reminder",
            future_time,
            priority=2,
            tags=["test"]
        )
        
        assert len(user_state.ppv_reminders) == 1
        assert reminder.user_id == 123456789
        
        # Проверяем активные напоминания (пока не должно быть)
        active_reminders = user_state.get_active_reminders()
        assert len(active_reminders) == 0


class TestLogging:
    """Тесты системы логирования"""
    
    def test_logging_setup(self):
        """Тест настройки логирования"""
        # Настройка логирования в тестовом режиме
        setup_logging(
            log_level="DEBUG",
            log_dir="test_logs",
            enable_console=False,
            enable_file=False
        )
        
        # Проверяем, что настройка прошла без ошибок
        import logging
        logger = logging.getLogger("test")
        assert logger is not None


@pytest.mark.asyncio
async def test_integration_scenario():
    """Интеграционный тест основного сценария"""
    
    # Создаем пользователя
    user_data = {
        'user_id': 123456789,
        'username': 'integration_test'
    }
    
    # Валидируем входные данные
    validated_user = validate_user_input(user_data, 'user')
    
    # Создаем состояние пользователя
    user_state = UserState(
        user_id=validated_user.user_id,
        username=validated_user.username
    )
    
    # Проверяем rate limiting
    assert rate_limiter.check_rate_limit(user_state.user_id, 'message') == True
    
    # Добавляем сообщение
    user_state.add_message_to_history("user", "Hello bot!")
    
    # Проверяем метрики
    assert user_state.conversation_metrics.total_messages == 1
    assert user_state.conversation_metrics.user_messages == 1
    
    # Проверяем сериализацию
    data = user_state.to_dict()
    restored_state = UserState.from_dict(data)
    
    assert restored_state.user_id == user_state.user_id
    assert restored_state.conversation_metrics.total_messages == 1


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 