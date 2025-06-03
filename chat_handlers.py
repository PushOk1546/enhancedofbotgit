"""
Обработчики для управления множественными чатами с клиентами.
Включает создание, переключение, удаление чатов и работу с контекстом.
"""

import logging
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from chat_models import ChatManager, ClientProfile, ClientChat, ChatMessage
from chat_utils import (
    get_chat_management_keyboard, get_chat_list_keyboard, get_chat_context_keyboard,
    format_chat_info, format_chat_memory, format_chat_analytics, create_chat_context_prompt
)
from api import generate_groq_response
from config import MODELS
from datetime import datetime

logger = logging.getLogger("bot_logger")

async def safe_send_message(bot: AsyncTeleBot, chat_id: int, text: str, **kwargs):
    """Безопасная отправка сообщения с fallback для parse_mode"""
    try:
        return await bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        if "can't parse entities" in str(e):
            # Убираем parse_mode и пытаемся снова
            kwargs.pop('parse_mode', None)
            return await bot.send_message(chat_id, text, **kwargs)
        else:
            raise e

async def safe_edit_message_text(bot: AsyncTeleBot, text: str, chat_id: int, message_id: int, **kwargs):
    """Безопасное редактирование сообщения с fallback для parse_mode"""
    try:
        return await bot.edit_message_text(text, chat_id, message_id, **kwargs)
    except Exception as e:
        if "can't parse entities" in str(e):
            # Убираем parse_mode и пытаемся снова
            kwargs.pop('parse_mode', None)
            return await bot.edit_message_text(text, chat_id, message_id, **kwargs)
        else:
            raise e

class ChatHandlers:
    """Класс для обработки команд управления чатами"""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
    
    async def handle_chat_management(self, bot: AsyncTeleBot, call: types.CallbackQuery, from_button: bool = False):
        """Отображение главного меню управления чатами"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            # Инициализируем chat_manager если его нет
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                user.chat_manager = ChatManager(user_id)
            
            active_chat = user.chat_manager.get_active_chat()
            total_chats = len(user.chat_manager.chats)
            
            text = f"💬 **Управление чатами с клиентами**\n\n"
            text += f"📊 Всего чатов: {total_chats}\n"
            
            if active_chat:
                text += f"🟢 Активный чат: **{active_chat.client_profile.name}**\n"
                text += f"💌 Сообщений: {len(active_chat.messages)}\n"
                text += f"🎭 Этап: {active_chat.conversation_stage}\n"
            else:
                text += "⚪ Нет активного чата\n"
            
            text += "\nВыберите действие:"
            
            # Если это вызов из кнопки (не callback), отправляем новое сообщение
            if from_button:
                await safe_send_message(bot, call.message.chat.id, text, reply_markup=get_chat_management_keyboard())
            else:
                # Обычный callback query - пытаемся редактировать сообщение
                try:
                    await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=get_chat_management_keyboard())
                except Exception as edit_error:
                    # Если не удается редактировать, отправляем новое сообщение
                    logger.warning(f"Cannot edit message, sending new: {str(edit_error)}")
                    await safe_send_message(bot, call.message.chat.id, text, reply_markup=get_chat_management_keyboard())
            
            # Отвечаем на callback query только если это реальный callback и не from_button
            if not from_button:
                try:
                    await bot.answer_callback_query(call.id)
                except Exception as callback_error:
                    # Игнорируем ошибки callback query (expired, timeout, etc.)
                    logger.debug(f"Callback query error (ignored): {str(callback_error)}")
            
        except Exception as e:
            logger.error(f"Error in chat management: {str(e)}", exc_info=True)
            
            # Пытаемся отправить сообщение об ошибке
            try:
                if from_button:
                    await safe_send_message(bot, call.message.chat.id, "❌ Ошибка управления чатами. Попробуйте еще раз.")
                else:
                    # Для callback query пытаемся ответить, но не критично если не получится
                    try:
                        await bot.answer_callback_query(call.id, "❌ Ошибка управления чатами")
                    except Exception:
                        # Если callback query expired/invalid, отправляем обычное сообщение
                        await safe_send_message(bot, call.message.chat.id, "❌ Ошибка управления чатами. Попробуйте еще раз.")
            except Exception as final_error:
                logger.error(f"Cannot send error message: {str(final_error)}")
    
    async def handle_chat_list(self, bot: AsyncTeleBot, call: types.CallbackQuery, page: int = 0):
        """Отображение списка чатов"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                user.chat_manager = ChatManager(user_id)
            
            chat_list = user.chat_manager.get_chat_list()
            
            if not chat_list:
                text = "💬 **Список чатов**\n\nУ вас пока нет чатов с клиентами.\nСоздайте первый чат кнопкой ➕ Новый чат"
                keyboard = get_chat_list_keyboard(user.chat_manager, page)
            else:
                text = f"💬 **Список чатов** (стр. {page + 1})\n\n"
                
                # Показываем чаты на текущей странице
                items_per_page = 5
                start_idx = page * items_per_page
                end_idx = min(start_idx + items_per_page, len(chat_list))
                
                for i, chat_info in enumerate(chat_list[start_idx:end_idx], start_idx + 1):
                    status = "🟢" if chat_info['is_active'] else "⚪"
                    stage_emoji = "🌱" if chat_info['conversation_stage'] == "initial" else \
                                  "🔥" if chat_info['conversation_stage'] == "warming_up" else \
                                  "💕" if chat_info['conversation_stage'] == "engaged" else "😍"
                    
                    text += f"{i}. {status} {stage_emoji} **{chat_info['client_name']}**\n"
                    text += f"   💌 {chat_info['message_count']} сообщений\n"
                    text += f"   📝 _{chat_info['last_message'][:40]}..._\n\n"
                
                keyboard = get_chat_list_keyboard(user.chat_manager, page)
            
            # Пытаемся редактировать сообщение, если не получается - отправляем новое
            try:
                await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            except Exception as edit_error:
                logger.warning(f"Cannot edit message in chat_list, sending new: {str(edit_error)}")
                await safe_send_message(bot, call.message.chat.id, text, reply_markup=keyboard)
            
            # Отвечаем на callback query
            try:
                await bot.answer_callback_query(call.id)
            except Exception as callback_error:
                logger.debug(f"Callback query error (ignored): {str(callback_error)}")
            
        except Exception as e:
            logger.error(f"Error in chat list: {str(e)}", exc_info=True)
            try:
                await bot.answer_callback_query(call.id, "❌ Ошибка отображения чатов")
            except Exception:
                try:
                    await safe_send_message(bot, call.message.chat.id, "❌ Ошибка отображения чатов. Попробуйте еще раз.")
                except Exception as final_error:
                    logger.error(f"Cannot send error message: {str(final_error)}")
    
    async def handle_new_chat(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Создание нового чата"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                user.chat_manager = ChatManager(user_id)
            
            # Устанавливаем состояние ожидания имени клиента
            user.waiting_for_chat_name = True
            
            text = ("➕ **Создание нового чата**\n\n"
                   "Введите имя клиента или оставьте пустое сообщение для автоматического имени:")
            
            try:
                await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id)
            except Exception as edit_error:
                logger.warning(f"Cannot edit message in new_chat, sending new: {str(edit_error)}")
                await safe_send_message(bot, call.message.chat.id, text)
            
            try:
                await bot.answer_callback_query(call.id)
            except Exception as callback_error:
                logger.debug(f"Callback query error (ignored): {str(callback_error)}")
            
        except Exception as e:
            logger.error(f"Error in new chat: {str(e)}", exc_info=True)
            try:
                await bot.answer_callback_query(call.id, "❌ Ошибка создания чата")
            except Exception:
                try:
                    await safe_send_message(bot, call.message.chat.id, "❌ Ошибка создания чата. Попробуйте еще раз.")
                except Exception as final_error:
                    logger.error(f"Cannot send error message: {str(final_error)}")
    
    async def handle_switch_chat(self, bot: AsyncTeleBot, call: types.CallbackQuery, chat_id: str):
        """Переключение на другой чат"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                try:
                    await bot.answer_callback_query(call.id, "❌ Нет доступных чатов")
                except Exception:
                    await safe_send_message(bot, call.message.chat.id, "❌ Нет доступных чатов")
                return
            
            if user.chat_manager.switch_chat(chat_id):
                chat = user.chat_manager.get_active_chat()
                
                text = f"🔄 **Переключено на чат с {chat.client_profile.name}**\n\n"
                text += format_chat_info(chat)
                
                try:
                    await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=get_chat_context_keyboard())
                except Exception as edit_error:
                    logger.warning(f"Cannot edit message in switch_chat, sending new: {str(edit_error)}")
                    await safe_send_message(bot, call.message.chat.id, text, reply_markup=get_chat_context_keyboard())
                
                try:
                    await bot.answer_callback_query(call.id, f"✅ Переключено на {chat.client_profile.name}")
                except Exception as callback_error:
                    logger.debug(f"Callback query error (ignored): {str(callback_error)}")
                
                await self.state_manager.save_data()
            else:
                try:
                    await bot.answer_callback_query(call.id, "❌ Чат не найден")
                except Exception:
                    await safe_send_message(bot, call.message.chat.id, "❌ Чат не найден")
                
        except Exception as e:
            logger.error(f"Error switching chat: {str(e)}", exc_info=True)
            try:
                await bot.answer_callback_query(call.id, "❌ Ошибка переключения чата")
            except Exception:
                try:
                    await safe_send_message(bot, call.message.chat.id, "❌ Ошибка переключения чата. Попробуйте еще раз.")
                except Exception as final_error:
                    logger.error(f"Cannot send error message: {str(final_error)}")
    
    async def handle_chat_reply(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Подготовка к ответу в активном чате"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                try:
                    await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                except Exception:
                    await safe_send_message(bot, call.message.chat.id, "❌ Нет активного чата")
                return
            
            active_chat = user.chat_manager.get_active_chat()
            if not active_chat:
                try:
                    await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                except Exception:
                    await safe_send_message(bot, call.message.chat.id, "❌ Нет активного чата")
                return
            
            # Устанавливаем состояние ожидания сообщения для ответа
            user.waiting_for_chat_reply = True
            
            text = f"💬 **Ответ клиенту {active_chat.client_profile.name}**\n\n"
            text += "Введите сообщение от клиента, и я создам подходящий ответ, учитывая всю историю общения:\n\n"
            
            # Показываем последние сообщения для контекста
            recent_messages = active_chat.get_recent_messages(3)
            if recent_messages:
                text += "📝 **Последние сообщения:**\n"
                for msg in recent_messages:
                    role_emoji = "👤" if msg.role == "user" else "🤖"
                    text += f"{role_emoji} {msg.content[:50]}...\n"
            
            try:
                await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id)
            except Exception as edit_error:
                logger.warning(f"Cannot edit message in chat_reply, sending new: {str(edit_error)}")
                await safe_send_message(bot, call.message.chat.id, text)
            
            try:
                await bot.answer_callback_query(call.id)
            except Exception as callback_error:
                logger.debug(f"Callback query error (ignored): {str(callback_error)}")
            
        except Exception as e:
            logger.error(f"Error in chat reply: {str(e)}", exc_info=True)
            try:
                await bot.answer_callback_query(call.id, "❌ Ошибка подготовки ответа")
            except Exception:
                try:
                    await safe_send_message(bot, call.message.chat.id, "❌ Ошибка подготовки ответа. Попробуйте еще раз.")
                except Exception as final_error:
                    logger.error(f"Cannot send error message: {str(final_error)}")
    
    async def handle_chat_memory(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Отображение памяти о клиенте"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                try:
                    await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                except Exception:
                    await safe_send_message(bot, call.message.chat.id, "❌ Нет активного чата")
                return
            
            active_chat = user.chat_manager.get_active_chat()
            if not active_chat:
                try:
                    await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                except Exception:
                    await safe_send_message(bot, call.message.chat.id, "❌ Нет активного чата")
                return
            
            memory_text = format_chat_memory(active_chat)
            
            # Создаем inline клавиатуру для редактирования памяти
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("✏️ Добавить заметку", callback_data="memory_add_note"),
                types.InlineKeyboardButton("🏷 Добавить тег", callback_data="memory_add_tag")
            )
            keyboard.row(
                types.InlineKeyboardButton("💝 Предпочтения", callback_data="memory_preferences"),
                types.InlineKeyboardButton("❤️ Интересы", callback_data="memory_interests")
            )
            keyboard.row(
                types.InlineKeyboardButton("🔙 Назад", callback_data="chat_management")
            )
            
            try:
                await safe_edit_message_text(bot, memory_text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            except Exception as edit_error:
                logger.warning(f"Cannot edit message in chat_memory, sending new: {str(edit_error)}")
                await safe_send_message(bot, call.message.chat.id, memory_text, reply_markup=keyboard)
            
            try:
                await bot.answer_callback_query(call.id)
            except Exception as callback_error:
                logger.debug(f"Callback query error (ignored): {str(callback_error)}")
            
        except Exception as e:
            logger.error(f"Error in chat memory: {str(e)}", exc_info=True)
            try:
                await bot.answer_callback_query(call.id, "❌ Ошибка отображения памяти")
            except Exception:
                try:
                    await safe_send_message(bot, call.message.chat.id, "❌ Ошибка отображения памяти. Попробуйте еще раз.")
                except Exception as final_error:
                    logger.error(f"Cannot send error message: {str(final_error)}")
    
    async def handle_chat_analytics(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Отображение аналитики чатов"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                user.chat_manager = ChatManager(user_id)
            
            analytics_text = format_chat_analytics(user.chat_manager)
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("🔄 Обновить", callback_data="chat_analytics"),
                types.InlineKeyboardButton("💬 К чатам", callback_data="chat_list")
            )
            keyboard.row(
                types.InlineKeyboardButton("🔙 Назад", callback_data="chat_management")
            )
            
            try:
                await safe_edit_message_text(bot, analytics_text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            except Exception as edit_error:
                logger.warning(f"Cannot edit message in chat_analytics, sending new: {str(edit_error)}")
                await safe_send_message(bot, call.message.chat.id, analytics_text, reply_markup=keyboard)
            
            try:
                await bot.answer_callback_query(call.id)
            except Exception as callback_error:
                logger.debug(f"Callback query error (ignored): {str(callback_error)}")
            
        except Exception as e:
            logger.error(f"Error in chat analytics: {str(e)}", exc_info=True)
            try:
                await bot.answer_callback_query(call.id, "❌ Ошибка аналитики")
            except Exception:
                try:
                    await safe_send_message(bot, call.message.chat.id, "❌ Ошибка аналитики. Попробуйте еще раз.")
                except Exception as final_error:
                    logger.error(f"Cannot send error message: {str(final_error)}")
    
    async def process_chat_name_input(self, bot: AsyncTeleBot, message: types.Message):
        """Обработка ввода имени для нового чата"""
        try:
            user_id = message.from_user.id
            user = self.state_manager.get_user(user_id)
            
            client_name = message.text.strip() if message.text else ""
            
            # Создаем новый чат
            new_chat = user.chat_manager.create_chat(client_name=client_name)
            
            user.waiting_for_chat_name = False
            
            text = f"✅ **Чат создан!**\n\n"
            text += format_chat_info(new_chat)
            text += "\nТеперь вы можете начать общение с этим клиентом."
            
            await safe_send_message(bot, message.chat.id, text, reply_markup=get_chat_context_keyboard())
            
            await self.state_manager.save_data()
            
        except Exception as e:
            logger.error(f"Error processing chat name: {str(e)}", exc_info=True)
            await safe_send_message(bot, message.chat.id, "❌ Ошибка создания чата")
    
    async def process_chat_reply_input(self, bot: AsyncTeleBot, message: types.Message):
        """Обработка сообщения клиента для генерации ответа"""
        try:
            user_id = message.from_user.id
            user = self.state_manager.get_user(user_id)
            
            client_message = message.text.strip()
            active_chat = user.chat_manager.get_active_chat()
            
            if not active_chat:
                await safe_send_message(bot, message.chat.id, "❌ Нет активного чата")
                return
            
            # Добавляем сообщение клиента в историю
            user.chat_manager.add_message_to_active_chat("user", client_message, "text")
            
            # Показываем статус генерации
            wait_msg = await safe_send_message(bot, message.chat.id, 
                f"🤔 Генерирую ответ для **{active_chat.client_profile.name}**...",
                parse_mode='Markdown'
            )
            
            try:
                # Создаем контекстный промпт
                context_prompt = create_chat_context_prompt(active_chat, client_message)
                
                # Генерируем ответ
                response = await generate_groq_response(
                    context_prompt,
                    MODELS[user.model]['id']
                )
                
                # Добавляем ответ в историю
                user.chat_manager.add_message_to_active_chat("assistant", response, "reply")
                
                user.waiting_for_chat_reply = False
                
                # Отправляем результат
                result_text = f"💬 **Ответ для {active_chat.client_profile.name}:**\n\n{response}\n\n"
                result_text += f"📊 Этап диалога: {active_chat.conversation_stage}\n"
                result_text += f"💌 Всего сообщений: {len(active_chat.messages)}"
                
                await safe_edit_message_text(bot, result_text, wait_msg.chat.id, wait_msg.message_id, reply_markup=get_chat_context_keyboard())
                
                await self.state_manager.save_data()
                
            except Exception as e:
                logger.error(f"Error generating chat response: {str(e)}", exc_info=True)
                await safe_edit_message_text(bot, 
                    f"❌ Ошибка генерации ответа: {str(e)}\n\n"
                    "Попробуйте еще раз или смените модель.",
                    wait_msg.chat.id,
                    wait_msg.message_id
                )
                
        except Exception as e:
            logger.error(f"Error processing chat reply: {str(e)}", exc_info=True)
            await safe_send_message(bot, message.chat.id, "❌ Ошибка обработки сообщения")
    
    def get_callback_handlers(self) -> dict:
        """Возвращает словарь обработчиков callback'ов"""
        return {
            "chat_management": self.handle_chat_management,
            "chat_list": lambda bot, call: self.handle_chat_list(bot, call, 0),
            "chat_new": self.handle_new_chat,
            "chat_reply": self.handle_chat_reply,
            "chat_memory": self.handle_chat_memory,
            "chat_analytics": self.handle_chat_analytics,
        }
    
    def handle_callback_with_params(self, callback_data: str):
        """Обработка callback'ов с параметрами"""
        if callback_data.startswith("chat_switch_"):
            chat_id = callback_data.replace("chat_switch_", "")
            return lambda bot, call: self.handle_switch_chat(bot, call, chat_id)
        
        if callback_data.startswith("chat_list_page_"):
            page = int(callback_data.replace("chat_list_page_", ""))
            return lambda bot, call: self.handle_chat_list(bot, call, page)
        
        return None
    
    async def handle_chat_flirt(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Обработка генерации флирта в контексте чата"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                user.chat_manager = ChatManager(user_id)
            
            active_chat = user.chat_manager.get_active_chat()
            if not active_chat:
                await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                return
            
            text = f"💕 Генерация флирта для {active_chat.client_profile.name}\n\n"
            text += "Выберите стиль флирта:"
            
            from utils import get_flirt_style_keyboard
            
            try:
                await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=get_flirt_style_keyboard())
            except Exception:
                await safe_send_message(bot, call.message.chat.id, text, reply_markup=get_flirt_style_keyboard())
            
            await bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Error in chat flirt: {str(e)}", exc_info=True)
            await bot.answer_callback_query(call.id, "❌ Ошибка")
    
    async def handle_chat_ppv(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Обработка создания PPV в контексте чата"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            active_chat = user.chat_manager.get_active_chat()
            if not active_chat:
                await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                return
            
            text = f"🎁 Создание PPV для {active_chat.client_profile.name}\n\n"
            text += "Выберите стиль PPV:"
            
            from utils import get_ppv_style_keyboard
            
            try:
                await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=get_ppv_style_keyboard())
            except Exception:
                await safe_send_message(bot, call.message.chat.id, text, reply_markup=get_ppv_style_keyboard())
            
            await bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Error in chat ppv: {str(e)}", exc_info=True)
            await bot.answer_callback_query(call.id, "❌ Ошибка")
    
    async def handle_chat_tips(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Обработка создания запроса чаевых в контексте чата"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            active_chat = user.chat_manager.get_active_chat()
            if not active_chat:
                await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                return
            
            text = f"💰 Запрос чаевых для {active_chat.client_profile.name}\n\n"
            text += "Напишите ситуацию, и я создам деликатный запрос на чаевые.\n\n"
            text += "*Пример:* После показа танца\n"
            text += "*Результат:* Милый запрос с благодарностью"
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("🔙 Назад", callback_data="chat_management")
            )
            
            try:
                await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            except Exception:
                await safe_send_message(bot, call.message.chat.id, text, reply_markup=keyboard)
            
            await bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Error in chat tips: {str(e)}", exc_info=True)
            await bot.answer_callback_query(call.id, "❌ Ошибка")
    
    async def handle_chat_note(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Обработка добавления заметки о клиенте"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            active_chat = user.chat_manager.get_active_chat()
            if not active_chat:
                await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                return
            
            text = f"📝 Заметка о клиенте {active_chat.client_profile.name}\n\n"
            
            # Показываем существующие заметки
            notes = active_chat.client_memory.get("notes", [])
            if notes:
                text += "*Существующие заметки:*\n"
                for i, note in enumerate(notes[-3:], 1):  # Последние 3
                    text += f"{i}. {note[:50]}...\n"
                text += "\n"
            
            text += "Напишите новую заметку о клиенте (предпочтения, особенности, важные моменты):"
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("🔙 Назад", callback_data="chat_management")
            )
            
            try:
                await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            except Exception:
                await safe_send_message(bot, call.message.chat.id, text, reply_markup=keyboard)
            
            await bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Error in chat note: {str(e)}", exc_info=True)
            await bot.answer_callback_query(call.id, "❌ Ошибка")
    
    async def handle_chat_tags(self, bot: AsyncTeleBot, call: types.CallbackQuery):
        """Обработка добавления тегов к клиенту"""
        try:
            user_id = call.from_user.id
            user = self.state_manager.get_user(user_id)
            
            active_chat = user.chat_manager.get_active_chat()
            if not active_chat:
                await bot.answer_callback_query(call.id, "❌ Нет активного чата")
                return
            
            text = f"🏷 Теги для клиента {active_chat.client_profile.name}\n\n"
            
            # Показываем существующие теги
            tags = active_chat.client_memory.get("tags", [])
            if tags:
                text += f"*Текущие теги:* {', '.join(tags)}\n\n"
            
            text += "*Популярные теги:*\n"
            text += "• VIP, постоянный, щедрый\n"
            text += "• любит_фото, предпочитает_видео\n"
            text += "• утром_активен, вечером_онлайн\n"
            text += "• флиртующий, серьезный\n\n"
            text += "Напишите теги через запятую:"
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("🔙 Назад", callback_data="chat_management")
            )
            
            try:
                await safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            except Exception:
                await safe_send_message(bot, call.message.chat.id, text, reply_markup=keyboard)
            
            await bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Error in chat tags: {str(e)}", exc_info=True)
            await bot.answer_callback_query(call.id, "❌ Ошибка") 