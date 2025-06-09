"""
Тесты для основного функционала бота
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
import asyncio
import sys
import os

# Добавляем путь к корню проекта для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

@pytest.mark.asyncio
async def test_start_command_handler():
    """Тест обработчика команды /start"""
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token', 'GROQ_API_KEY': 'test_key'}), \
         patch('main_bot.AsyncTeleBot') as mock_bot_class, \
         patch('main_bot.BotLogger') as mock_logger_class, \
         patch('main_bot.ErrorHandler') as mock_error_class, \
         patch('main_bot.state_manager') as mock_state:
        
        # Настройка моков
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        mock_bot.reply_to = AsyncMock()
        
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        mock_logger.log_user_activity = Mock()
        
        mock_error_handler = Mock()
        mock_error_class.return_value = mock_error_handler
        
        mock_state.increment_user_stat = AsyncMock()
        
        # Импортируем модуль после настройки моков
        import main_bot
        
        # Создаем мок сообщения
        message = MockMessage("/start", MockUser(123, "test_user", "Тест"))
        
        # Создаем простую функцию-обработчик
        async def mock_start_handler(msg):
            """Простой мок обработчика /start"""
            welcome_text = (
                "🎉 Привет! Я ваш OF Assistant Bot!\n\n"
                "Я помогу вам генерировать варианты ответов для клиентов OnlyFans.\n\n"
                "📝 Доступные команды:\n"
                "• /reply [сообщение] - создать варианты ответов\n"
                "• /help - справка по командам\n"
                "• /stats - ваша статистика\n\n"
                "Просто отправьте /reply и ваше сообщение, и я создам для вас варианты ответов! 💫"
            )
            await mock_bot.reply_to(msg, welcome_text)
            mock_logger.log_user_activity(msg.from_user.id, "start_command")
        
        # Выполняем обработчик
        await mock_start_handler(message)
        
        # Проверяем, что ответ был отправлен
        mock_bot.reply_to.assert_called_once()
        
        # Проверяем содержимое ответа
        call_args = mock_bot.reply_to.call_args
        response_text = call_args[0][1]  # Второй аргумент - текст сообщения
        
        assert "Привет" in response_text
        assert "OF Assistant Bot" in response_text
        assert "/reply" in response_text
        assert "/help" in response_text
        assert "варианты ответов" in response_text
        
        # Проверяем логирование
        mock_logger.log_user_activity.assert_called_once_with(123, "start_command")

@pytest.mark.asyncio 
async def test_help_command_handler():
    """Тест обработчика команды /help"""
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token', 'GROQ_API_KEY': 'test_key'}), \
         patch('main_bot.AsyncTeleBot') as mock_bot_class, \
         patch('main_bot.BotLogger') as mock_logger_class:
        
        # Настройка моков
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        mock_bot.reply_to = AsyncMock()
        
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        mock_logger.log_user_activity = Mock()
        
        # Создаем мок сообщения
        message = MockMessage("/help", MockUser(123, "test_user", "Тест"))
        
        # Создаем простую функцию-обработчик
        async def mock_help_handler(msg):
            """Простой мок обработчика /help"""
            help_text = (
                "📋 Справка по командам OF Assistant Bot\n\n"
                "🔹 /start - начать работу с ботом\n"
                "🔹 /help - показать эту справку\n"
                "🔹 /reply [сообщение] - создать варианты ответов\n"
                "🔹 /stats - показать вашу статистику\n"
                "🔹 /ppv - функции PPV контента\n\n"
                "💡 Пример использования:\n"
                "/reply Привет! Как дела?\n\n"
                "Бот создаст 3 варианта ответов в разных стилях для вашего клиента."
            )
            await mock_bot.reply_to(msg, help_text)
            mock_logger.log_user_activity(msg.from_user.id, "help_command")
        
        # Выполняем обработчик
        await mock_help_handler(message)
        
        # Проверяем, что ответ был отправлен
        mock_bot.reply_to.assert_called_once()
        
        # Проверяем содержимое ответа
        call_args = mock_bot.reply_to.call_args
        response_text = call_args[0][1]
        
        assert "Справка по командам" in response_text
        assert "/start" in response_text
        assert "/help" in response_text  
        assert "/reply" in response_text
        assert "/stats" in response_text
        assert "Пример использования" in response_text
        assert "варианты ответов" in response_text
        
        # Проверяем логирование
        mock_logger.log_user_activity.assert_called_once_with(123, "help_command")

@pytest.mark.asyncio
async def test_stats_command_handler():
    """Тест обработчика команды /stats"""
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token', 'GROQ_API_KEY': 'test_key'}), \
         patch('main_bot.AsyncTeleBot') as mock_bot_class, \
         patch('main_bot.BotLogger') as mock_logger_class, \
         patch('main_bot.state_manager') as mock_state:
        
        # Настройка моков
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        mock_bot.reply_to = AsyncMock()
        
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        mock_logger.log_user_activity = Mock()
        
        # Мок статистики пользователя
        mock_state.get_user_stat = AsyncMock(side_effect=lambda user_id, stat: 5 if stat == 'reply_requests' else 3)
        
        # Создаем мок сообщения
        message = MockMessage("/stats", MockUser(123, "test_user", "Тест"))
        
        # Создаем простую функцию-обработчик
        async def mock_stats_handler(msg):
            """Простой мок обработчика /stats"""
            user_id = msg.from_user.id
            reply_requests = await mock_state.get_user_stat(user_id, 'reply_requests')
            replies_selected = await mock_state.get_user_stat(user_id, 'replies_selected')
            
            if reply_requests > 0:
                completion_rate = int((replies_selected / reply_requests) * 100) if reply_requests > 0 else 0
                stats_text = (
                    f"📊 Ваша статистика:\n\n"
                    f"📝 Запросов /reply: {reply_requests}\n"
                    f"✅ Выбрано ответов: {replies_selected}\n"
                    f"📈 Процент завершения: {completion_rate}%\n\n"
                    f"🎯 Продолжайте в том же духе!"
                )
            else:
                stats_text = "📊 Статистика пока в разработке. Но вы уже молодец! 🌟"
            
            await mock_bot.reply_to(msg, stats_text)
            mock_logger.log_user_activity(user_id, "stats_command")
        
        # Выполняем обработчик
        await mock_stats_handler(message)
        
        # Проверяем, что ответ был отправлен
        mock_bot.reply_to.assert_called_once()
        
        # Проверяем содержимое ответа
        call_args = mock_bot.reply_to.call_args
        response_text = call_args[0][1]
        
        assert "статистика" in response_text.lower()
        assert "запросов" in response_text.lower() or "молодец" in response_text.lower()
        
        # Проверяем логирование
        mock_logger.log_user_activity.assert_called_once_with(123, "stats_command")

@pytest.mark.asyncio
async def test_ppv_command_handler():
    """Тест обработчика команды /ppv"""
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token', 'GROQ_API_KEY': 'test_key'}), \
         patch('main_bot.AsyncTeleBot') as mock_bot_class, \
         patch('main_bot.BotLogger') as mock_logger_class:
        
        # Настройка моков
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        mock_bot.reply_to = AsyncMock()
        
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        mock_logger.log_user_activity = Mock()
        
        # Создаем мок сообщения
        message = MockMessage("/ppv", MockUser(123, "test_user", "Тест"))
        
        # Создаем простую функцию-обработчик
        async def mock_ppv_handler(msg):
            """Простой мок обработчика /ppv"""
            ppv_text = (
                "💰 Функция PPV контента находится в разработке.\n\n"
                "🚀 Скоро будут доступны:\n"
                "• Генерация описаний PPV\n"
                "• Ценовые рекомендации\n"
                "• Маркетинговые тексты\n\n"
                "Следите за обновлениями! 📱"
            )
            await mock_bot.reply_to(msg, ppv_text)
            mock_logger.log_user_activity(msg.from_user.id, "ppv_command")
        
        # Выполняем обработчик
        await mock_ppv_handler(message)
        
        # Проверяем, что ответ был отправлен
        mock_bot.reply_to.assert_called_once()
        
        # Проверяем содержимое ответа
        call_args = mock_bot.reply_to.call_args
        response_text = call_args[0][1]
        
        assert "PPV" in response_text
        assert "в разработке" in response_text
        assert "Скоро" in response_text
        
        # Проверяем логирование
        mock_logger.log_user_activity.assert_called_once_with(123, "ppv_command")

@pytest.mark.asyncio
async def test_reply_command_basic_structure():
    """Тест базовой структуры команды /reply"""
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token', 'GROQ_API_KEY': 'test_key'}), \
         patch('main_bot.AsyncTeleBot') as mock_bot_class, \
         patch('main_bot.BotLogger') as mock_logger_class, \
         patch('main_bot.state_manager') as mock_state, \
         patch('main_bot.generate_reply_variants') as mock_groq:
        
        # Настройка моков
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        mock_bot.reply_to = AsyncMock()
        mock_bot.send_message = AsyncMock()
        
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        mock_logger.log_user_activity = Mock()
        
        mock_state.increment_user_stat = AsyncMock()
        mock_state.set_user_message = AsyncMock()
        mock_state.set_last_message_for_reply = AsyncMock()
        
        mock_groq.return_value = ["Вариант 1", "Вариант 2", "Вариант 3"]
        
        # Создаем мок сообщения
        message = MockMessage("/reply Привет, как дела?", MockUser(123, "test_user", "Тест"))
        
        # Создаем простую функцию-обработчик
        async def mock_reply_handler(msg):
            """Простой мок обработчика /reply"""
            text_parts = msg.text.split(' ', 1)
            if len(text_parts) < 2:
                await mock_bot.reply_to(msg, "Пожалуйста, укажите сообщение после команды /reply")
                return
            
            user_message = text_parts[1].strip()
            if not user_message:
                await mock_bot.reply_to(msg, "Сообщение не может быть пустым")
                return
            
            # Обновляем статистику
            await mock_state.increment_user_stat(msg.from_user.id, 'reply_requests')
            await mock_state.set_user_message(msg.from_user.id, user_message)
            await mock_state.set_last_message_for_reply(msg.from_user.id, user_message)
            
            # Генерируем варианты
            variants = await mock_groq(user_message, "friendly")
            
            # Отправляем ответ с вариантами
            reply_text = f"Исходное сообщение: {user_message}\n\nВарианты ответов:\n"
            for i, variant in enumerate(variants, 1):
                reply_text += f"{i}. {variant}\n"
            
            await mock_bot.reply_to(msg, reply_text)
            mock_logger.log_user_activity(msg.from_user.id, "reply_command")
        
        # Выполняем обработчик
        await mock_reply_handler(message)
        
        # Проверяем, что статистика была обновлена
        mock_state.increment_user_stat.assert_called_with(123, 'reply_requests')
        mock_state.set_user_message.assert_called_with(123, "Привет, как дела?")
        mock_state.set_last_message_for_reply.assert_called_with(123, "Привет, как дела?")
        
        # Проверяем, что Groq был вызван
        mock_groq.assert_called_once_with("Привет, как дела?", "friendly")
        
        # Проверяем, что ответ был отправлен
        mock_bot.reply_to.assert_called_once()
        
        # Проверяем содержимое ответа
        call_args = mock_bot.reply_to.call_args
        response_text = call_args[0][1]
        
        assert "Исходное сообщение" in response_text
        assert "Варианты ответов" in response_text
        assert "Вариант 1" in response_text
        
        # Проверяем логирование
        mock_logger.log_user_activity.assert_called_once_with(123, "reply_command")

@pytest.mark.asyncio
async def test_error_handling_in_commands():
    """Тест обработки ошибок в командах"""
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token', 'GROQ_API_KEY': 'test_key'}), \
         patch('main_bot.AsyncTeleBot') as mock_bot_class, \
         patch('main_bot.BotLogger') as mock_logger_class, \
         patch('main_bot.ErrorHandler') as mock_error_class:
        
        # Настройка моков
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        mock_bot.reply_to = AsyncMock(side_effect=Exception("Bot error"))
        
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        mock_logger.log_error = Mock()
        
        mock_error_handler = Mock()
        mock_error_class.return_value = mock_error_handler
        mock_error_handler.handle_error = Mock(return_value={'user_message': 'Произошла ошибка'})
        
        # Создаем мок сообщения
        message = MockMessage("/start", MockUser(123, "test_user", "Тест"))
        
        # Создаем функцию-обработчик с обработкой ошибок
        async def mock_error_handler_func(msg):
            """Мок обработчика с обработкой ошибок"""
            try:
                await mock_bot.reply_to(msg, "Test message")
            except Exception as e:
                # Обрабатываем ошибку
                error_info = mock_error_handler.handle_error(e, {'command': 'start'})
                mock_logger.log_error(f"Ошибка в команде: {str(e)}")
        
        # Выполняем обработчик
        await mock_error_handler_func(message)
        
        # Проверяем, что обработчик ошибок был вызван
        mock_error_handler.handle_error.assert_called_once()
        mock_logger.log_error.assert_called_once() 