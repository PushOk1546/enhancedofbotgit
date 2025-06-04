"""
🎨 ЕДИНЫЙ UI МЕНЕДЖЕР
Централизованное управление всеми клавиатурами и интерфейсом бота
Решает проблемы конфликтов и несовместимости UI элементов
"""

import logging
from typing import Dict, List, Optional, Any
from telebot import types
from enum import Enum

logger = logging.getLogger(__name__)

class UIState(Enum):
    """Состояния пользовательского интерфейса"""
    MAIN_MENU = "main_menu"
    CHAT_MODE = "chat_mode" 
    ADMIN_PANEL = "admin_panel"
    PREMIUM_MENU = "premium_menu"
    SETTINGS = "settings"
    CONTENT_MENU = "content_menu"

class KeyboardType(Enum):
    """Типы клавиатур"""
    INLINE = "inline"
    REPLY = "reply"

class UIManager:
    """Централизованный менеджер UI"""
    
    def __init__(self):
        self.user_states: Dict[int, UIState] = {}
        self.active_keyboards: Dict[int, types.InlineKeyboardMarkup] = {}
        
        # Эмодзи константы для консистентности
        self.EMOJIS = {
            'chat': '💬',
            'flirt': '😘', 
            'premium': '💎',
            'money': '💰',
            'gift': '🎁',
            'settings': '⚙️',
            'admin': '👨‍💼',
            'stats': '📊',
            'home': '🏠',
            'back': '🔙',
            'fire': '🔥',
            'heart': '💝',
            'star': '⭐',
            'check': '✅',
            'cross': '❌'
        }
    
    def set_user_state(self, user_id: int, state: UIState):
        """Устанавливает состояние UI для пользователя"""
        self.user_states[user_id] = state
        logger.debug(f"UI state set for user {user_id}: {state.value}")
    
    def get_user_state(self, user_id: int) -> UIState:
        """Получает текущее состояние UI пользователя"""
        return self.user_states.get(user_id, UIState.MAIN_MENU)
    
    def create_main_menu_keyboard(self, user_tier: str = "free") -> types.InlineKeyboardMarkup:
        """🏠 Создает главное меню с учетом тарифа пользователя"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Основные функции
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['chat']} Начать чат", 
                callback_data="ui_start_chat"
            ),
            types.InlineKeyboardButton(
                f"{self.EMOJIS['flirt']} Флирт режим", 
                callback_data="ui_flirt_mode"
            )
        )
        
        # Premium функции
        if user_tier == "free":
            keyboard.add(
                types.InlineKeyboardButton(
                    f"{self.EMOJIS['premium']} Апгрейд", 
                    callback_data="ui_upgrade_menu"
                ),
                types.InlineKeyboardButton(
                    f"{self.EMOJIS['gift']} Бесплатные", 
                    callback_data="ui_free_content"
                )
            )
        else:
            keyboard.add(
                types.InlineKeyboardButton(
                    f"{self.EMOJIS['fire']} Эксклюзив", 
                    callback_data="ui_premium_content"
                ),
                types.InlineKeyboardButton(
                    f"{self.EMOJIS['star']} VIP чат", 
                    callback_data="ui_vip_chat"
                )
            )
        
        # Дополнительные функции
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['stats']} Мой профиль", 
                callback_data="ui_profile"
            ),
            types.InlineKeyboardButton(
                f"{self.EMOJIS['settings']} Настройки", 
                callback_data="ui_settings"
            )
        )
        
        return keyboard
    
    def create_chat_keyboard(self, context: Dict[str, Any] = None) -> types.InlineKeyboardMarkup:
        """💬 Создает клавиатуру для режима чата"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Быстрые ответы
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['chat']} Продолжить", 
                callback_data="ui_continue_chat"
            ),
            types.InlineKeyboardButton(
                f"{self.EMOJIS['flirt']} Добавить флирт", 
                callback_data="ui_add_flirt"
            )
        )
        
        # Монетизация
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['gift']} PPV предложение", 
                callback_data="ui_suggest_ppv"
            ),
            types.InlineKeyboardButton(
                f"{self.EMOJIS['money']} Чаевые", 
                callback_data="ui_request_tips"
            )
        )
        
        # Настройки режима
        keyboard.add(
            types.InlineKeyboardButton(
                "🌡️ Уровень откровенности", 
                callback_data="ui_heat_level"
            ),
            types.InlineKeyboardButton(
                "🎭 Сменить режим", 
                callback_data="ui_change_mode"
            )
        )
        
        # Навигация
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['home']} Главное меню", 
                callback_data="ui_main_menu"
            )
        )
        
        return keyboard
    
    def create_admin_keyboard(self) -> types.InlineKeyboardMarkup:
        """👨‍💼 Создает админ панель"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Управление
        keyboard.add(
            types.InlineKeyboardButton(
                "👥 Пользователи", 
                callback_data="ui_admin_users"
            ),
            types.InlineKeyboardButton(
                f"{self.EMOJIS['money']} Доходы", 
                callback_data="ui_admin_revenue"
            )
        )
        
        # Премиум
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['gift']} Выдать Premium", 
                callback_data="ui_admin_grant"
            ),
            types.InlineKeyboardButton(
                "🧪 Тест режим", 
                callback_data="ui_admin_test"
            )
        )
        
        # Система
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['stats']} Статистика", 
                callback_data="ui_admin_stats"
            ),
            types.InlineKeyboardButton(
                "🔧 Диагностика", 
                callback_data="ui_admin_health"
            )
        )
        
        # TON платежи
        keyboard.add(
            types.InlineKeyboardButton(
                "💎 TON платежи", 
                callback_data="ui_admin_ton"
            ),
            types.InlineKeyboardButton(
                "📋 Справка", 
                callback_data="ui_admin_help"
            )
        )
        
        # Назад
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['back']} Назад", 
                callback_data="ui_main_menu"
            )
        )
        
        return keyboard
    
    def create_premium_keyboard(self, user_tier: str = "free") -> types.InlineKeyboardMarkup:
        """💎 Создает меню подписок"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        # Текущий статус
        if user_tier == "free":
            keyboard.add(
                types.InlineKeyboardButton(
                    "🎯 БЕСПЛАТНАЯ ПРОБНАЯ ВЕРСИЯ", 
                    callback_data="ui_current_status"
                )
            )
        else:
            keyboard.add(
                types.InlineKeyboardButton(
                    f"👑 АКТИВНА: {user_tier.upper()}", 
                    callback_data="ui_current_status"
                )
            )
        
        # Тарифы
        if user_tier in ["free", "premium"]:
            keyboard.add(
                types.InlineKeyboardButton(
                    "⭐ PREMIUM - 150 Stars/день", 
                    callback_data="ui_buy_premium"
                )
            )
        
        if user_tier in ["free", "premium", "vip"]:
            keyboard.add(
                types.InlineKeyboardButton(
                    "🔥 VIP - 250 Stars/день", 
                    callback_data="ui_buy_vip"
                )
            )
        
        if user_tier != "ultimate":
            keyboard.add(
                types.InlineKeyboardButton(
                    "👑 ULTIMATE - 500 Stars/день", 
                    callback_data="ui_buy_ultimate"
                )
            )
        
        # Криптоплатежи
        keyboard.add(
            types.InlineKeyboardButton(
                "💎 Оплата TON", 
                callback_data="ui_pay_ton"
            )
        )
        
        # Назад
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['back']} Назад", 
                callback_data="ui_main_menu"
            )
        )
        
        return keyboard
    
    def create_settings_keyboard(self) -> types.InlineKeyboardMarkup:
        """⚙️ Создает меню настроек"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Контент настройки
        keyboard.add(
            types.InlineKeyboardButton(
                "🌡️ Откровенность", 
                callback_data="ui_set_heat"
            ),
            types.InlineKeyboardButton(
                "🎭 Режим чата", 
                callback_data="ui_set_mode"
            )
        )
        
        # Уведомления
        keyboard.add(
            types.InlineKeyboardButton(
                "🔔 Уведомления", 
                callback_data="ui_notifications"
            ),
            types.InlineKeyboardButton(
                "🌐 Язык", 
                callback_data="ui_language"
            )
        )
        
        # Приватность
        keyboard.add(
            types.InlineKeyboardButton(
                "🔒 Приватность", 
                callback_data="ui_privacy"
            ),
            types.InlineKeyboardButton(
                "📊 Мои данные", 
                callback_data="ui_my_data"
            )
        )
        
        # Назад
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['back']} Назад", 
                callback_data="ui_main_menu"
            )
        )
        
        return keyboard
    
    def create_feedback_keyboard(self, message_id: int) -> types.InlineKeyboardMarkup:
        """⭐ Создает клавиатуру обратной связи"""
        keyboard = types.InlineKeyboardMarkup(row_width=5)
        
        # Рейтинг звездами
        star_buttons = [
            types.InlineKeyboardButton(
                f"{i}⭐", 
                callback_data=f"ui_rate_{i}_{message_id}"
            )
            for i in range(1, 6)
        ]
        keyboard.add(*star_buttons)
        
        # Дополнительные действия
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['heart']} В избранное", 
                callback_data=f"ui_favorite_{message_id}"
            ),
            types.InlineKeyboardButton(
                "🔄 Другой ответ", 
                callback_data=f"ui_regenerate_{message_id}"
            )
        )
        
        return keyboard
    
    def create_heat_level_keyboard(self, current_level: int = 2) -> types.InlineKeyboardMarkup:
        """🌡️ Создает клавиатуру уровня откровенности"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        levels = [
            (1, "😊 Мягкий"),
            (2, "😏 Средний"),
            (3, "🔥 Горячий"),
            (4, "💦 Страстный"),
            (5, "🔞 Экстрим")
        ]
        
        for level, description in levels:
            marker = "🎯 " if level == current_level else ""
            keyboard.add(
                types.InlineKeyboardButton(
                    f"{marker}{description}", 
                    callback_data=f"ui_heat_set_{level}"
                )
            )
        
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['back']} Назад", 
                callback_data="ui_settings"
            )
        )
        
        return keyboard
    
    def create_mode_keyboard(self, current_mode: str = "chat") -> types.InlineKeyboardMarkup:
        """🎭 Создает клавиатуру режимов общения"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        modes = [
            ("chat", "💬 Дружеское общение"),
            ("flirt", "😘 Флирт"),
            ("sexting", "🔞 Секстинг")
        ]
        
        for mode, description in modes:
            marker = "🎯 " if mode == current_mode else ""
            keyboard.add(
                types.InlineKeyboardButton(
                    f"{marker}{description}", 
                    callback_data=f"ui_mode_set_{mode}"
                )
            )
        
        keyboard.add(
            types.InlineKeyboardButton(
                f"{self.EMOJIS['back']} Назад", 
                callback_data="ui_settings"
            )
        )
        
        return keyboard
    
    def handle_callback(self, call: types.CallbackQuery) -> bool:
        """Обрабатывает UI callback'и"""
        if not call.data.startswith("ui_"):
            return False
        
        try:
            user_id = call.from_user.id
            action = call.data[3:]  # Убираем "ui_"
            
            logger.info(f"UI callback: {action} from user {user_id}")
            
            # Обновляем состояние на основе действия
            if action in ["main_menu", "start_chat", "flirt_mode"]:
                self.set_user_state(user_id, UIState.MAIN_MENU)
            elif action.startswith("admin"):
                self.set_user_state(user_id, UIState.ADMIN_PANEL)
            elif action in ["upgrade_menu", "buy_premium", "buy_vip", "buy_ultimate"]:
                self.set_user_state(user_id, UIState.PREMIUM_MENU)
            elif action == "settings":
                self.set_user_state(user_id, UIState.SETTINGS)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling UI callback: {str(e)}", exc_info=True)
            return False
    
    def get_context_keyboard(self, user_id: int, context: str = "") -> types.InlineKeyboardMarkup:
        """Получает клавиатуру на основе контекста пользователя"""
        state = self.get_user_state(user_id)
        
        if state == UIState.ADMIN_PANEL:
            return self.create_admin_keyboard()
        elif state == UIState.PREMIUM_MENU:
            return self.create_premium_keyboard()
        elif state == UIState.SETTINGS:
            return self.create_settings_keyboard()
        elif state == UIState.CHAT_MODE:
            return self.create_chat_keyboard()
        else:
            return self.create_main_menu_keyboard()
    
    def store_keyboard(self, user_id: int, keyboard: types.InlineKeyboardMarkup):
        """Сохраняет активную клавиатуру пользователя"""
        self.active_keyboards[user_id] = keyboard
    
    def get_stored_keyboard(self, user_id: int) -> Optional[types.InlineKeyboardMarkup]:
        """Получает сохраненную клавиатуру пользователя"""
        return self.active_keyboards.get(user_id)

# Глобальный экземпляр UI менеджера
ui_manager = UIManager()

# Utility функции для обратной совместимости
def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    """Legacy функция - создает reply клавиатуру"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton('💬 Написать сообщение'),
        types.KeyboardButton('💝 Флирт'),
        types.KeyboardButton('🎁 Платный контент'),
        types.KeyboardButton('🌟 Чаевые'),
        types.KeyboardButton('👥 Чаты с клиентами'),
        types.KeyboardButton('⚙️ Сменить модель'),
        types.KeyboardButton('ℹ️ Помощь')
    )
    return keyboard

def create_inline_keyboard(buttons: List[List[Dict[str, str]]]) -> types.InlineKeyboardMarkup:
    """Утилита для создания inline клавиатур из конфигурации"""
    keyboard = types.InlineKeyboardMarkup()
    
    for row in buttons:
        button_row = []
        for button in row:
            button_row.append(
                types.InlineKeyboardButton(
                    button['text'], 
                    callback_data=button['callback']
                )
            )
        keyboard.add(*button_row)
    
    return keyboard 