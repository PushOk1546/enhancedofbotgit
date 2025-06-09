"""
Основной файл OF Assistant Bot.
Использует pyTelegramBotAPI (telebot) вместо python-telegram-bot.
"""

import logging
import asyncio
import signal
import sys
from typing import Optional, Dict, Any
from telebot.async_telebot import AsyncTeleBot
from telebot import types, asyncio_helper
from dotenv import load_dotenv

# Импорты модулей проекта
from config.config import BOT_TOKEN, MODELS, SURVEY_STEPS, GROQ_KEY, FLIRT_STYLES, PPV_STYLES
from utils import (
    setup_logging, get_model_keyboard, get_survey_keyboard, 
    get_flirt_style_keyboard, get_main_keyboard, get_ppv_style_keyboard,
    get_relationship_stage_keyboard, get_quick_continue_keyboard,
    get_smart_continuation_keyboard
)
from state_manager import StateManager
from handlers import (
    handle_start_command,
    handle_model_command,
    handle_flirt_command,
    handle_ppv_command,
    handle_set_ppv_reminder_command,
    set_state_manager
)
from api import generate_groq_response
from chat_handlers import ChatHandlers

# Инициализация логгера
logger = setup_logging()

class BotManager:
    """Основной класс для управления OF Assistant Bot"""
    
    def __init__(self):
        self.bot: Optional[AsyncTeleBot] = None
        self.state_manager: Optional[StateManager] = None
        self.is_running = False
        self._shutdown_event = asyncio.Event()
        self.chat_handlers: Optional[ChatHandlers] = None
        
    async def initialize(self) -> bool:
        """Инициализация бота с проверкой всех компонентов"""
        try:
            # Валидация конфигурации
            if not self._validate_config():
                return False
            
            # Загружаем настройки
            load_dotenv()
            
            # Настройка таймаутов для telebot
            asyncio_helper.SESSION_TIME_TO_LIVE = 5 * 60  # 5 минут
            
            # Инициализация бота
            self.bot = AsyncTeleBot(BOT_TOKEN, parse_mode='HTML')
            
            # Создаем менеджер состояний
            self.state_manager = StateManager()
            
            # Передаем state_manager в handlers
            set_state_manager(self.state_manager)
            
            # Инициализируем обработчики чатов
            self.chat_handlers = ChatHandlers(self.state_manager)
            
            # Регистрация обработчиков
            self._register_handlers()
            
            # Настройка graceful shutdown
            self._setup_signal_handlers()
            
            logger.info("✅ OF Assistant Bot initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {str(e)}", exc_info=True)
            return False
    
    def _validate_config(self) -> bool:
        """Валидация конфигурации бота"""
        errors = []
        
        if not BOT_TOKEN:
            errors.append("BOT_TOKEN is not set")
        elif not BOT_TOKEN.strip():
            errors.append("BOT_TOKEN is empty")
        elif len(BOT_TOKEN.split(':')) != 2:
            errors.append("BOT_TOKEN has invalid format")
            
        if not GROQ_KEY:
            errors.append("GROQ_KEY is not set")
        elif not GROQ_KEY.strip():
            errors.append("GROQ_KEY is empty")
            
        if not MODELS:
            errors.append("MODELS configuration is empty")
            
        if errors:
            for error in errors:
                logger.error(f"❌ Configuration error: {error}")
            return False
            
        logger.info("✅ Configuration validation passed")
        return True
    
    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        
        # Обработчики команд
        @self.bot.message_handler(commands=['start'])
        async def start_handler(message):
            await self._safe_handler_execution(
                handle_start_command, self.bot, message
            )

        @self.bot.message_handler(commands=['model'])
        async def model_handler(message):
            await self._safe_handler_execution(
                handle_model_command, self.bot, message
            )

        @self.bot.message_handler(commands=['flirt'])
        async def flirt_handler(message):
            await self._safe_handler_execution(
                handle_flirt_command, self.bot, message
            )

        @self.bot.message_handler(commands=['ppv'])
        async def ppv_handler(message):
            await self._safe_handler_execution(
                handle_ppv_command, self.bot, message
            )

        @self.bot.message_handler(commands=['set_ppv_reminder'])
        async def set_ppv_reminder_handler(message):
            await self._safe_handler_execution(
                handle_set_ppv_reminder_command, self.bot, message
            )

        # Обработчик callback-кнопок
        @self.bot.callback_query_handler(func=lambda call: True)
        async def callback_query_handler(call):
            await self._handle_callback_query(call)

        # Обработчик текстовых сообщений
        @self.bot.message_handler(content_types=['text'])
        async def text_handler(message):
            await self._handle_text_message(message)
    
    async def _safe_handler_execution(self, handler_func, *args, **kwargs):
        """Безопасное выполнение обработчика с логированием ошибок"""
        try:
            await handler_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in handler {handler_func.__name__}: {str(e)}", exc_info=True)
            # Попытка отправить сообщение об ошибке пользователю
            try:
                if args and hasattr(args[1], 'from_user'):
                    await self.bot.send_message(
                        args[1].from_user.id,
                        "❌ Произошла внутренняя ошибка. Попробуйте позже."
                    )
            except:
                pass  # Игнорируем ошибки при отправке сообщения об ошибке
    
    async def _handle_callback_query(self, call):
        """Обработчик callback-кнопок"""
        try:
            # Валидация входных данных
            if not call or not call.from_user or not call.data:
                logger.warning("Invalid callback query data")
                await self.bot.answer_callback_query(call.id, "❌ Неверные данные запроса")
                return
            
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)

            # Безопасный ответ на callback query
            try:
                await self.bot.answer_callback_query(call.id)
            except Exception as callback_error:
                error_msg = str(callback_error)
                if "query is too old" in error_msg or "response timeout expired" in error_msg:
                    logger.debug(f"Callback query expired (ignored): {error_msg}")
                    await self.bot.send_message(
                        call.message.chat.id,
                        "⏰ Запрос устарел. Пожалуйста, воспользуйтесь актуальными кнопками."
                    )
                    return
                else:
                    logger.warning(f"Callback query answer failed: {error_msg}")

            # Обработка различных типов callback queries
            data = call.data
            
            # 🆕 ФАЗЫ 2-3: Обработчики для контекстуальных кнопок продолжения диалога
            if data == "continue_writing":
                await self._handle_continue_writing(call, user)
            elif data == "add_flirt":
                await self._handle_add_flirt(call, user)
            elif data == "quick_ppv":
                await self._handle_quick_ppv(call, user)
            elif data == "quick_tips":
                await self._handle_quick_tips(call, user)
            # Новые контекстуальные обработчики
            elif data == "get_closer":
                await self._handle_get_closer(call, user)
            elif data == "light_flirt":
                await self._handle_light_flirt(call, user)
            elif data == "show_content":
                await self._handle_show_content(call, user)
            elif data == "casual_chat":
                await self._handle_casual_chat(call, user)
            elif data == "hot_content":
                await self._handle_hot_content(call, user)
            elif data == "exclusive_content":
                await self._handle_exclusive_content(call, user)
            elif data == "tips_for_content":
                await self._handle_tips_for_content(call, user)
            elif data == "teasing_response":
                await self._handle_teasing_response(call, user)
            elif data == "flirty_thanks":
                await self._handle_flirty_thanks(call, user)
            elif data == "escalate_flirt":
                await self._handle_escalate_flirt(call, user)
            elif data == "return_compliment":
                await self._handle_return_compliment(call, user)
            elif data == "reward_compliment":
                await self._handle_reward_compliment(call, user)
            elif data == "continue_conversation":
                await self._handle_continue_conversation(call, user)
            elif data == "suggest_content":
                await self._handle_suggest_content(call, user)
            elif data == "playful_response":
                await self._handle_playful_response(call, user)
            # 🆕 НЕДОСТАЮЩИЕ ОБРАБОТЧИКИ:
            elif data == "tease_more":
                await self._handle_tease_more(call, user)
            elif data == "request_payment":
                await self._handle_request_payment(call, user)
            elif data == "ppv_offer":
                await self._handle_ppv_offer(call, user)
            elif data == "vip_content":
                await self._handle_vip_content(call, user)
            elif data == "more_flirt":
                await self._handle_more_flirt(call, user)
            elif data == "escalate_passion":
                await self._handle_escalate_passion(call, user)
            elif data == "special_content":
                await self._handle_special_content(call, user)
            elif data == "flirt_tips":
                await self._handle_flirt_tips(call, user)
            elif data == "continue_chat":
                await self._handle_continue_chat(call, user)
            elif data == "transition_flirt":
                await self._handle_transition_flirt(call, user)
            elif data == "tell_about_self":
                await self._handle_tell_about_self(call, user)
            elif data == "ask_question":
                await self._handle_ask_question(call, user)
            # Existing handlers
            elif data.startswith("model_"):
                model_key = data.replace("model_", "")
                await self._handle_model_change(call, user, model_key)
            elif data.startswith("flirt_style_"):
                style_id = data.replace("flirt_style_", "")
                await self._handle_flirt_style(call, user, style_id)
            elif data.startswith("ppv_style_"):
                style_name = data.replace("ppv_style_", "")
                await self._handle_ppv_style(call, user, style_name)
            elif data.startswith("survey_"):
                await self._handle_survey_step(call, user)
            elif data.startswith("chat_"):
                # Полная обработка всех chat callbacks через ChatHandlers
                await self._handle_chat_callback(call, data)
            elif data == "back_to_main":
                # Возврат в главное меню
                await self._handle_back_to_main(call)
            else:
                logger.warning(f"Unknown callback data: {data}")
                
        except Exception as e:
            logger.error(f"Error in callback query handler: {str(e)}", exc_info=True)
    
    async def _handle_model_change(self, call, user, model_key):
        """Обработка смены модели AI"""
        if model_key in MODELS:
            user.model = model_key
            self.state_manager.save_user(call.from_user.id, user)
            
            model_info = MODELS[model_key]
            text = f"✅ Модель изменена на: <b>{model_info['description']}</b>\n\n"
            text += f"🔧 Параметры:\n"
            text += f"• Токены: {model_info.get('max_tokens', 'auto')}\n"
            text += f"• Креативность: {model_info.get('temperature', 0.8)}"
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                text,
                parse_mode="HTML",
            )
    
    async def _handle_flirt_style(self, call, user, style_id):
        """Обработка выбора стиля флирта"""
        # Найдем стиль по id
        style_info = None
        style_name = None
        
        for name, info in FLIRT_STYLES.items():
            if info['id'] == style_id:
                style_info = info
                style_name = name
                break
        
        if not style_info:
            logger.error(f"Unknown flirt style id: {style_id}")
            await self.bot.answer_callback_query(call.id, "❌ Неизвестный стиль")
            return
            
        # Генерируем флирт-сообщение
        prompt = f"Создай флирт-сообщение в стиле '{style_name}': {style_info['description']}"
        
        try:
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            
            text = f"{style_info['emoji']} <b>Флирт ({style_name})</b>\n\n"
            text += response
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Error generating flirt message: {e}")
            error_text = "❌ Ошибка при генерации сообщения. Попробуйте позже."
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                error_text,
            )
    
    async def _handle_ppv_style(self, call, user, style_name):
        """Обработка выбора стиля PPV"""
        if style_name not in PPV_STYLES:
            logger.error(f"Unknown PPV style: {style_name}")
            await self.bot.answer_callback_query(call.id, "❌ Неизвестный стиль")
            return
            
        style_description = PPV_STYLES[style_name]
        
        # Генерируем PPV-сообщение
        prompt = f"Создай привлекательное PPV сообщение в стиле '{style_name}': {style_description}. Сделай его коротким, заманчивым и профессиональным."
        
        try:
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            
            text = f"💎 <b>PPV - {style_name.title()}</b>\n\n"
            text += response
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Error generating PPV message: {e}")
            error_text = "❌ Ошибка при генерации сообщения. Попробуйте позже."
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                error_text,
            )
    
    async def _handle_survey_step(self, call, user):
        """Обработка шагов опроса"""
        # Парсинг данных опроса - более точная логика
        if not call.data.startswith("survey_"):
            return
            
        # Убираем префикс "survey_"
        survey_data = call.data[7:]  # len("survey_") = 7
        
        # Разделяем на части, но учитываем что в step могут быть подчеркивания
        parts = survey_data.split('_')
        if len(parts) < 2:
            logger.warning(f"Invalid survey callback format: {call.data}")
            return
        
        # Последняя часть - это value, всё остальное - step
        value = parts[-1]
        step = '_'.join(parts[:-1])
        
        logger.debug(f"Survey callback: step='{step}', value='{value}'")
        
        # Обновляем предпочтения пользователя
        if step == "content_types":
            user.preferences.content_types = [value] if value != "all" else ["photos", "videos", "messages"]
        elif step == "price_range":
            user.preferences.price_range = value
        elif step == "communication_style":
            user.preferences.communication_style = value
        elif step == "notification_frequency":
            user.preferences.notification_frequency = value
        else:
            logger.warning(f"Unknown survey step: {step}")
            return
        
        # Переходим к следующему шагу или завершаем опрос
        next_steps = list(SURVEY_STEPS.keys())
        current_index = next_steps.index(step) if step in next_steps else -1
        
        if current_index + 1 < len(next_steps):
            # Показываем следующий шаг
            next_step = next_steps[current_index + 1]
            await self._show_survey_step(call, next_step)
        else:
            # Завершаем опрос
            user.preferences.completed_survey = True
            self.state_manager.save_user(call.from_user.id, user)
            
            text = "✅ <b>Опрос завершен!</b>\n\n"
            text += "Ваши предпочтения сохранены. Теперь бот будет учитывать их при генерации сообщений."
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                text,
            )
    
    async def _show_survey_step(self, call, step):
        """Показывает шаг опроса"""
        if step not in SURVEY_STEPS:
            return
            
        step_data = SURVEY_STEPS[step]
        keyboard = get_survey_keyboard(step)
        
        try:
            # Проверяем что контент действительно изменился
            current_text = call.message.text if call.message.text else ""
            new_text = step_data['question']
            
            if current_text == new_text:
                # Если текст не изменился, просто отвечаем на callback
                await self.bot.answer_callback_query(call.id, "Переходим к следующему шагу...")
                return
            
            success = await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                step_data['question'],
                reply_markup=keyboard,
                parse_mode=None,
            )
            if not success:
                try:
                    await self.bot.delete_message(
                        call.message.chat.id, call.message.message_id
                    )
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Could not edit message, sending new one: {e}")
            try:
                await self.bot.delete_message(
                    call.message.chat.id, call.message.message_id
                )
            except Exception:
                pass
            await self.bot.send_message(
                call.message.chat.id,
                step_data['question'],
                reply_markup=keyboard,
            )
    
    async def _handle_text_message(self, message):
        """Обработчик текстовых сообщений"""
        try:
            user_id = message.from_user.id
            user = self.state_manager.get_user(user_id)
            text = message.text
            
            # Обработка ожидающих состояний
            if user.waiting_for_chat_name:
                await self.chat_handlers.process_chat_name_input(self.bot, message)
                return
            elif user.waiting_for_chat_reply:
                await self.chat_handlers.process_chat_reply_input(self.bot, message)
                return
            
            # Обработка кнопок главного меню
            if text == "💬 Написать сообщение":
                await self._handle_write_message(message, user)
            elif text == "💝 Флирт":
                await self._handle_flirt_button(message, user)
            elif text == "🎁 Платный контент":
                await self._handle_ppv_button(message, user)
            elif text == "🌟 Чаевые":
                await self._handle_tips_button(message, user)
            elif text == "👥 Чаты с клиентами":
                await self._handle_chat_management_button(message, user)
            elif text == "⚙️ Сменить модель":
                await self._handle_model_button(message, user)
            elif text == "ℹ️ Помощь":
                await self._handle_help_button(message, user)
            else:
                # Генерация ответа через AI
                await self._handle_user_message_generation(message, user, text)
                
        except Exception as e:
            logger.error(f"Error in text message handler: {str(e)}", exc_info=True)
    
    async def _handle_write_message(self, message, user):
        """Обработка кнопки 'Написать сообщение'"""
        text = "✍️ <b>Генерация сообщения</b>\n\n"
        text += "Опишите ситуацию или контекст, и я создам подходящее сообщение:"
        
        await self.bot.send_message(
            message.chat.id, text,
            parse_mode='HTML'
        )
    
    async def _handle_flirt_button(self, message, user):
        """Обработка кнопки 'Флирт'"""
        text = "💝 <b>Выберите стиль флирта:</b>"
        keyboard = get_flirt_style_keyboard()
        
        await self.bot.send_message(
            message.chat.id, text,
            parse_mode='HTML', reply_markup=keyboard
        )
    
    async def _handle_ppv_button(self, message, user):
        """Обработка кнопки 'Платный контент'"""
        text = "🎁 <b>Выберите стиль PPV контента:</b>"
        keyboard = get_ppv_style_keyboard()
        
        await self.bot.send_message(
            message.chat.id, text,
            parse_mode='HTML', reply_markup=keyboard
        )
    
    async def _handle_tips_button(self, message, user):
        """Обработка кнопки 'Чаевые'"""
        text = "🌟 <b>Запрос чаевых</b>\n\n"
        text += "Опишите ситуацию, и я создам деликатный запрос на чаевые:"
        
        await self.bot.send_message(
            message.chat.id, text,
            parse_mode='HTML'
        )
    
    async def _handle_chat_management_button(self, message, user):
        """Обработка кнопки 'Чаты с клиентами'"""
        # Создаем mock callback query для совместимости с ChatHandlers
        mock_call = types.CallbackQuery(
            id="mock",
            from_user=message.from_user,
            data="chat_management",
            chat_instance="mock_instance",
            json_string="{}",
            message=message
        )
        
        await self.chat_handlers.handle_chat_management(self.bot, mock_call, from_button=True)
    
    async def _handle_model_button(self, message, user):
        """Обработка кнопки 'Сменить модель'"""
        current_model = MODELS.get(user.model, {})
        text = f"🤖 <b>Текущая модель:</b> {current_model.get('description', 'Неизвестно')}\n\n"
        text += "Выберите новую модель:"
        
        keyboard = get_model_keyboard()
        
        await self.bot.send_message(
            message.chat.id, text,
            parse_mode='HTML', reply_markup=keyboard
        )
    
    async def _handle_help_button(self, message, user):
        """Обработка кнопки 'Помощь'"""
        text = "ℹ️ <b>Помощь по использованию бота</b>\n\n"
        text += "🔹 <b>💬 Написать сообщение</b> - Генерация обычных сообщений\n"
        text += "🔹 <b>💝 Флирт</b> - Создание флирт-сообщений\n"
        text += "🔹 <b>🎁 Платный контент</b> - Описания для PPV\n"
        text += "🔹 <b>🌟 Чаевые</b> - Деликатные запросы на чаевые\n"
        text += "🔹 <b>👥 Чаты с клиентами</b> - Управление диалогами\n"
        text += "🔹 <b>⚙️ Сменить модель</b> - Выбор AI модели\n\n"
        text += "💡 Просто напишите сообщение, и бот создаст подходящий ответ!"
        
        await self.bot.send_message(
            message.chat.id, text,
            parse_mode='HTML'
        )
    
    async def _handle_user_message_generation(self, message, user, text):
        """
        Генерация ответа на пользовательское сообщение
        🆕 ФАЗА 1: Добавлены кнопки продолжения диалога
        """
        try:
            # Показываем индикатор печатания
            await self.bot.send_chat_action(message.chat.id, 'typing')
            
            # Создаем промпт
            prompt = self._create_safe_prompt(text, user)
            
            # Генерируем ответ
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            
            # Добавляем в историю
            user.add_message_to_history("user", text)
            user.add_message_to_history("assistant", response)
            user.update_activity()
            self.state_manager.save_user(message.from_user.id, user)
            
            # 🆕 ФАЗА 1: Отправляем ответ с кнопками продолжения
            continue_keyboard = get_quick_continue_keyboard(text)
            await self.bot.send_message(
                message.chat.id, response,
                parse_mode='HTML',
                reply_markup=continue_keyboard  # 🆕 КНОПКИ ПРОДОЛЖЕНИЯ!
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            await self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при генерации ответа. Попробуйте позже."
            )
    
    def _create_safe_prompt(self, text: str, user) -> str:
        """Создает живой, человечный промпт для генерации завлекающих ответов на английском с переводом"""
        
        # 🆕 АНГЛИЙСКИЕ ПРОМПТЫ ДЛЯ МЕЖДУНАРОДНЫХ КЛИЕНТОВ
        base_prompt = """You are a real OnlyFans model named Christina. You're chatting with a client in private messages.

🎭 YOUR PERSONALITY:
- Young, attractive and confident
- Playful, flirty, but elegant  
- Genuinely interested in the client
- Know how to entice and intrigue
- Speak naturally like a real girl

💬 COMMUNICATION STYLE:
- Use emojis moderately (1-2 per message)
- Address client warmly: "babe", "honey", "sexy"
- Ask questions, show interest
- Add light flirt and intrigue
- Write in short sentences (1-3 sentences)

🎯 GOALS:
- Engage client in conversation
- Create desire to continue chatting
- Hint at closer connection
- Gradually lead to content purchases

❌ DON'T DO:
- Don't write like robot or assistant
- Don't use overly formal language
- Don't mention "creating messages" or "generation"
- Don't reveal you're AI

📋 IMPORTANT OUTPUT FORMAT:
You MUST provide your response in this EXACT format:

[Your English response here]

---
🔍 Перевод: [Russian translation here for moderator]

The English part should be natural and engaging for international clients.
The Russian translation helps the chat moderator understand the message."""

        # Добавляем контекст истории сообщений если есть
        if hasattr(user, 'message_history') and user.message_history:
            recent_messages = user.message_history[-4:]  # Последние 4 сообщения
            history_context = "\n📚 CONVERSATION HISTORY:\n"
            for msg in recent_messages:
                role = "Client" if msg['role'] == 'user' else "You"
                history_context += f"{role}: {msg['content']}\n"
            base_prompt += f"\n{history_context}"

        # Учитываем предпочтения пользователя для персонализации
        if hasattr(user, 'preferences') and user.preferences.completed_survey:
            style = user.preferences.communication_style
            if style == "кокетливый":
                base_prompt += "\n💝 SPECIAL STYLE: Be more playful and flirty, use more hints and teasing."
            elif style == "дружелюбный": 
                base_prompt += "\n😊 SPECIAL STYLE: Be warm and friendly, create atmosphere of closeness."
            elif style == "загадочный":
                base_prompt += "\n🔮 SPECIAL STYLE: Be intriguing and mysterious, leave things unsaid to create intrigue."

        # Анализируем сообщение клиента для контекстного ответа
        context_hint = ""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['привет', 'hello', 'hi', 'hey', 'здравствуй']):
            context_hint = "\n🎯 CONTEXT: This is a greeting. Respond warmly and with interest, ask a question about the client."
        elif any(word in text_lower for word in ['как дела', 'что делаешь', 'how are you', 'what are you doing']):
            context_hint = "\n🎯 CONTEXT: Client is asking about you. Tell something intriguing about yourself, hint at interesting things."
        elif any(word in text_lower for word in ['фото', 'видео', 'контент', 'показать', 'photo', 'pic', 'video', 'content', 'show']):
            context_hint = "\n🎯 CONTEXT: Client is interested in content. Intrigue them, but don't give everything immediately, lead to PPV."
        elif any(word in text_lower for word in ['красивая', 'сексуальная', 'горячая', 'beautiful', 'sexy', 'hot', 'gorgeous']):
            context_hint = "\n🎯 CONTEXT: Compliment received. Thank flirtily, return compliment, increase flirt level."
        
        final_prompt = f"""{base_prompt}{context_hint}

💌 CLIENT'S MESSAGE: "{text}"

🎭 Respond as real Christina, naturally and enticingly in English with Russian translation:"""

        return final_prompt
    
    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов для graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _edit_or_send(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        *,
        reply_markup=None,
        parse_mode: str = "HTML",
    ) -> bool:
        """Пытается отредактировать сообщение, при неудаче отправляет новое.

        Возвращает ``True`` если редактирование прошло успешно, иначе ``False``.
        """
        try:
            await self.bot.edit_message_text(
                text,
                chat_id,
                message_id,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
            return True
        except Exception as e:
            logger.warning(f"Could not edit message: {e}")
            await self.bot.send_message(
                chat_id,
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
            return False
    
    async def run(self):
        """Запуск бота"""
        try:
            self.is_running = True
            logger.info("🚀 Starting OF Assistant Bot...")
            
            # Запускаем бота с минимальными параметрами для версии 4.15.0
            await self.bot.infinity_polling()
            
        except Exception as e:
            logger.error(f"Error during bot execution: {str(e)}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы бота"""
        try:
            logger.info("🛑 Shutting down OF Assistant Bot...")
            self.is_running = False
            
            if self.state_manager:
                self.state_manager.save_data()
            
            if self.bot:
                await self.bot.close_session()
                
            self._shutdown_event.set()
            logger.info("✅ Shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}", exc_info=True)

    async def _handle_chat_callback(self, call, data):
        """Обработка всех chat_ callback queries"""
        try:
            # Проверяем простые callbacks
            simple_handlers = {
                "chat_management": lambda: self.chat_handlers.handle_chat_management(self.bot, call),
                "chat_list": lambda: self.chat_handlers.handle_chat_list(self.bot, call, 0),
                "chat_new": lambda: self.chat_handlers.handle_new_chat(self.bot, call),
                "chat_reply": lambda: self.chat_handlers.handle_chat_reply(self.bot, call),
                "chat_memory": lambda: self.chat_handlers.handle_chat_memory(self.bot, call),
                "chat_analytics": lambda: self.chat_handlers.handle_chat_analytics(self.bot, call),
            }
            
            if data in simple_handlers:
                await simple_handlers[data]()
                return
            
            # Обрабатываем параметризованные callbacks
            if data.startswith("chat_switch_"):
                chat_id = data.replace("chat_switch_", "")
                await self.chat_handlers.handle_switch_chat(self.bot, call, chat_id)
                return
            
            if data.startswith("chat_list_page_"):
                try:
                    page = int(data.replace("chat_list_page_", ""))
                    await self.chat_handlers.handle_chat_list(self.bot, call, page)
                except ValueError:
                    logger.warning(f"Invalid page number in callback: {data}")
                    await self.bot.answer_callback_query(call.id, "❌ Неверный номер страницы")
                return
            
            # Обрабатываем дополнительные chat callbacks
            if data == "chat_flirt":
                await self.chat_handlers.handle_chat_flirt(self.bot, call)
                return
            elif data == "chat_ppv":
                await self.chat_handlers.handle_chat_ppv(self.bot, call)
                return
            elif data == "chat_tips":
                await self.chat_handlers.handle_chat_tips(self.bot, call)
                return
            elif data == "chat_note":
                await self.chat_handlers.handle_chat_note(self.bot, call)
                return
            elif data == "chat_tags":
                await self.chat_handlers.handle_chat_tags(self.bot, call)
                return
            
            # Если callback не распознан
            logger.warning(f"Unknown chat callback: {data}")
            await self.bot.answer_callback_query(call.id, "❌ Неизвестная команда")
            
        except Exception as e:
            logger.error(f"Error in chat callback handler: {str(e)}", exc_info=True)
            try:
                await self.bot.answer_callback_query(call.id, "❌ Ошибка обработки команды")
            except:
                pass

    async def _handle_back_to_main(self, call):
        """Обработка callback back_to_main"""
        try:
            text = "🏠 <b>Главное меню</b>\n\nВыберите действие:"
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                text,
                reply_markup=get_main_keyboard(),
            )
        except Exception as e:
            logger.error(f"Error in back_to_main handler: {str(e)}", exc_info=True)

    async def _handle_main_menu(self, call):
        """Обработка возврата в главное меню"""
        await self._handle_back_to_main(call)

    # 🆕 ФАЗЫ 2-3: Обработчики для контекстуальных кнопок продолжения диалога
    async def _handle_continue_writing(self, call, user):
        """Обработка кнопки 'Еще сообщение'"""
        try:
            text = "✍️ <b>Продолжение беседы</b>\n\n"
            text += "Напишите, что хотите добавить к разговору, и я создам подходящее продолжение:"
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                text,
            )
        except Exception as e:
            logger.error(f"Error in continue writing handler: {str(e)}", exc_info=True)

    async def _handle_add_flirt(self, call, user):
        """Обработка кнопки 'Добавить флирт'"""
        try:
            text = "💝 <b>Добавляем флирт</b>\n\nВыберите стиль флирта:"
            keyboard = get_flirt_style_keyboard()
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                text,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Error in add flirt handler: {str(e)}", exc_info=True)

    async def _handle_quick_ppv(self, call, user):
        """Обработка кнопки 'Быстрый PPV'"""
        try:
            text = "🎁 <b>Быстрый PPV</b>\n\nВыберите стиль контента:"
            keyboard = get_ppv_style_keyboard()
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                text,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Error in quick PPV handler: {str(e)}", exc_info=True)

    async def _handle_quick_tips(self, call, user):
        """Обработка кнопки 'Чаевые'"""
        try:
            # Показываем индикатор печатания
            await self.bot.send_chat_action(call.message.chat.id, 'typing')
            
            # Создаем промпт для запроса чаевых на английском
            prompt = """Create a delicate and sweet tip request for OnlyFans in English with Russian translation. Make it short, grateful and not pushy.

Format: [English response]
---
🔍 Перевод: [Russian translation]

The message should feel natural and appreciative, encouraging tips without being demanding."""
            
            # Генерируем ответ
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            
            # Добавляем кнопки продолжения
            continue_keyboard = get_quick_continue_keyboard("tips")
            
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                response,
                reply_markup=continue_keyboard,
            )
                
        except Exception as e:
            logger.error(f"Error in quick tips handler: {str(e)}", exc_info=True)
            error_text = "❌ Ошибка при генерации запроса чаевых. Попробуйте позже."
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                error_text,
            )

    # Новые контекстуальные обработчики
    async def _handle_get_closer(self, call, user):
        """Обработка кнопки 'Познакомиться ближе'"""
        try:
            await self.bot.send_chat_action(call.message.chat.id, 'typing')
            
            prompt = """Client wants to get closer. Create an intriguing response from Christina in English with Russian translation:
            - Show genuine interest
            - Ask a personal question about the client  
            - Share something about yourself
            - Hint at possibility of closer connection
            
            Format: [English response]
            ---
            🔍 Перевод: [Russian translation]"""
            
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            keyboard = get_smart_continuation_keyboard("casual_chat")
            
            await self._send_contextual_response(call, response, keyboard, user, "get_closer")
        except Exception as e:
            logger.error(f"Error in get_closer handler: {str(e)}", exc_info=True)

    async def _handle_light_flirt(self, call, user):
        """Обработка кнопки 'Легкий флирт'"""
        try:
            await self.bot.send_chat_action(call.message.chat.id, 'typing')
            
            prompt = """Client chose light flirt. Create a flirty response from Christina in English with Russian translation:
            - Be playful and flirty
            - Use light hints and teasing
            - Compliment the client
            - Create intrigue for continuation
            
            Format: [English response]
            ---
            🔍 Перевод: [Russian translation]"""
            
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            keyboard = get_smart_continuation_keyboard("flirt_mode")
            
            await self._send_contextual_response(call, response, keyboard, user, "light_flirt")
        except Exception as e:
            logger.error(f"Error in light_flirt handler: {str(e)}", exc_info=True)

    async def _handle_show_content(self, call, user):
        """Обработка кнопки 'Показать контент'"""
        try:
            await self.bot.send_chat_action(call.message.chat.id, 'typing')
            
            prompt = """Client is interested in content. Create a seductive response from Christina in English with Russian translation:
            - Tease with description of your content
            - Don't give everything immediately
            - Hint at exclusivity
            - Lead towards payment/PPV
            
            Format: [English response]
            ---
            🔍 Перевод: [Russian translation]"""
            
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            keyboard = get_smart_continuation_keyboard("content_interest")
            
            await self._send_contextual_response(call, response, keyboard, user, "show_content")
        except Exception as e:
            logger.error(f"Error in show_content handler: {str(e)}", exc_info=True)

    async def _handle_casual_chat(self, call, user):
        """Обработка кнопки 'Просто пообщаться'"""
        try:
            await self.bot.send_chat_action(call.message.chat.id, 'typing')
            
            prompt = """Client wants to just chat. Create a friendly response from Christina in English with Russian translation:
            - Be open and friendly
            - Ask an interesting question
            - Show you're interested in the person
            - Create warm atmosphere
            
            Format: [English response]
            ---
            🔍 Перевод: [Russian translation]"""
            
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            keyboard = get_smart_continuation_keyboard("casual_chat")
            
            await self._send_contextual_response(call, response, keyboard, user, "casual_chat")
        except Exception as e:
            logger.error(f"Error in casual_chat handler: {str(e)}", exc_info=True)

    async def _handle_continue_conversation(self, call, user):
        """Обработка кнопки 'Продолжить беседу'"""
        try:
            await self.bot.send_chat_action(call.message.chat.id, 'typing')
            
            # Анализируем историю для контекстного продолжения
            history_context = ""
            if hasattr(user, 'message_history') and user.message_history:
                recent_msg = user.message_history[-1] if user.message_history else None
                if recent_msg:
                    history_context = f"Last message was: {recent_msg.get('content', '')}"
            
            prompt = f"""Continue natural conversation as Christina in English with Russian translation. {history_context}
            Create logical continuation of the conversation:
            - Develop previous topic
            - Add something new and interesting
            - Maintain client engagement
            - Show genuine interest
            
            Format: [English response]
            ---
            🔍 Перевод: [Russian translation]"""
            
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            keyboard = get_quick_continue_keyboard("conversation continuation")
            
            await self._send_contextual_response(call, response, keyboard, user, "continue_conversation")
        except Exception as e:
            logger.error(f"Error in continue_conversation handler: {str(e)}", exc_info=True)

    async def _handle_flirty_thanks(self, call, user):
        """Обработка кнопки 'Поблагодарить кокетливо'"""
        try:
            await self.bot.send_chat_action(call.message.chat.id, 'typing')
            
            prompt = """Client gave a compliment. Create a flirty thank you from Christina in English with Russian translation:
            - Thank playfully and sweetly
            - Show the compliment touched you
            - Hint at reciprocity
            - Create desire for more compliments
            
            Format: [English response]
            ---
            🔍 Перевод: [Russian translation]"""
            
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            keyboard = get_smart_continuation_keyboard("flirt_mode")
            
            await self._send_contextual_response(call, response, keyboard, user, "flirty_thanks")
        except Exception as e:
            logger.error(f"Error in flirty_thanks handler: {str(e)}", exc_info=True)

    async def _send_contextual_response(self, call, response: str, keyboard, user, action_type: str):
        """Универсальная функция отправки контекстуального ответа"""
        try:
            # Добавляем в историю
            user.add_message_to_history("assistant", response)
            user.add_message_to_history("action", f"User used: {action_type}")
            user.update_activity()
            self.state_manager.save_user(call.from_user.id, user)
            
            # Отправляем ответ
            await self._edit_or_send(
                call.message.chat.id,
                call.message.message_id,
                response,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Error sending contextual response: {str(e)}")

    # Заглушки для остальных обработчиков (будут реализованы по требованию)
    async def _handle_hot_content(self, call, user):
        await self._handle_show_content(call, user)  # Используем базовую логику контента

    async def _handle_exclusive_content(self, call, user):
        await self._handle_show_content(call, user)  # Используем базовую логику контента

    async def _handle_tips_for_content(self, call, user):
        await self._handle_quick_tips(call, user)  # Используем базовую логику чаевых

    async def _handle_teasing_response(self, call, user):
        await self._handle_light_flirt(call, user)  # Используем базовую логику флирта

    async def _handle_escalate_flirt(self, call, user):
        await self._handle_light_flirt(call, user)  # Используем базовую логику флирта

    async def _handle_return_compliment(self, call, user):
        await self._handle_flirty_thanks(call, user)  # Используем базовую логику благодарности

    async def _handle_reward_compliment(self, call, user):
        await self._handle_show_content(call, user)  # Используем базовую логику контента

    async def _handle_suggest_content(self, call, user):
        await self._handle_show_content(call, user)  # Используем базовую логику контента

    async def _handle_playful_response(self, call, user):
        await self._handle_light_flirt(call, user)  # Используем базовую логику флирта

    async def _handle_tease_more(self, call, user):
        await self._handle_light_flirt(call, user)  # Используем базовую логику флирта

    async def _handle_request_payment(self, call, user):
        await self._handle_show_content(call, user)  # Используем базовую логику контента

    async def _handle_ppv_offer(self, call, user):
        await self._handle_show_content(call, user)  # Используем базовую логику контента

    async def _handle_vip_content(self, call, user):
        await self._handle_show_content(call, user)  # Используем базовую логику контента

    async def _handle_more_flirt(self, call, user):
        await self._handle_light_flirt(call, user)  # Используем базовую логику флирта

    async def _handle_escalate_passion(self, call, user):
        await self._handle_light_flirt(call, user)  # Используем базовую логику флирта

    async def _handle_special_content(self, call, user):
        await self._handle_show_content(call, user)  # Используем базовую логику контента

    async def _handle_flirt_tips(self, call, user):
        await self._handle_quick_tips(call, user)  # Используем базовую логику чаевых

    async def _handle_continue_chat(self, call, user):
        await self._handle_continue_conversation(call, user)  # Используем базовую логику продолжения диалога

    async def _handle_transition_flirt(self, call, user):
        await self._handle_light_flirt(call, user)  # Используем базовую логику флирта

    async def _handle_tell_about_self(self, call, user):
        await self._handle_get_closer(call, user)  # Используем базовую логику знакомства

    async def _handle_ask_question(self, call, user):
        await self._handle_get_closer(call, user)  # Используем базовую логику знакомства


async def main():
    """Главная функция запуска бота с поддержкой enhanced features"""
    bot_manager = BotManager()
    
    # Инициализируем базовый бот
    if not await bot_manager.initialize():
        logger.error("❌ Failed to initialize base bot. Exiting...")
        sys.exit(1)
    
    # Пытаемся инициализировать enhanced features
    try:
        from bot_integration import integrate_enhanced_features
        
        logger.info("🚀 Initializing enhanced OF bot features...")
        integrated_manager = await integrate_enhanced_features(bot_manager)
        
        if integrated_manager:
            logger.info("✅ Enhanced features initialized successfully")
            logger.info("🔥 Professional OF Bot v2.0 with Adult Content System - Ready!")
            
            # Запускаем интегрированный бот
            await integrated_manager.original_manager.run()
        else:
            logger.warning("⚠️ Enhanced features failed to initialize, running basic bot")
            await bot_manager.run()
            
    except ImportError as e:
        logger.warning(f"⚠️ Enhanced features not available: {str(e)}")
        logger.info("Running basic bot without enhanced features")
        await bot_manager.run()
        
    except Exception as e:
        logger.error(f"❌ Error initializing enhanced features: {str(e)}", exc_info=True)
        logger.info("Falling back to basic bot")
        await bot_manager.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}", exc_info=True)
        sys.exit(1) 