"""
🎯 ЕДИНЫЙ CALLBACK HANDLER
Централизованная обработка всех callback запросов
Решает проблемы конфликтов между разными системами
"""

import logging
from typing import Dict, Callable, Any, Optional
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from ui_manager import ui_manager, UIState
from premium_system import premium_manager

logger = logging.getLogger(__name__)

class CallbackRouter:
    """Маршрутизатор callback'ов"""
    
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.handlers: Dict[str, Callable] = {}
        self.register_core_handlers()
    
    def register_handler(self, prefix: str, handler: Callable):
        """Регистрирует обработчик для префикса"""
        self.handlers[prefix] = handler
        logger.info(f"Registered callback handler for prefix: {prefix}")
    
    def register_core_handlers(self):
        """Регистрирует основные обработчики"""
        
        # UI система
        self.register_handler("ui_", self.handle_ui_callbacks)
        
        # Админ система
        self.register_handler("admin_", self.handle_admin_callbacks)
        
        # Платежная система
        self.register_handler("payment_", self.handle_payment_callbacks)
        
        # Premium система
        self.register_handler("premium_", self.handle_premium_callbacks)
        
        # Legacy обработчики
        self.register_handler("continue_", self.handle_legacy_callbacks)
        self.register_handler("add_", self.handle_legacy_callbacks)
        self.register_handler("quick_", self.handle_legacy_callbacks)
        self.register_handler("main_", self.handle_legacy_callbacks)
        self.register_handler("back_", self.handle_legacy_callbacks)
    
    async def route_callback(self, call: types.CallbackQuery) -> bool:
        """Маршрутизирует callback к соответствующему обработчику"""
        try:
            callback_data = call.data
            user_id = call.from_user.id
            
            logger.info(f"Routing callback: {callback_data} from user {user_id}")
            
            # Находим подходящий обработчик
            for prefix, handler in self.handlers.items():
                if callback_data.startswith(prefix):
                    result = await handler(call)
                    if result:
                        return True
            
            # Если не нашли обработчик
            logger.warning(f"No handler found for callback: {callback_data}")
            await self.bot.answer_callback_query(call.id, "❌ Неизвестная команда")
            return False
            
        except Exception as e:
            logger.error(f"Error routing callback: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка обработки")
            return False
    
    async def handle_ui_callbacks(self, call: types.CallbackQuery) -> bool:
        """Обрабатывает UI callback'и"""
        try:
            user_id = call.from_user.id
            action = call.data[3:]  # Убираем "ui_"
            
            # Базовая обработка состояний
            ui_manager.handle_callback(call)
            
            # Получаем информацию о пользователе
            user_sub = premium_manager.get_user_subscription(user_id)
            user_tier = user_sub.tier.value if user_sub else "free"
            
            # Обрабатываем конкретные действия
            if action == "main_menu":
                await self.send_main_menu(call, user_tier)
                
            elif action == "start_chat":
                ui_manager.set_user_state(user_id, UIState.CHAT_MODE)
                await self.send_chat_interface(call)
                
            elif action == "flirt_mode":
                await self.send_flirt_interface(call)
                
            elif action == "upgrade_menu":
                ui_manager.set_user_state(user_id, UIState.PREMIUM_MENU)
                await self.send_premium_menu(call, user_tier)
                
            elif action == "settings":
                ui_manager.set_user_state(user_id, UIState.SETTINGS)
                await self.send_settings_menu(call)
                
            elif action.startswith("admin"):
                if self.is_admin(user_id):
                    ui_manager.set_user_state(user_id, UIState.ADMIN_PANEL)
                    await self.send_admin_panel(call)
                else:
                    await self.bot.answer_callback_query(call.id, "❌ Нет прав доступа")
                    
            elif action.startswith("heat_set_"):
                level = int(action.split("_")[-1])
                await self.set_heat_level(call, level)
                
            elif action.startswith("mode_set_"):
                mode = action.split("_")[-1]
                await self.set_chat_mode(call, mode)
                
            elif action.startswith("rate_"):
                await self.handle_rating(call)
                
            elif action.startswith("favorite_"):
                await self.handle_favorite(call)
                
            else:
                # Неизвестное UI действие
                logger.warning(f"Unknown UI action: {action}")
                await self.bot.answer_callback_query(call.id, "⚠️ Функция в разработке")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in UI callback handler: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка UI")
            return False
    
    async def handle_admin_callbacks(self, call: types.CallbackQuery) -> bool:
        """Обрабатывает админ callback'и"""
        try:
            user_id = call.from_user.id
            
            if not self.is_admin(user_id):
                await self.bot.answer_callback_query(call.id, "❌ Нет прав доступа")
                return True
            
            action = call.data[6:]  # Убираем "admin_"
            
            if action == "users":
                await self.show_admin_users(call)
            elif action == "revenue":
                await self.show_admin_revenue(call)
            elif action == "stats":
                await self.show_admin_stats(call)
            elif action == "health":
                await self.show_admin_health(call)
            elif action == "grant":
                await self.show_grant_premium_menu(call)
            elif action == "test":
                await self.show_test_mode(call)
            elif action == "ton":
                await self.show_ton_menu(call)
            elif action == "help":
                await self.show_admin_help(call)
            else:
                await self.bot.answer_callback_query(call.id, "⚠️ Админ функция в разработке")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in admin callback handler: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Админ ошибка")
            return False
    
    async def handle_payment_callbacks(self, call: types.CallbackQuery) -> bool:
        """Обрабатывает платежные callback'и"""
        try:
            user_id = call.from_user.id
            action = call.data[8:]  # Убираем "payment_"
            
            if action == "upgrade":
                await self.show_upgrade_options(call)
            elif action == "pricing":
                await self.show_pricing_info(call)
            elif action.startswith("stars_"):
                tier = action.split("_")[1]
                await self.initiate_stars_payment(call, tier)
            elif action == "method_ton":
                await self.show_ton_payment(call)
            else:
                await self.bot.answer_callback_query(call.id, "⚠️ Платежная функция в разработке")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in payment callback handler: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Платежная ошибка")
            return False
    
    async def handle_premium_callbacks(self, call: types.CallbackQuery) -> bool:
        """Обрабатывает premium callback'и"""
        try:
            user_id = call.from_user.id
            action = call.data[8:]  # Убираем "premium_"
            
            user_sub = premium_manager.get_user_subscription(user_id)
            
            if action == "status":
                await self.show_premium_status(call, user_sub)
            elif action == "upgrade":
                await self.show_upgrade_options(call)
            elif action == "content":
                if premium_manager.can_access_premium_content(user_id):
                    await self.show_premium_content(call)
                else:
                    await self.show_upgrade_prompt(call)
            else:
                await self.bot.answer_callback_query(call.id, "⚠️ Premium функция в разработке")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in premium callback handler: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Premium ошибка")
            return False
    
    async def handle_legacy_callbacks(self, call: types.CallbackQuery) -> bool:
        """Обрабатывает legacy callback'и для обратной совместимости"""
        try:
            callback_data = call.data
            
            # Маппинг старых callback'ов на новые UI действия
            legacy_mapping = {
                "continue_writing": "ui_continue_chat",
                "add_flirt": "ui_add_flirt",
                "quick_ppv": "ui_suggest_ppv",
                "quick_tips": "ui_request_tips",
                "main_menu": "ui_main_menu",
                "back_to_main": "ui_main_menu"
            }
            
            if callback_data in legacy_mapping:
                # Преобразуем в новый формат
                new_call_data = legacy_mapping[callback_data]
                call.data = new_call_data
                return await self.handle_ui_callbacks(call)
            
            # Если не нашли маппинг
            logger.warning(f"Unmapped legacy callback: {callback_data}")
            await self.bot.answer_callback_query(call.id, "⚠️ Устаревшая функция")
            return True
            
        except Exception as e:
            logger.error(f"Error in legacy callback handler: {str(e)}", exc_info=True)
            return False
    
    # === HELPER METHODS ===
    
    def is_admin(self, user_id: int) -> bool:
        """Проверяет является ли пользователь админом"""
        admin_ids = [377917978]  # ID админа
        return user_id in admin_ids
    
    async def send_main_menu(self, call: types.CallbackQuery, user_tier: str = "free"):
        """Отправляет главное меню"""
        keyboard = ui_manager.create_main_menu_keyboard(user_tier)
        
        main_menu_text = f"""🏠 ГЛАВНОЕ МЕНЮ

👋 Привет! Я твоя личная AI подружка 💕

🎯 Твой статус: {user_tier.upper()}
💬 Доступно: Безлимитное общение
🔥 Режимы: Чат, флирт, секстинг

⚡ Выбери что хочешь делать:"""
        
        try:
            await self.bot.edit_message_text(
                main_menu_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
            await self.bot.answer_callback_query(call.id)
        except Exception as e:
            # Если редактирование не удалось - отправляем новое
            await self.bot.send_message(
                call.message.chat.id,
                main_menu_text,
                reply_markup=keyboard
            )
            await self.bot.answer_callback_query(call.id)
    
    async def send_chat_interface(self, call: types.CallbackQuery):
        """Отправляет интерфейс чата"""
        keyboard = ui_manager.create_chat_keyboard()
        
        chat_text = """💬 РЕЖИМ ЧАТА

🔥 Я готова к общению! Напиши мне что-нибудь...

💝 Или выбери быстрое действие:"""
        
        try:
            await self.bot.edit_message_text(
                chat_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
            await self.bot.answer_callback_query(call.id, "💬 Режим чата активирован!")
        except:
            await self.bot.send_message(
                call.message.chat.id,
                chat_text,
                reply_markup=keyboard
            )
    
    async def send_flirt_interface(self, call: types.CallbackQuery):
        """Отправляет интерфейс флирта"""
        keyboard = ui_manager.create_chat_keyboard()
        
        flirt_text = """😘 ФЛИРТ РЕЖИМ

🔥 Ммм, готова пофлиртовать с тобой... 💕

💋 Что хочешь услышать, красавчик?"""
        
        try:
            await self.bot.edit_message_text(
                flirt_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
            await self.bot.answer_callback_query(call.id, "😘 Флирт режим включен!")
        except:
            await self.bot.send_message(
                call.message.chat.id,
                flirt_text,
                reply_markup=keyboard
            )
    
    async def send_premium_menu(self, call: types.CallbackQuery, user_tier: str):
        """Отправляет меню премиум подписок"""
        keyboard = ui_manager.create_premium_keyboard(user_tier)
        
        premium_text = f"""💎 ПРЕМИУМ ПОДПИСКИ

🎯 Текущий статус: {user_tier.upper()}

⭐ PREMIUM - 150 Stars/день
• Безлимитное общение
• Базовые функции флирта

🔥 VIP - 250 Stars/день
• Все функции Premium
• Эксклюзивный контент
• Персональные фантазии

👑 ULTIMATE - 500 Stars/день
• Все функции VIP
• Ультра откровенный контент
• Ролевые игры любой сложности
• Персональная AI модель

💎 Также доступна оплата TON"""
        
        try:
            await self.bot.edit_message_text(
                premium_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
            await self.bot.answer_callback_query(call.id)
        except:
            await self.bot.send_message(
                call.message.chat.id,
                premium_text,
                reply_markup=keyboard
            )
    
    async def send_settings_menu(self, call: types.CallbackQuery):
        """Отправляет меню настроек"""
        keyboard = ui_manager.create_settings_keyboard()
        
        settings_text = """⚙️ НАСТРОЙКИ

🎛️ Настрой бот под себя:

🌡️ Откровенность - уровень контента
🎭 Режим чата - стиль общения
🔔 Уведомления - когда присылать
🌐 Язык - русский/английский
🔒 Приватность - защита данных"""
        
        try:
            await self.bot.edit_message_text(
                settings_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
            await self.bot.answer_callback_query(call.id)
        except:
            await self.bot.send_message(
                call.message.chat.id,
                settings_text,
                reply_markup=keyboard
            )
    
    async def send_admin_panel(self, call: types.CallbackQuery):
        """Отправляет админ панель"""
        keyboard = ui_manager.create_admin_keyboard()
        
        admin_text = """👨‍💼 АДМИН ПАНЕЛЬ

🛠️ Управление системой:

👥 Пользователи - управление аккаунтами
💰 Доходы - финансовая статистика
🎁 Выдать Premium - активация подписок
🧪 Тест режим - отладка функций
📊 Статистика - аналитика системы
🔧 Диагностика - состояние бота
💎 TON платежи - криптовалютные операции"""
        
        try:
            await self.bot.edit_message_text(
                admin_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
            await self.bot.answer_callback_query(call.id)
        except:
            await self.bot.send_message(
                call.message.chat.id,
                admin_text,
                reply_markup=keyboard
            )
    
    async def set_heat_level(self, call: types.CallbackQuery, level: int):
        """Устанавливает уровень откровенности"""
        user_id = call.from_user.id
        
        # Тут должна быть логика сохранения уровня в базу
        # Пока просто уведомляем
        
        level_names = {
            1: "😊 Мягкий",
            2: "😏 Средний", 
            3: "🔥 Горячий",
            4: "💦 Страстный",
            5: "🔞 Экстрим"
        }
        
        level_name = level_names.get(level, "Неизвестный")
        
        await self.bot.answer_callback_query(
            call.id, 
            f"🌡️ Уровень установлен: {level_name}"
        )
        
        # Возвращаемся в настройки
        await self.send_settings_menu(call)
    
    async def set_chat_mode(self, call: types.CallbackQuery, mode: str):
        """Устанавливает режим чата"""
        user_id = call.from_user.id
        
        mode_names = {
            "chat": "💬 Дружеское общение",
            "flirt": "😘 Флирт",
            "sexting": "🔞 Секстинг"
        }
        
        mode_name = mode_names.get(mode, "Неизвестный")
        
        await self.bot.answer_callback_query(
            call.id,
            f"🎭 Режим установлен: {mode_name}"
        )
        
        # Возвращаемся в настройки
        await self.send_settings_menu(call)
    
    async def handle_rating(self, call: types.CallbackQuery):
        """Обрабатывает рейтинг ответа"""
        parts = call.data.split("_")
        rating = parts[2]
        message_id = parts[3]
        
        await self.bot.answer_callback_query(
            call.id,
            f"⭐ Спасибо за оценку: {rating}/5!"
        )
        
        # Убираем кнопки рейтинга
        try:
            await self.bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except:
            pass
    
    async def handle_favorite(self, call: types.CallbackQuery):
        """Обрабатывает добавление в избранное"""
        user_id = call.from_user.id
        message_id = call.data.split("_")[-1]
        
        # Тут должна быть логика сохранения в избранное
        
        await self.bot.answer_callback_query(
            call.id,
            "💝 Добавлено в избранное!"
        )
    
    # Placeholder методы для админ функций
    async def show_admin_users(self, call): await self.bot.answer_callback_query(call.id, "👥 Функция в разработке")
    async def show_admin_revenue(self, call): await self.bot.answer_callback_query(call.id, "💰 Функция в разработке")
    async def show_admin_stats(self, call): await self.bot.answer_callback_query(call.id, "📊 Функция в разработке")
    async def show_admin_health(self, call): await self.bot.answer_callback_query(call.id, "🔧 Функция в разработке")
    async def show_grant_premium_menu(self, call): await self.bot.answer_callback_query(call.id, "🎁 Функция в разработке")
    async def show_test_mode(self, call): await self.bot.answer_callback_query(call.id, "🧪 Функция в разработке")
    async def show_ton_menu(self, call): await self.bot.answer_callback_query(call.id, "💎 Функция в разработке")
    async def show_admin_help(self, call): await self.bot.answer_callback_query(call.id, "📋 Функция в разработке")
    
    # Placeholder методы для платежных функций
    async def show_upgrade_options(self, call): await self.bot.answer_callback_query(call.id, "💎 Функция в разработке")
    async def show_pricing_info(self, call): await self.bot.answer_callback_query(call.id, "💰 Функция в разработке")
    async def initiate_stars_payment(self, call, tier): await self.bot.answer_callback_query(call.id, "⭐ Функция в разработке")
    async def show_ton_payment(self, call): await self.bot.answer_callback_query(call.id, "💎 Функция в разработке")
    
    # Placeholder методы для premium функций
    async def show_premium_status(self, call, user_sub): await self.bot.answer_callback_query(call.id, "📊 Функция в разработке")
    async def show_premium_content(self, call): await self.bot.answer_callback_query(call.id, "🔥 Функция в разработке")
    async def show_upgrade_prompt(self, call): await self.bot.answer_callback_query(call.id, "💎 Функция в разработке")

# Глобальный экземпляр
callback_router = None

def initialize_callback_router(bot: AsyncTeleBot) -> CallbackRouter:
    """Инициализирует и возвращает callback router"""
    global callback_router
    callback_router = CallbackRouter(bot)
    return callback_router 