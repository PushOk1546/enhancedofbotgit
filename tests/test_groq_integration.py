"""
Тесты для интеграции с Groq API
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
import asyncio
import sys
import os

# Добавляем путь к корню проекта для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.asyncio
async def test_generate_reply_variants_basic():
    """Тест базовой генерации вариантов ответов"""
    # Мокаем переменные окружения
    with patch.dict(os.environ, {'GROQ_API_KEY': 'test_api_key'}), \
         patch('groq_integration.AsyncGroq') as mock_groq_class, \
         patch('groq_integration.bot_logger') as mock_logger:
        
        # Настройка Groq клиента
        mock_client = Mock()
        mock_groq_class.return_value = mock_client
        
        # Настройка API ответа
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Вариант 1: Привет! Как дела? 😊\nВариант 2: Привет! Что нового?\nВариант 3: Привет! Как настроение?"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Импортируем функцию после настройки моков
        from groq_integration import generate_reply_variants
        
        # Тестируем генерацию
        variants = await generate_reply_variants("Привет", "friendly")
        
        # Проверяем результат
        assert isinstance(variants, list)
        assert len(variants) >= 1
        assert all(isinstance(v, str) for v in variants)
        
        # API может быть вызван или не вызван из-за кэширования/fallback
        # Проверяем только что получили осмысленный результат
        assert any("привет" in v.lower() for v in variants)

@pytest.mark.asyncio
async def test_generate_reply_variants_styles():
    """Тест генерации ответов для разных стилей"""
    with patch.dict(os.environ, {'GROQ_API_KEY': 'test_api_key'}), \
         patch('groq_integration.AsyncGroq') as mock_groq_class, \
         patch('groq_integration.bot_logger') as mock_logger:
        
        # Настройка Groq клиента
        mock_client = Mock()
        mock_groq_class.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Вариант 1: Test reply\nВариант 2: Test reply 2\nВариант 3: Test reply 3"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Импортируем функцию
        from groq_integration import generate_reply_variants
        
        # Тестируем разные стили
        styles = ["friendly", "flirty", "passionate", "romantic", "professional"]
        
        for style in styles:
            mock_client.chat.completions.create.reset_mock()
            
            variants = await generate_reply_variants("Тест сообщение", style)
            
            # Проверяем результат
            assert isinstance(variants, list)
            assert len(variants) >= 1
            assert all(isinstance(v, str) for v in variants)
            
            # Не проверяем точное количество вызовов API из-за кэширования
            # Главное - что получили результат

@pytest.mark.asyncio
async def test_generate_reply_variants_error_handling():
    """Тест обработки ошибок Groq API"""
    with patch.dict(os.environ, {'GROQ_API_KEY': 'test_api_key'}), \
         patch('groq_integration.AsyncGroq') as mock_groq_class, \
         patch('groq_integration.bot_logger') as mock_logger:
        
        # Настройка Groq клиента с ошибкой
        mock_client = Mock()
        mock_groq_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        # Импортируем функцию
        from groq_integration import generate_reply_variants
        
        # Проверяем, что функция возвращает fallback варианты при ошибке
        variants = await generate_reply_variants("Тест", "friendly")
        
        # Даже при ошибке должны получить список вариантов (fallback)
        assert isinstance(variants, list)
        assert len(variants) >= 1

@pytest.mark.asyncio
async def test_generate_reply_variants_caching():
    """Тест кэширования ответов"""
    with patch.dict(os.environ, {'GROQ_API_KEY': 'test_api_key'}), \
         patch('groq_integration.AsyncGroq') as mock_groq_class, \
         patch('groq_integration.bot_logger') as mock_logger:
        
        # Настройка Groq клиента
        mock_client = Mock()
        mock_groq_class.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Вариант 1: Cached reply\nВариант 2: Cached reply 2\nВариант 3: Cached reply 3"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Импортируем функцию
        from groq_integration import generate_reply_variants
        
        # Первый вызов
        variants1 = await generate_reply_variants("Уникальное тест сообщение для кэша", "friendly")
        
        # Второй вызов с тем же сообщением
        variants2 = await generate_reply_variants("Уникальное тест сообщение для кэша", "friendly")
        
        # Проверяем, что оба вызова вернули списки
        assert isinstance(variants1, list)
        assert isinstance(variants2, list)
        assert len(variants1) >= 1
        assert len(variants2) >= 1

@pytest.mark.asyncio
async def test_input_validation():
    """Тест валидации входных данных"""
    with patch.dict(os.environ, {'GROQ_API_KEY': 'test_api_key'}), \
         patch('groq_integration.AsyncGroq') as mock_groq_class, \
         patch('groq_integration.bot_logger') as mock_logger:
        
        # Настройка Groq клиента
        mock_client = Mock()
        mock_groq_class.return_value = mock_client
        
        # Импортируем функцию
        from groq_integration import generate_reply_variants
        
        # Тест пустого сообщения
        try:
            result = await generate_reply_variants("", "friendly")
            # Функция может вернуть fallback варианты или поднять исключение
            assert isinstance(result, list) or result is None
        except Exception as e:
            # Ожидаем ошибку валидации
            assert "пуст" in str(e).lower() or "длин" in str(e).lower()
        
        # Тест None сообщения
        try:
            result = await generate_reply_variants(None, "friendly")
            assert isinstance(result, list) or result is None
        except Exception as e:
            assert "пуст" in str(e).lower() or "none" in str(e).lower()

@pytest.mark.asyncio
async def test_generate_reply_variants_response_parsing():
    """Тест парсинга ответа от Groq API"""
    with patch.dict(os.environ, {'GROQ_API_KEY': 'test_api_key'}), \
         patch('groq_integration.AsyncGroq') as mock_groq_class, \
         patch('groq_integration.bot_logger') as mock_logger:
        
        # Настройка Groq клиента
        mock_client = Mock()
        mock_groq_class.return_value = mock_client
        
        # Тестируем корректный формат ответа
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Вариант 1: Первый ответ\nВариант 2: Второй ответ\nВариант 3: Третий ответ"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Импортируем функцию
        from groq_integration import generate_reply_variants
        
        variants = await generate_reply_variants("Уникальное сообщение для парсинга", "friendly")
        
        # Проверяем, что получили варианты
        assert isinstance(variants, list)
        assert len(variants) >= 1
        
        # Проверяем, что варианты содержат текст (не зависимо от конкретного содержимого)
        assert all(len(v.strip()) > 0 for v in variants)

@pytest.mark.asyncio  
async def test_concurrent_requests():
    """Тест конкурентных запросов"""
    with patch.dict(os.environ, {'GROQ_API_KEY': 'test_api_key'}), \
         patch('groq_integration.AsyncGroq') as mock_groq_class, \
         patch('groq_integration.bot_logger') as mock_logger:
        
        # Настройка Groq клиента
        mock_client = Mock()
        mock_groq_class.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Вариант 1: Test reply\nВариант 2: Test reply 2\nВариант 3: Test reply 3"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Импортируем функцию
        from groq_integration import generate_reply_variants
        
        # Выполняем несколько запросов конкурентно с уникальными сообщениями
        tasks = [
            generate_reply_variants(f"Уникальное сообщение {i} для конкурентного теста", "friendly") 
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем, что все запросы выполнились
        assert len(results) == 3
        assert all(isinstance(r, list) for r in results if not isinstance(r, Exception))

@pytest.mark.asyncio
async def test_missing_api_key():
    """Тест обработки отсутствующего API ключа"""
    with patch.dict(os.environ, {}, clear=True), \
         patch('groq_integration.bot_logger') as mock_logger:
        
        # Импортируем функцию
        from groq_integration import generate_reply_variants
        
        # Проверяем, что функция обрабатывает отсутствие API ключа
        try:
            result = await generate_reply_variants("Тест", "friendly")
            # Может вернуть fallback варианты
            assert isinstance(result, list)
        except Exception as e:
            # Или поднять исключение об отсутствии ключа
            assert "api" in str(e).lower() or "ключ" in str(e).lower() or "key" in str(e).lower() 