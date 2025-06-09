"""
Модуль обработчиков команд бота.
Содержит все обработчики команд и сообщений Telegram бота.
"""

import logging
from datetime import datetime, timedelta
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from models import PPVReminder
from utils import (
    get_main_keyboard, get_model_keyboard, get_flirt_style_keyboard,
    get_relationship_stage_keyboard, get_survey_keyboard, parse_time_string,
    get_ppv_style_keyboard
)
from api import generate_groq_response
from config.config import (
    MODELS, FLIRT_STYLES, RELATIONSHIP_STAGES, SURVEY_STEPS, PPV_STYLES
)
from security import (
    admin_required, rate_limit_check, validate_user_input, secure_format_prompt,
    rate_limiter, ai_rate_limiter, log_security_event, security_stats
)

logger = logging.getLogger("bot_logger")

# Глобальная переменная для менеджера состояний
state_manager = None

def set_state_manager(sm):
    """Устанавливает глобальный менеджер состояний"""
    global state_manager
    state_manager = sm

# === БЕЗОПАСНЫЕ ФУНКЦИИ ОТПРАВКИ ===

async def safe_send_message(bot: AsyncTeleBot, chat_id: int, text: str, **kwargs):
    """Безопасная отправка сообщения с fallback для parse_mode"""
    try:
        return await bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        if "can't parse entities" in str(e) or "bad request" in str(e).lower():
            # Убираем parse_mode и пытаемся снова
            kwargs.pop('parse_mode', None)
            logger.warning(f"HTML parsing failed, retrying without parse_mode for chat {chat_id}")
            return await bot.send_message(chat_id, text, **kwargs)
        else:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            raise e

async def safe_reply_to(bot: AsyncTeleBot, message: types.Message, text: str, **kwargs):
    """Безопасный ответ на сообщение с fallback для parse_mode"""
    try:
        return await bot.reply_to(message, text, **kwargs)
    except Exception as e:
        if "can't parse entities" in str(e) or "bad request" in str(e).lower():
            # Убираем parse_mode и пытаемся снова
            kwargs.pop('parse_mode', None)
            logger.warning(f"HTML parsing failed, retrying without parse_mode for user {message.from_user.id}")
            return await bot.reply_to(message, text, **kwargs)
        else:
            logger.error(f"Failed to reply to message from {message.from_user.id}: {e}")
            raise e

async def safe_edit_message_text(bot: AsyncTeleBot, text: str, chat_id: int, message_id: int, **kwargs):
    """Безопасное редактирование сообщения с fallback для parse_mode"""
    try:
        return await bot.edit_message_text(text, chat_id, message_id, **kwargs)
    except Exception as e:
        if "can't parse entities" in str(e) or "bad request" in str(e).lower():
            # Убираем parse_mode и пытаемся снова
            kwargs.pop('parse_mode', None)
            logger.warning(f"HTML parsing failed, retrying edit without parse_mode for chat {chat_id}")
            return await bot.edit_message_text(text, chat_id, message_id, **kwargs)
        else:
            logger.error(f"Failed to edit message in {chat_id}: {e}")
            raise e

async def send_welcome_message(bot: AsyncTeleBot, chat_id: int, user_state):
    """Отправляет персонализированное приветственное сообщение"""
    try:
        # Формируем данные о предпочтениях
        preferences = ""
        if user_state.preferences.completed_survey:
            prefs = []
            if user_state.preferences.content_types:
                prefs.append(f"Content: {', '.join(user_state.preferences.content_types)}")
            if user_state.preferences.price_range:
                prefs.append(f"Price range: {user_state.preferences.price_range}")
            if user_state.preferences.communication_style:
                prefs.append(f"Style: {user_state.preferences.communication_style}")
            preferences = "\n".join(prefs)
        
        # Загружаем промпт приветствия
        prompt_template = await state_manager.load_prompt('welcome')
        if not prompt_template:
            # Используем стандартное приветствие если промпт не найден
            welcome_text = """🤖 *OnlyFans Assistant Bot* - Ваш умный помощник!

*🎯 Что я умею:*
• 💬 *Общение с подписчиками* - генерация персонализированных ответов
• 💰 *PPV контент* - создание продающих описаний (/ppv)
• 💕 *Флирт* - разные стили общения (/flirt)
• 📊 *Аналитика* - отслеживание активности
• ⏰ *Напоминания* - уведомления о контенте
• 🎨 *Модели ИИ* - выбор стиля генерации (/model)

*🚀 Быстрый старт:*
1. Пройдите короткий опрос (настройка под вас)
2. Используйте команды или кнопки меню
3. Получайте качественные ответы для подписчиков

*⚡ Готов работать 24/7 с защитой от спама!*"""
        else:
            # Генерируем персонализированное приветствие
            history_text = "\n".join([
                f"{m['role']}: {m['content']}"
                for m in user_state.history[-3:]
            ])
            
            prompt = secure_format_prompt(
                prompt_template,
                preferences=preferences,
                history=history_text
            )
            
            welcome_text = await generate_groq_response(
                prompt,
                MODELS[user_state.model]['id']
            )
        
        # Отправляем приветствие
        await safe_send_message(
            bot,
            chat_id,
            welcome_text,
            parse_mode='Markdown'
        )
        
        # Если опрос еще не пройден, начинаем его
        if not user_state.preferences.completed_survey:
            await start_survey(bot, chat_id)
        else:
            # Если опрос пройден, отправляем инструкции
            await send_navigation_instructions(bot, chat_id, user_state)
            
    except Exception as e:
        logger.error(f"Error sending welcome message: {str(e)}", exc_info=True)

async def start_survey(bot: AsyncTeleBot, chat_id: int):
    """Начинает опрос пользователя"""
    try:
        user = state_manager.get_user(chat_id)
        user.current_survey_step = 'content_types'
        
        await safe_send_message(
            bot,
            chat_id,
            "📋 Давайте проведем короткий опрос, чтобы настроить бота под ваши предпочтения!",
            reply_markup=get_survey_keyboard('content_types')
        )
    except Exception as e:
        logger.error(f"Error starting survey: {str(e)}", exc_info=True)

async def send_navigation_instructions(bot: AsyncTeleBot, chat_id: int, user_state):
    """Отправляет инструкции по навигации"""
    try:
        # Загружаем промпт инструкций
        prompt_template = await state_manager.load_prompt('instructions')
        if not prompt_template:
            # Используем стандартные инструкции если промпт не найден
            instructions = """📱 *Как пользоваться ботом:*

*💰 Создание PPV:*
• /ppv 30 - обычное описание за $30
• /ppv 50 провокационный - провокационный стиль

*💕 Флирт-сообщения:*
• /flirt - выбор стиля из меню
• /flirt романтичный - романтичный стиль

*⚙️ Настройки:*
• /model - выбор ИИ модели (умная/креативная)
• /survey - изменить предпочтения

*⏰ Напоминания:*
• /reminder 19:00 Новое фото готово! - создать напоминание

*📊 Меню бота:*
Используйте кнопки внизу экрана для быстрого доступа ко всем функциям.

*💡 Совет:* Всё работает на основе ваших предпочтений из опроса!"""
        else:
            # Генерируем персонализированные инструкции
            preferences = ""
            if user_state.preferences.completed_survey:
                prefs = []
                if user_state.preferences.content_types:
                    prefs.append(f"Content: {', '.join(user_state.preferences.content_types)}")
                if user_state.preferences.price_range:
                    prefs.append(f"Price range: {user_state.preferences.price_range}")
                preferences = "\n".join(prefs)
            
            # Формируем историю сообщений
            history = "\n".join([
                f"{m['role']}: {m['content']}"
                for m in user_state.history[-3:]
            ]) if user_state.history else "Нет истории сообщений"
            
            prompt = secure_format_prompt(
                prompt_template,
                preferences=preferences,
                history=history
            )
            instructions = await generate_groq_response(
                prompt,
                MODELS[user_state.model]['id']
            )
        
        await safe_send_message(
            bot,
            chat_id,
            instructions,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending instructions: {str(e)}", exc_info=True)

# === КРИТИЧЕСКИ ВАЖНЫЕ КОМАНДЫ С АВТОРИЗАЦИЕЙ ===

@rate_limit_check(rate_limiter)
async def handle_start_command(bot: AsyncTeleBot, message: types.Message):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        user = state_manager.get_user(user_id)
        
        # Отправляем персонализированное приветствие
        await send_welcome_message(bot, user_id, user)
        
        # Сохраняем данные
        await state_manager.save_data()
        
        log_security_event("USER_START", user_id, f"Username: @{message.from_user.username}")
        
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        await safe_reply_to(bot, message, "❌ Произошла ошибка. Попробуйте позже.")

@admin_required
async def handle_model_command(bot: AsyncTeleBot, message: types.Message):
    """Обработчик команды /model"""
    try:
        user_id = message.from_user.id
        
        await safe_reply_to(
            bot, message,
            "🧠 Выберите модель ИИ для генерации ответов:",
            reply_markup=get_model_keyboard()
        )
        
        log_security_event("ADMIN_MODEL_ACCESS", user_id)
        security_stats.increment_admin_access()
        
    except Exception as e:
        logger.error(f"Error in model command: {str(e)}", exc_info=True)
        await safe_reply_to(bot, message, "❌ Ошибка доступа к настройкам модели.")

@rate_limit_check(ai_rate_limiter)  # Строже rate limiting для AI запросов
async def handle_flirt_command(bot: AsyncTeleBot, message: types.Message):
    """Обработчик команды /flirt"""
    try:
        user_id = message.from_user.id
        user = state_manager.get_user(user_id)
        
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Валидация пользовательского ввода
        try:
            command_parts = message.text.split()[1:]  # Убираем "/flirt"
            user_input = " ".join(command_parts) if command_parts else ""
            
            if user_input:
                # Валидируем ввод на предмет опасного контента
                validated_input = validate_user_input(user_input, max_length=500)
                if validated_input != user_input:
                    security_stats.increment_sanitized()
                    log_security_event("INPUT_SANITIZED", user_id, f"Original length: {len(user_input)}")
            else:
                validated_input = ""
        except ValueError as e:
            await safe_reply_to(bot, message, f"❌ Некорректный ввод: {e}")
            return
        
        # Остальная логика команды флирта остается прежней, но с валидированным вводом
        if not validated_input:
            # Если не указан стиль, показываем клавиатуру
            await safe_reply_to(
                bot, message,
                "💕 Выберите стиль флирта:",
                reply_markup=get_flirt_style_keyboard()
            )
        else:
            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Используем secure_format_prompt
            # Загружаем промпт
            prompt_template = await state_manager.load_prompt('flirt')
            if not prompt_template:
                prompt_template = """Создай флиртовое сообщение в стиле "{style}". 
Учти предпочтения: {preferences}
История: {history}
Сообщение должно быть привлекательным и персонализированным."""
            
            # Формируем данные безопасно
            preferences = f"Стиль: {user.preferences.communication_style}" if user.preferences.communication_style else "Не указан"
            history = "Нет истории" if not user.history else f"Последнее: {user.history[-1]['content'][:100]}"
            
            # Безопасное форматирование с защитой от injection
            prompt = secure_format_prompt(
                prompt_template,
                style=validated_input,
                preferences=preferences,
                history=history
            )
            
            # Генерируем ответ
            response = await generate_groq_response(prompt, MODELS[user.model]['id'])
            
            # Сохраняем в историю
            state_manager.add_to_history(user_id, "user", f"flirt: {validated_input}")
            state_manager.add_to_history(user_id, "assistant", response)
            
            await safe_reply_to(bot, message, response)
            
            # Сохраняем данные
            await state_manager.save_data()
            
        log_security_event("FLIRT_COMMAND", user_id, f"Style: {validated_input}")
        
    except Exception as e:
        logger.error(f"Error in flirt command: {str(e)}", exc_info=True)
        await safe_reply_to(bot, message, "❌ Ошибка генерации флирта. Попробуйте позже.")

async def handle_ppv_command(bot: AsyncTeleBot, message: types.Message):
    """Обработчик команды /ppv"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await safe_reply_to(
                bot,
                message,
                "📝 Использование: /ppv <цена> [стиль]\n"
                "Например: /ppv 30 провокационный\n\n"
                "Доступные стили:\n" +
                "\n".join(f"• {desc}" for desc in PPV_STYLES.values())
            )
            return
        
        price = parts[1]
        style = parts[2].lower() if len(parts) > 2 else None
        
        if style and style not in PPV_STYLES:
            await safe_reply_to(bot, message, "❌ Неизвестный стиль. Выберите стиль:", 
                             reply_markup=get_ppv_style_keyboard())
            return
        
        user_id = message.from_user.id
        user = state_manager.get_user(user_id)
        
        # Формируем историю сообщений
        history_text = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in user.history[-5:]
        ])
        
        # Загружаем соответствующий промпт
        prompt_template = await state_manager.load_prompt(f'ppv_{style}' if style else 'ppv')
        if not prompt_template:
            await safe_reply_to(bot, message, "❌ Ошибка загрузки промпта")
            return
        
        prompt = prompt_template.format(
            price=price,
            history=history_text
        )
        
        # Отправляем сообщение о генерации
        wait_msg = await safe_reply_to(bot, message, "🤔 Генерирую описание PPV...")
        
        try:
            response = await generate_groq_response(
                prompt,
                MODELS[user.model]['id']
            )
            
            state_manager.add_to_history(user_id, 'assistant', response)
            await state_manager.save_data()
            
            # Удаляем сообщение о генерации и отправляем результат
            await bot.delete_message(wait_msg.chat.id, wait_msg.message_id)
            await safe_reply_to(bot, message, response)
            
        except Exception as e:
            error_msg = (f"❌ Ошибка генерации:\n{str(e)}\n\n"
                        f"Попробуйте другую модель через ⚙️ Сменить модель")
            
            # Удаляем сообщение о генерации
            await bot.delete_message(wait_msg.chat.id, wait_msg.message_id)
            await safe_reply_to(bot, message, error_msg)
            
    except Exception as e:
        logger.error(f"Error in PPV handler: {str(e)}", exc_info=True)
        await safe_reply_to(bot, message, "❌ Произошла ошибка при создании PPV")

async def handle_set_ppv_reminder_command(bot: AsyncTeleBot, message: types.Message):
    """Обработчик команды /set_ppv_reminder"""
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await safe_reply_to(
                bot,
                message,
                "📝 Использование: /set_ppv_reminder <время> <сообщение>\n"
                "Время в формате: 30m, 2h, 1d (минуты, часы, дни)\n"
                "Например: /set_ppv_reminder 2h 🔥 Не пропустите горячий контент!"
            )
            return
        
        time_str = parts[1].lower()
        reminder_message = parts[2]
        
        # Парсим время
        try:
            minutes = parse_time_string(time_str)
            send_time = datetime.now() + timedelta(minutes=minutes)
            
        except ValueError:
            await safe_reply_to(
                bot,
                message,
                "❌ Неверный формат времени. Используйте: 30m, 2h, 1d"
            )
            return
        
        user_id = message.from_user.id
        user = state_manager.get_user(user_id)
        
        # Создаем напоминание
        reminder = PPVReminder(
            user_id=user_id,
            message=reminder_message,
            scheduled_time=send_time
        )
        
        # Добавляем напоминание
        user.ppv_reminders.append(reminder)
        # TODO: Реализовать scheduler для отправки напоминаний
        await state_manager.save_data()
        
        await safe_reply_to(
            bot,
            message,
            f"✅ Напоминание установлено на: {send_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Сообщение: {reminder_message}"
        )
        
    except Exception as e:
        logger.error(f"Error in set ppv reminder handler: {str(e)}", exc_info=True)
        await safe_reply_to(bot, message, "❌ Произошла ошибка при установке напоминания") 