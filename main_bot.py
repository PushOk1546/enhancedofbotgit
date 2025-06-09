#!/usr/bin/env python3
"""
Основной файл для запуска OF Assistant Telegram Bot
"""

import asyncio
import sys
from typing import Optional

try:
    # Обходим проблему с aioredis в Python 3.11+
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Импортируем напрямую необходимые модули
    import telebot
    
    # Создаем прокси для AsyncTeleBot, который импортируется безопасно
    class SafeAsyncTeleBot:
        def __init__(self, token, **kwargs):
            # Отложенный импорт при создании экземпляра
            try:
                from telebot.async_telebot import AsyncTeleBot as _AsyncTeleBot
                self._bot = _AsyncTeleBot(token, **kwargs)
                print("✅ AsyncTeleBot инициализирован")
            except Exception as e:
                print(f"❌ Ошибка инициализации AsyncTeleBot: {e}")
                raise
        
        def __getattr__(self, name):
            return getattr(self._bot, name)
    
    AsyncTeleBot = SafeAsyncTeleBot
    types = telebot.types
    
except ImportError as e:
    print(f"❌ Ошибка: pyTelegramBotAPI не установлен: {e}")
    print("Установите: pip install pyTelegramBotAPI")
    sys.exit(1)
except Exception as e:
    print(f"⚠️ Предупреждение при импорте telebot: {e}")
    print("Попытка использования базового импорта...")
    try:
        import telebot.types as types
        # Создаем минимальную заглушку для тестирования
        class MockAsyncTeleBot:
            def __init__(self, token, **kwargs):
                print("⚠️ Используется mock-версия AsyncTeleBot для тестирования")
                raise RuntimeError("AsyncTeleBot недоступен из-за проблем с зависимостями")
        AsyncTeleBot = MockAsyncTeleBot
    except:
        print("❌ Критическая ошибка: telebot полностью недоступен")
        sys.exit(1)

try:
    from config import config
    from enhanced_logging import BotLogger
    from app.core.error_handler import (
        ErrorHandler,
        TelegramApiError,
        InvalidUserInputError,
        GroqApiError,
        InputValidator,
        handle_bot_errors
    )
    from app.core import state_manager
    from groq_integration import generate_reply_variants
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что все необходимые файлы существуют")
    sys.exit(1)


class TelegramBot:
    """Основной класс Telegram бота"""
    
    def __init__(self):
        """Инициализация бота"""
        # Инициализация логгера
        self.logger = BotLogger(
            log_dir="logs",
            log_file="bot.log",
            logger_name="TelegramBot"
        )
        
        # Инициализация обработчика ошибок
        self.error_handler = ErrorHandler(self.logger)
        
        self.logger.log_info("🤖 Инициализация Telegram бота...")
        
        # Проверка наличия токена
        if not config.TELEGRAM_BOT_TOKEN:
            self.logger.log_error("❌ TELEGRAM_BOT_TOKEN не найден в конфигурации")
            raise ValueError("TELEGRAM_BOT_TOKEN обязателен для работы бота")
        
        # Инициализация асинхронного бота
        try:
            self.bot = AsyncTeleBot(
                token=config.TELEGRAM_BOT_TOKEN,
                parse_mode='HTML'  # Поддержка HTML разметки
            )
            self.logger.log_info("✅ AsyncTeleBot успешно инициализирован")
        except Exception as e:
            self.logger.log_error(f"❌ Ошибка инициализации бота: {e}", exc_info=True)
            raise
        
        # Регистрация обработчиков
        self._register_handlers()
        
        self.logger.log_info("🚀 Бот готов к запуску")
    
    async def _safe_send_message(self, chat_id: int, text: str, **kwargs) -> Optional[types.Message]:
        """Безопасная отправка сообщения с обработкой ошибок"""
        try:
            return await self.bot.send_message(chat_id, text, **kwargs)
        except Exception as e:
            error_result = self.error_handler.handle_error(e, {
                'function': '_safe_send_message',
                'chat_id': chat_id,
                'text_length': len(text)
            })
            self.logger.log_error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
            return None
    
    async def _safe_reply_to(self, message: types.Message, text: str, **kwargs) -> Optional[types.Message]:
        """Безопасный ответ на сообщение с обработкой ошибок"""
        try:
            return await self.bot.reply_to(message, text, **kwargs)
        except Exception as e:
            error_result = self.error_handler.handle_error(e, {
                'function': '_safe_reply_to',
                'user_id': message.from_user.id,
                'text_length': len(text)
            })
            self.logger.log_error(f"Ошибка ответа пользователю {message.from_user.id}: {e}")
            return None
    
    async def _safe_edit_message(self, chat_id: int, message_id: int, text: str, **kwargs) -> bool:
        """Безопасное редактирование сообщения"""
        try:
            await self.bot.edit_message_text(text, chat_id, message_id, **kwargs)
            return True
        except Exception as e:
            self.logger.log_warning(f"Ошибка редактирования сообщения: {e}")
            return False
    
    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        
        @self.bot.message_handler(commands=['start'])
        async def handle_start(message):
            """Асинхронный обработчик команды /start с обработкой ошибок"""
            try:
                # Валидация пользователя
                user_id = InputValidator.validate_user_id(message.from_user.id)
                username = message.from_user.username or "Unknown"
                first_name = message.from_user.first_name or "Пользователь"
                
                # Логируем факт вызова команды с user_id через BotLogger
                self.logger.log_user_activity(
                    user_id, 
                    "start_command", 
                    {
                        "username": username, 
                        "first_name": first_name,
                        "chat_id": message.chat.id,
                        "chat_type": message.chat.type
                    }
                )
                
                # Приветственное сообщение согласно требованиям
                welcome_text = (
                    "Привет! Я бот, который поможет тебе генерировать варианты ответов "
                    "с помощью AI Groq. Используй /reply <твое сообщение> для начала. "
                    "/help - для справки."
                )
                
                result = await self._safe_reply_to(message, welcome_text)
                
                if result:
                    # Дополнительное логирование успешной отправки сообщения
                    self.logger.log_info(f"✅ Приветственное сообщение отправлено пользователю {user_id} (@{username})")
                
            except InvalidUserInputError as e:
                self.logger.log_warning(f"Неверные данные пользователя в /start: {e}")
                await self._safe_reply_to(message, "❌ Ошибка данных пользователя.")
            except Exception as e:
                error_result = self.error_handler.handle_error(e, {
                    'function': 'handle_start',
                    'user_id': getattr(message.from_user, 'id', 'unknown')
                })
                
                await self._safe_reply_to(message, error_result['user_message'])
        
        @self.bot.message_handler(commands=['help'])
        async def handle_help(message):
            """Асинхронный обработчик команды /help с обработкой ошибок"""
            try:
                user_id = InputValidator.validate_user_id(message.from_user.id)
                username = message.from_user.username or "Unknown"
                
                # Логируем использование команды
                self.logger.log_user_activity(user_id, "help_command", {"username": username})
                
                # Справочное сообщение согласно требованиям
                help_text = (
                    "📚 <b>Справка по командам бота:</b>\n\n"
                    "🚀 <b>/start</b> - начало работы\n"
                    "❓ <b>/help</b> - эта справка\n"
                    "💬 <b>/reply &lt;сообщение&gt;</b> - сгенерировать варианты ответов\n"
                    "📊 <b>/stats</b> - ваша статистика\n\n"
                    "💡 <b>Пример использования:</b>\n"
                    "<code>/reply Привет, как дела?</code>\n\n"
                    "🤖 Я создам несколько вариантов ответов с помощью AI Groq!"
                )
                
                result = await self._safe_reply_to(message, help_text, parse_mode='HTML')
                
                if result:
                    self.logger.log_info(f"✅ Справка отправлена пользователю {user_id} (@{username})")
                
            except Exception as e:
                error_result = self.error_handler.handle_error(e, {
                    'function': 'handle_help',
                    'user_id': getattr(message.from_user, 'id', 'unknown')
                })
                
                await self._safe_reply_to(message, error_result['user_message'])
        
        @self.bot.message_handler(commands=['reply'])
        async def handle_reply(message):
            """Асинхронный обработчик команды /reply с обработкой ошибок"""
            try:
                user_id = InputValidator.validate_user_id(message.from_user.id)
                username = message.from_user.username or "Unknown"
                
                # Получаем текст после команды /reply
                text_parts = message.text.split(' ', 1)
                
                if len(text_parts) < 2:
                    # Если текст не указан
                    raise InvalidUserInputError(
                        "Необходимо указать сообщение после команды /reply",
                        user_input=message.text,
                        validation_rule="reply_message_required"
                    )
                
                user_message = text_parts[1].strip()
                
                # Валидация длины сообщения
                InputValidator.validate_message_length(user_message, config.MAX_MESSAGE_LENGTH)
                
                # Увеличиваем счетчик запросов /reply для статистики
                reply_count = await state_manager.increment_user_stat(user_id, 'reply_requests')
                
                # Логируем использование команды
                self.logger.log_user_activity(
                    user_id, 
                    "reply_command", 
                    {
                        "username": username,
                        "message_length": len(user_message),
                        "reply_count": reply_count,
                        "original_message": user_message[:100] + "..." if len(user_message) > 100 else user_message
                    }
                )
                
                # Создаем хеш сообщения для связи с callback
                import hashlib
                message_hash = hashlib.md5(user_message.encode()).hexdigest()[:8]
                
                # Сохраняем сообщение в StateManager
                await state_manager.set_user_message(message_hash, user_id, user_message)
                await state_manager.set_last_message_for_reply(user_id, user_message, message_hash)
                
                # Создаем inline клавиатуру для выбора стиля
                markup = types.InlineKeyboardMarkup()
                styles = [
                    ("Дружелюбный", "friendly"),
                    ("Флиртующий", "flirty"),
                    ("Страстный", "passionate"),
                    ("Романтичный", "romantic"),
                    ("Профессиональный", "professional")
                ]
                
                for style_name, style_code in styles:
                    callback_data = f"style:{style_code}:{message_hash}"
                    markup.add(types.InlineKeyboardButton(style_name, callback_data=callback_data))
                
                # Отправляем сообщение с выбором стиля
                reply_text = (
                    f"💬 <b>Ваше сообщение:</b>\n"
                    f"<i>\"{user_message}\"</i>\n\n"
                    f"🎨 <b>Выберите стиль ответа:</b>"
                )
                
                result = await self._safe_reply_to(message, reply_text, reply_markup=markup, parse_mode='HTML')
                
                if result:
                    self.logger.log_info(f"✅ Меню выбора стиля отправлено пользователю {user_id}")
                
            except InvalidUserInputError as e:
                # Отправляем помощь если ошибка валидации
                help_text = (
                    "❓ Пожалуйста, укажите сообщение после команды /reply\n\n"
                    "📝 Пример: /reply Привет, как дела?\n\n"
                    "Я создам несколько вариантов ответов с помощью AI Groq!"
                )
                await self._safe_reply_to(message, help_text)
                
                self.logger.log_warning(f"Неверный ввод от пользователя {message.from_user.id}: {e}")
                
            except Exception as e:
                error_result = self.error_handler.handle_error(e, {
                    'function': 'handle_reply',
                    'user_id': getattr(message.from_user, 'id', 'unknown'),
                    'message_text': getattr(message, 'text', '')[:100]
                })
                
                await self._safe_reply_to(message, error_result['user_message'])
        
        @self.bot.message_handler(commands=['stats'])
        async def handle_stats(message):
            """Обработчик команды /stats с обработкой ошибок"""
            try:
                user_id = InputValidator.validate_user_id(message.from_user.id)
                username = message.from_user.username or "Unknown"
                
                self.logger.log_user_activity(user_id, "stats_command", {"username": username})
                
                # Получаем статистику пользователя из StateManager
                reply_requests = await state_manager.get_user_stat(user_id, 'reply_requests')
                replies_selected = await state_manager.get_user_stat(user_id, 'replies_selected')
                user_stats = await state_manager.get_user_stats(user_id)
                
                # Формируем сообщение со статистикой
                if reply_requests > 0:
                    completion_rate = (replies_selected / reply_requests * 100) if reply_requests > 0 else 0
                    stats_text = (
                        f"📊 <b>Ваша статистика</b>\n\n"
                        f"👤 <b>Пользователь:</b> {message.from_user.first_name or 'Пользователь'}\n"
                        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                        f"📝 <b>Username:</b> @{username}\n\n"
                        f"📈 <b>Активность:</b>\n"
                        f"💬 Запросов /reply: <b>{reply_requests}</b>\n"
                        f"✅ Выбрано ответов: <b>{replies_selected}</b>\n"
                        f"📋 Завершенность: <b>{completion_rate:.1f}%</b>\n"
                        f"🎯 Статус: {'🔥 Активный пользователь!' if reply_requests >= 5 else '✨ Новичок'}\n\n"
                        f"{'🏆 Отлично! Вы активно используете бота!' if reply_requests >= 10 else '💡 Попробуйте команду /reply с разными сообщениями!'}"
                    )
                else:
                    stats_text = (
                        f"📊 <b>Добро пожаловать!</b>\n\n"
                        f"👤 <b>Пользователь:</b> {message.from_user.first_name or 'Пользователь'}\n"
                        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                        f"📝 <b>Username:</b> @{username}\n\n"
                        f"📈 <b>Активность:</b>\n"
                        f"💬 Запросов /reply: <b>0</b>\n"
                        f"🎯 Статус: 🆕 Новичок\n\n"
                        f"💡 Статистика пока в разработке. Но вы уже молодец!\n"
                        f"🚀 Попробуйте команду /reply для создания ответов с помощью AI!"
                    )
                
                result = await self._safe_reply_to(message, stats_text, parse_mode='HTML')
                
                if result:
                    self.logger.log_info(f"✅ Статистика отправлена пользователю {user_id} (запросов /reply: {reply_requests})")
                
            except Exception as e:
                error_result = self.error_handler.handle_error(e, {
                    'function': 'handle_stats',
                    'user_id': getattr(message.from_user, 'id', 'unknown')
                })
                
                await self._safe_reply_to(message, error_result['user_message'])
        
        @self.bot.message_handler(commands=['ppv'])
        async def handle_ppv(message):
            """Обработчик команды /ppv с обработкой ошибок"""
            try:
                user_id = InputValidator.validate_user_id(message.from_user.id)
                username = message.from_user.username or "Unknown"
                
                self.logger.log_user_activity(user_id, "ppv_command", {"username": username})
                
                # MVP сообщение о том, что функция в разработке
                ppv_text = (
                    f"🔒 <b>PPV Контент</b>\n\n"
                    f"🚧 Функция PPV контента находится в разработке.\n\n"
                    f"📅 Скоро здесь будут доступны:\n"
                    f"• Платный контент\n"
                    f"• Персональные сообщения\n" 
                    f"• Эксклюзивные материалы\n\n"
                    f"🔔 Следите за обновлениями!"
                )
                
                result = await self._safe_reply_to(message, ppv_text, parse_mode='HTML')
                
                if result:
                    self.logger.log_info(f"✅ PPV сообщение отправлено пользователю {user_id}")
                
            except Exception as e:
                error_result = self.error_handler.handle_error(e, {
                    'function': 'handle_ppv',
                    'user_id': getattr(message.from_user, 'id', 'unknown')
                })
                
                await self._safe_reply_to(message, error_result['user_message'])
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('style:'))
        async def handle_style_callback(call):
            """Обработчик выбора стиля ответа с обработкой ошибок"""
            try:
                user_id = InputValidator.validate_user_id(call.from_user.id)
                
                # Парсим callback_data: style:style_code:message_hash
                parts = call.data.split(':')
                if len(parts) != 3:
                    raise InvalidUserInputError("Неверный формат callback данных")
                
                _, style_code, message_hash = parts
                
                # Валидируем стиль
                InputValidator.validate_style(style_code)
                
                # Получаем исходное сообщение
                stored_message = await state_manager.get_user_message(message_hash)
                if not stored_message:
                    raise InvalidUserInputError("Сообщение не найдено или истекло")
                
                user_message = stored_message['message']
                
                self.logger.log_user_activity(user_id, "style_selected", {
                    "style": style_code,
                    "message_hash": message_hash
                })
                
                # Проверяем кэш
                from app.core import memory_cache
                cache_key = memory_cache.get_cache_key(style_code, hashlib.md5(user_message.encode()).hexdigest())
                cached_variants = memory_cache.get(cache_key)
                
                if cached_variants:
                    self.logger.log_info(f"Использование кэшированных вариантов для пользователя {user_id}")
                    variants = cached_variants
                else:
                    # Отправляем сообщение о генерации
                    processing_text = "🤖 Генерирую варианты ответов с помощью AI Groq... ⏳"
                    processing_msg = await self.bot.edit_message_text(
                        processing_text, 
                        call.message.chat.id, 
                        call.message.message_id
                    )
                    
                    try:
                        # Генерируем варианты через Groq API
                        variants = await generate_reply_variants(user_message, style_code)
                        
                        if not variants or len(variants) == 0:
                            raise GroqApiError("Получен пустой список вариантов от API")
                        
                        # Сохраняем в кэш
                        memory_cache.set(cache_key, variants)
                        
                        self.logger.log_api_call("Groq API успешный вызов", {
                            "style": style_code,
                            "variants_count": len(variants),
                            "user_id": user_id
                        })
                        
                    except GroqApiError as groq_error:
                        self.logger.log_error(f"Ошибка Groq API для пользователя {user_id}: {groq_error}")
                        
                        # Используем fallback варианты
                        fallback_variants = [
                            "Спасибо за сообщение! 😊",
                            "Интересно, расскажи больше! 💕",
                            "Отличное сообщение! 🌟"
                        ]
                        variants = fallback_variants
                        
                        # Уведомляем пользователя
                        error_text = (
                            "⚠️ Сервис AI временно недоступен.\n"
                            "Показываю базовые варианты ответов:"
                        )
                        await self._safe_edit_message(call.message.chat.id, call.message.message_id, error_text)
                        await asyncio.sleep(2)  # Пауза перед показом вариантов
                
                # Сохраняем варианты в state manager
                await state_manager.set_reply_variants(user_id, message_hash, variants)
                
                # Создаем клавиатуру для выбора варианта
                markup = types.InlineKeyboardMarkup()
                for i, variant in enumerate(variants):
                    callback_data = f"select_reply:{i}:{message_hash}"
                    button_text = f"{i+1}. {variant[:50]}{'...' if len(variant) > 50 else ''}"
                    markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
                
                # Формируем сообщение с вариантами
                style_names = {
                    'friendly': 'Дружелюбный',
                    'flirty': 'Флиртующий', 
                    'passionate': 'Страстный',
                    'romantic': 'Романтичный',
                    'professional': 'Профессиональный'
                }
                
                variants_text = (
                    f"🎨 <b>Стиль:</b> {style_names.get(style_code, style_code)}\n\n"
                    f"💬 <b>Варианты ответов:</b>\n\n"
                )
                
                for i, variant in enumerate(variants):
                    variants_text += f"<b>{i+1}.</b> {variant}\n\n"
                
                variants_text += "👆 <b>Выберите понравившийся вариант:</b>"
                
                await self._safe_edit_message(
                    call.message.chat.id, 
                    call.message.message_id, 
                    variants_text, 
                    reply_markup=markup, 
                    parse_mode='HTML'
                )
                
                # Отвечаем на callback
                await self.bot.answer_callback_query(call.id, f"✅ Стиль '{style_names.get(style_code)}' выбран!")
                
            except InvalidUserInputError as e:
                await self.bot.answer_callback_query(call.id, f"❌ {e.message}", show_alert=True)
                self.logger.log_warning(f"Ошибка валидации в style callback: {e}")
                
            except GroqApiError as e:
                await self.bot.answer_callback_query(call.id, "⚠️ Сервис AI недоступен", show_alert=True)
                self.logger.log_error(f"Ошибка Groq API в style callback: {e}")
                
            except Exception as e:
                error_result = self.error_handler.handle_error(e, {
                    'function': 'handle_style_callback',
                    'user_id': getattr(call.from_user, 'id', 'unknown'),
                    'callback_data': call.data
                })
                
                await self.bot.answer_callback_query(
                    call.id, 
                    error_result['user_message'][:200],  # Ограничение длины callback ответа
                    show_alert=True
                )
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('select_reply:'))
        async def handle_select_reply_callback(call):
            """Обработчик выбора конкретного варианта ответа с обработкой ошибок"""
            try:
                user_id = InputValidator.validate_user_id(call.from_user.id)
                
                # Парсим callback_data: select_reply:variant_index:message_hash
                parts = call.data.split(':')
                if len(parts) != 3:
                    raise InvalidUserInputError("Неверный формат callback данных")
                
                _, variant_index_str, message_hash = parts
                
                try:
                    variant_index = int(variant_index_str)
                except ValueError:
                    raise InvalidUserInputError("Неверный индекс варианта")
                
                # Получаем сохраненные варианты
                variants = await state_manager.get_reply_variants(user_id, message_hash)
                if not variants:
                    raise InvalidUserInputError("Варианты ответов не найдены")
                
                if variant_index < 0 or variant_index >= len(variants):
                    raise InvalidUserInputError("Неверный индекс варианта")
                
                selected_variant = variants[variant_index]
                
                # Получаем данные об исходном сообщении для дополнительного контекста
                original_message_data = await state_manager.get_last_message_for_reply(user_id)
                original_message_text = original_message_data.get('text') if original_message_data else None
                
                # Увеличиваем счетчик успешно выбранных ответов
                selected_count = await state_manager.increment_user_stat(user_id, 'replies_selected')
                
                self.logger.log_user_activity(user_id, "reply_selected", {
                    "variant_index": variant_index + 1,  # Для логов используем 1-based индекс
                    "message_hash": message_hash,
                    "selected_text": selected_variant[:100],
                    "full_text_length": len(selected_variant),
                    "selected_count": selected_count,
                    "original_message_preview": original_message_text[:50] if original_message_text else None
                })
                
                # Отправляем выбранный текст как обычное сообщение пользователю
                final_message = (
                    f"💌 <b>Ваш выбранный ответ:</b>\n\n"
                    f"<blockquote>{selected_variant}</blockquote>\n\n"
                    f"📋 <i>Готово! Скопируйте текст выше и используйте как ответ.</i>"
                )
                
                # Отправляем новое сообщение с выбранным текстом
                await self._safe_send_message(
                    call.message.chat.id, 
                    final_message,
                    parse_mode='HTML'
                )
                
                # Обновляем исходное сообщение с подтверждением выбора
                confirmation_text = (
                    f"✅ <b>Вариант #{variant_index + 1} выбран!</b>\n\n"
                    f"📨 Ответ отправлен выше отдельным сообщением.\n\n"
                    f"🔄 Используйте /reply для создания новых вариантов."
                )
                
                await self._safe_edit_message(
                    call.message.chat.id, 
                    call.message.message_id, 
                    confirmation_text, 
                    parse_mode='HTML'
                )
                
                # Очищаем временные данные
                await state_manager.clear_reply_variants(user_id, message_hash)
                await state_manager.delete_user_message(message_hash)
                
                # Отвечаем на callback
                await self.bot.answer_callback_query(call.id, f"✅ Вариант #{variant_index + 1} отправлен!")
                
            except InvalidUserInputError as e:
                await self.bot.answer_callback_query(call.id, f"❌ {e.message}", show_alert=True)
                self.logger.log_warning(f"Ошибка валидации в select reply callback: {e}")
                
            except Exception as e:
                error_result = self.error_handler.handle_error(e, {
                    'function': 'handle_select_reply_callback',
                    'user_id': getattr(call.from_user, 'id', 'unknown'),
                    'callback_data': call.data
                })
                
                await self.bot.answer_callback_query(
                    call.id, 
                    error_result['user_message'][:200],
                    show_alert=True
                )
    
    async def start_polling(self):
        """Запуск polling с обработкой ошибок"""
        try:
            self.logger.log_info("🚀 Запуск polling режима...")
            await self.bot.polling(non_stop=True)
        except Exception as e:
            error_result = self.error_handler.handle_error(e, {
                'function': 'start_polling'
            })
            self.logger.log_error(f"❌ Критическая ошибка polling: {e}")
            raise
    
    async def stop(self):
        """Остановка бота с обработкой ошибок"""
        try:
            self.logger.log_info("🛑 Остановка бота...")
            await self.bot.stop_polling()
            self.logger.log_info("✅ Бот остановлен")
        except Exception as e:
            self.logger.log_error(f"❌ Ошибка остановки бота: {e}")


async def main():
    """Главная функция с обработкой ошибок"""
    # Проверка Python версии
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    print("🤖 OF Assistant Telegram Bot")
    print(f"🐍 Python {sys.version}")
    print("=" * 50)
    
    bot = None
    try:
        # Создание и запуск бота
        bot = TelegramBot()
        
        print("✅ Бот инициализирован успешно")
        print("🚀 Запуск в режиме polling...")
        print("📝 Нажмите Ctrl+C для остановки")
        print("=" * 50)
        
        await bot.start_polling()
        
    except KeyboardInterrupt:
        print("\n⏹️ Получен сигнал остановки...")
        if bot:
            await bot.stop()
        print("👋 Бот остановлен пользователем")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        if bot and hasattr(bot, 'logger'):
            bot.logger.log_error(f"Критическая ошибка в main: {e}", exc_info=True)
        if bot:
            await bot.stop()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Фатальная ошибка: {e}")
        sys.exit(1) 