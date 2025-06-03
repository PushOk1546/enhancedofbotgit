"""
Enhanced Command Handlers for Professional OF Bot
Includes heat level, mode switching, favorites, and A/B testing controls.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from telebot.async_telebot import AsyncTeleBot
from telebot import types

from adult_templates import ExplicitnessLevel, ContentMode, TemplateCategory
from response_generator import response_generator, GenerationMethod
from utils import get_main_keyboard

logger = logging.getLogger(__name__)

class EnhancedCommandHandlers:
    """Enhanced command handlers for professional OF bot"""
    
    def __init__(self, bot: AsyncTeleBot, state_manager):
        self.bot = bot
        self.state_manager = state_manager
        self.response_gen = response_generator
    
    async def handle_heat_command(self, message: types.Message):
        """Handle /heat [1-5] command to set explicitness level"""
        try:
            user_id = message.from_user.id
            parts = message.text.split()
            
            if len(parts) < 2:
                # Show current level and options
                prefs = self.response_gen.get_user_preferences(user_id)
                current_level = prefs.explicitness_level.value
                
                text = f"""🌡️ **Настройка уровня откровенности**

Текущий уровень: **{current_level}/5** ({prefs.explicitness_level.name})

Выберите уровень:
1️⃣ **SOFT** - Романтично, нежно
2️⃣ **MEDIUM** - Флирт, намёки  
3️⃣ **EXPLICIT** - Откровенно, прямо
4️⃣ **INTENSE** - Очень откровенно
5️⃣ **EXTREME** - Максимум страсти

Используйте: `/heat [1-5]`"""
                
                keyboard = self._create_heat_keyboard()
                await self.bot.send_message(user_id, text, reply_markup=keyboard)
                return
            
            try:
                level = int(parts[1])
                if level < 1 or level > 5:
                    raise ValueError("Level out of range")
                
                # Convert to ExplicitnessLevel
                explicitness_map = {
                    1: ExplicitnessLevel.SOFT,
                    2: ExplicitnessLevel.MEDIUM,
                    3: ExplicitnessLevel.EXPLICIT,
                    4: ExplicitnessLevel.INTENSE,
                    5: ExplicitnessLevel.EXTREME
                }
                
                new_level = explicitness_map[level]
                await self.response_gen.update_user_preference(
                    user_id, 'explicitness_level', new_level
                )
                
                level_names = {
                    1: "мягко и романтично",
                    2: "флиртуя с намёками", 
                    3: "откровенно и прямо",
                    4: "очень страстно",
                    5: "с максимальной откровенностью"
                }
                
                text = f"🌡️ Уровень откровенности установлен: **{level}/5**\n"
                text += f"Теперь я буду общаться {level_names[level]} 💕"
                
                await self.bot.send_message(user_id, text)
                
            except ValueError:
                await self.bot.send_message(
                    user_id, 
                    "❌ Укажите число от 1 до 5\nПример: `/heat 3`"
                )
                
        except Exception as e:
            logger.error(f"Error in heat command: {str(e)}", exc_info=True)
            await self.bot.send_message(
                message.from_user.id,
                "❌ Ошибка при установке уровня откровенности"
            )
    
    async def handle_mode_command(self, message: types.Message):
        """Handle /mode [chat/flirt/sexting] command"""
        try:
            user_id = message.from_user.id
            parts = message.text.split()
            
            if len(parts) < 2:
                # Show current mode and options
                prefs = self.response_gen.get_user_preferences(user_id)
                current_mode = prefs.content_mode.value
                
                text = f"""💬 **Режим общения**

Текущий режим: **{current_mode}**

Доступные режимы:
💬 **chat** - Обычное общение
😘 **flirt** - Флирт и соблазнение  
🔥 **sexting** - Откровенная переписка

Используйте: `/mode [режим]`"""
                
                keyboard = self._create_mode_keyboard()
                await self.bot.send_message(user_id, text, reply_markup=keyboard)
                return
            
            mode_text = parts[1].lower()
            mode_map = {
                'chat': ContentMode.CHAT,
                'flirt': ContentMode.FLIRT,
                'sexting': ContentMode.SEXTING
            }
            
            if mode_text not in mode_map:
                await self.bot.send_message(
                    user_id,
                    "❌ Доступные режимы: chat, flirt, sexting\nПример: `/mode flirt`"
                )
                return
            
            new_mode = mode_map[mode_text]
            await self.response_gen.update_user_preference(
                user_id, 'content_mode', new_mode
            )
            
            mode_descriptions = {
                'chat': "обычным общением",
                'flirt': "флиртом и соблазнением",
                'sexting': "откровенной перепиской"
            }
            
            text = f"💬 Режим изменён на: **{mode_text}**\n"
            text += f"Теперь я буду заниматься {mode_descriptions[mode_text]} 💕"
            
            await self.bot.send_message(user_id, text)
            
        except Exception as e:
            logger.error(f"Error in mode command: {str(e)}", exc_info=True)
            await self.bot.send_message(
                message.from_user.id,
                "❌ Ошибка при смене режима общения"
            )
    
    async def handle_fav_command(self, message: types.Message):
        """Handle /fav command to manage favorite responses"""
        try:
            user_id = message.from_user.id
            prefs = self.response_gen.get_user_preferences(user_id)
            
            if not prefs.favorite_responses:
                text = """💝 **Избранные ответы**

У вас пока нет избранных ответов.

Чтобы добавить ответ в избранное:
1. Получите ответ, который вам нравится
2. Нажмите кнопку ⭐ под сообщением
3. Ответ сохранится в избранном

Избранные ответы используются для улучшения качества генерации."""
                
                await self.bot.send_message(user_id, text)
                return
            
            # Show favorites with pagination
            page = 0
            favorites_per_page = 5
            total_pages = (len(prefs.favorite_responses) - 1) // favorites_per_page + 1
            
            text = f"💝 **Избранные ответы** (страница {page + 1}/{total_pages})\n\n"
            
            start_idx = page * favorites_per_page
            end_idx = min(start_idx + favorites_per_page, len(prefs.favorite_responses))
            
            for i, response in enumerate(prefs.favorite_responses[start_idx:end_idx], start_idx + 1):
                text += f"{i}. {response[:100]}{'...' if len(response) > 100 else ''}\n\n"
            
            keyboard = self._create_favorites_keyboard(page, total_pages)
            await self.bot.send_message(user_id, text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in fav command: {str(e)}", exc_info=True)
            await self.bot.send_message(
                message.from_user.id,
                "❌ Ошибка при отображении избранного"
            )
    
    async def handle_stats_command(self, message: types.Message):
        """Handle /stats command to show performance statistics"""
        try:
            user_id = message.from_user.id
            
            # Get user preferences
            prefs = self.response_gen.get_user_preferences(user_id)
            
            # Get performance stats
            perf_stats = self.response_gen.get_performance_stats()
            
            text = f"""📊 **Статистика производительности**

👤 **Ваши настройки:**
🌡️ Откровенность: {prefs.explicitness_level.value}/5
💬 Режим: {prefs.content_mode.value}
🧪 A/B группа: {prefs.ab_test_group}
📈 Ответов: {prefs.total_responses}
⏱️ Среднее время: {prefs.avg_response_time:.2f}с

🤖 **Общая статистика:**"""
            
            if perf_stats:
                text += f"""
📝 Всего ответов: {perf_stats['total_responses']}
📋 Доля шаблонов: {perf_stats['template_ratio']:.1%}
⚡ Среднее время: {perf_stats['avg_generation_time']:.2f}с
🗄️ Кэш: {perf_stats['cache_stats']['size']}/{perf_stats['cache_stats']['max_size']}
💾 Попаданий в кэш: {perf_stats['cache_stats']['total_hits']}"""
            else:
                text += "\n📊 Статистика пока не собрана"
            
            await self.bot.send_message(user_id, text)
            
        except Exception as e:
            logger.error(f"Error in stats command: {str(e)}", exc_info=True)
            await self.bot.send_message(
                message.from_user.id,
                "❌ Ошибка при получении статистики"
            )
    
    async def handle_debug_command(self, message: types.Message):
        """Handle /debug command for advanced users and testing"""
        try:
            user_id = message.from_user.id
            
            # Only allow for specific admin users
            if user_id not in [123456789]:  # Add your admin IDs
                await self.bot.send_message(
                    user_id,
                    "❌ Команда доступна только администраторам"
                )
                return
            
            parts = message.text.split(maxsplit=2)
            
            if len(parts) < 2:
                text = """🔧 **Debug Commands**

Available commands:
- `/debug cache` - Cache statistics  
- `/debug ab_test` - A/B test distribution
- `/debug user [user_id]` - User preferences
- `/debug template [category]` - Template stats
- `/debug reset_user [user_id]` - Reset user data"""
                
                await self.bot.send_message(user_id, text)
                return
            
            command = parts[1].lower()
            
            if command == 'cache':
                cache_stats = self.response_gen.cache.get_stats()
                text = f"""🗄️ **Cache Statistics**

Size: {cache_stats['size']}/{cache_stats['max_size']}
Total hits: {cache_stats['total_hits']}
Average quality: {cache_stats['avg_quality_score']:.2f}

Methods:
{json.dumps(cache_stats['methods'], indent=2)}"""
                
            elif command == 'ab_test':
                perf_stats = self.response_gen.get_performance_stats()
                if 'ab_test_distribution' in perf_stats:
                    text = "🧪 **A/B Test Distribution**\n\n"
                    for group, count in perf_stats['ab_test_distribution'].items():
                        text += f"{group}: {count} users\n"
                else:
                    text = "No A/B test data available"
            
            elif command == 'user' and len(parts) > 2:
                target_user_id = int(parts[2])
                if target_user_id in self.response_gen.user_preferences:
                    prefs = self.response_gen.user_preferences[target_user_id]
                    text = f"👤 **User {target_user_id} Preferences**\n\n"
                    text += f"Explicitness: {prefs.explicitness_level.name}\n"
                    text += f"Mode: {prefs.content_mode.value}\n"
                    text += f"A/B Group: {prefs.ab_test_group}\n"
                    text += f"Responses: {prefs.total_responses}\n"
                    text += f"Favorites: {len(prefs.favorite_responses)}\n"
                else:
                    text = f"User {target_user_id} not found"
            
            else:
                text = "❌ Unknown debug command"
            
            await self.bot.send_message(user_id, text)
            
        except Exception as e:
            logger.error(f"Error in debug command: {str(e)}", exc_info=True)
            await self.bot.send_message(
                message.from_user.id,
                "❌ Ошибка в debug команде"
            )
    
    def _create_heat_keyboard(self) -> types.InlineKeyboardMarkup:
        """Create keyboard for heat level selection"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            types.InlineKeyboardButton("1️⃣ Мягко", callback_data="heat_1"),
            types.InlineKeyboardButton("2️⃣ Флирт", callback_data="heat_2"),
            types.InlineKeyboardButton("3️⃣ Откровенно", callback_data="heat_3"),
            types.InlineKeyboardButton("4️⃣ Страстно", callback_data="heat_4"),
            types.InlineKeyboardButton("5️⃣ Максимум", callback_data="heat_5")
        ]
        
        keyboard.add(*buttons[:2])
        keyboard.add(*buttons[2:4])
        keyboard.add(buttons[4])
        keyboard.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        
        return keyboard
    
    def _create_mode_keyboard(self) -> types.InlineKeyboardMarkup:
        """Create keyboard for mode selection"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        keyboard.add(
            types.InlineKeyboardButton("💬 Chat - Обычное общение", callback_data="mode_chat"),
            types.InlineKeyboardButton("😘 Flirt - Флирт", callback_data="mode_flirt"),
            types.InlineKeyboardButton("🔥 Sexting - Откровенно", callback_data="mode_sexting"),
            types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        )
        
        return keyboard
    
    def _create_favorites_keyboard(self, page: int, total_pages: int) -> types.InlineKeyboardMarkup:
        """Create keyboard for favorites management"""
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        
        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"fav_page_{page-1}"))
        
        nav_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="fav_current"))
        
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"fav_page_{page+1}"))
        
        if len(nav_buttons) > 0:
            keyboard.add(*nav_buttons)
        
        # Action buttons
        keyboard.add(
            types.InlineKeyboardButton("🗑️ Очистить всё", callback_data="fav_clear_all"),
            types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        )
        
        return keyboard
    
    async def handle_heat_callback(self, call: types.CallbackQuery):
        """Handle heat level callback"""
        try:
            level = int(call.data.split('_')[1])
            user_id = call.from_user.id
            
            explicitness_map = {
                1: ExplicitnessLevel.SOFT,
                2: ExplicitnessLevel.MEDIUM,
                3: ExplicitnessLevel.EXPLICIT,
                4: ExplicitnessLevel.INTENSE,
                5: ExplicitnessLevel.EXTREME
            }
            
            new_level = explicitness_map[level]
            await self.response_gen.update_user_preference(
                user_id, 'explicitness_level', new_level
            )
            
            level_names = {
                1: "мягко и романтично 🌸",
                2: "флиртуя с намёками 😘", 
                3: "откровенно и прямо 🔥",
                4: "очень страстно 💋",
                5: "с максимальной откровенностью 🌶️"
            }
            
            text = f"🌡️ Уровень откровенности установлен: **{level}/5**\n"
            text += f"Теперь я буду общаться {level_names[level]}"
            
            await self.bot.edit_message_text(
                text, call.message.chat.id, call.message.message_id
            )
            await self.bot.answer_callback_query(call.id, f"Установлен уровень {level}/5")
            
        except Exception as e:
            logger.error(f"Error in heat callback: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка")
    
    async def handle_mode_callback(self, call: types.CallbackQuery):
        """Handle mode callback"""
        try:
            mode_text = call.data.split('_')[1]
            user_id = call.from_user.id
            
            mode_map = {
                'chat': ContentMode.CHAT,
                'flirt': ContentMode.FLIRT,
                'sexting': ContentMode.SEXTING
            }
            
            new_mode = mode_map[mode_text]
            await self.response_gen.update_user_preference(
                user_id, 'content_mode', new_mode
            )
            
            mode_descriptions = {
                'chat': "обычным общением 💬",
                'flirt': "флиртом и соблазнением 😘",
                'sexting': "откровенной перепиской 🔥"
            }
            
            text = f"💬 Режим изменён на: **{mode_text}**\n"
            text += f"Теперь я буду заниматься {mode_descriptions[mode_text]}"
            
            await self.bot.edit_message_text(
                text, call.message.chat.id, call.message.message_id
            )
            await self.bot.answer_callback_query(call.id, f"Режим: {mode_text}")
            
        except Exception as e:
            logger.error(f"Error in mode callback: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка")
    
    # Callback handler registry
    def get_callback_handlers(self) -> Dict[str, callable]:
        """Get callback handlers for registration"""
        return {
            'heat_': self.handle_heat_callback,
            'mode_': self.handle_mode_callback,
            'fav_': self.handle_favorites_callback,
        }
    
    async def handle_favorites_callback(self, call: types.CallbackQuery):
        """Handle favorites-related callbacks"""
        try:
            action = call.data.split('_', 1)[1]
            user_id = call.from_user.id
            
            if action == 'clear_all':
                prefs = self.response_gen.get_user_preferences(user_id)
                prefs.favorite_responses.clear()
                
                await self.bot.edit_message_text(
                    "💝 Все избранные ответы удалены",
                    call.message.chat.id, 
                    call.message.message_id
                )
                await self.bot.answer_callback_query(call.id, "Избранное очищено")
                
            elif action.startswith('page_'):
                page = int(action.split('_')[1])
                # Re-show favorites with new page
                await self._show_favorites_page(call, page)
                
        except Exception as e:
            logger.error(f"Error in favorites callback: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка")
    
    async def _show_favorites_page(self, call: types.CallbackQuery, page: int):
        """Show specific page of favorites"""
        user_id = call.from_user.id
        prefs = self.response_gen.get_user_preferences(user_id)
        
        favorites_per_page = 5
        total_pages = (len(prefs.favorite_responses) - 1) // favorites_per_page + 1
        
        text = f"💝 **Избранные ответы** (страница {page + 1}/{total_pages})\n\n"
        
        start_idx = page * favorites_per_page
        end_idx = min(start_idx + favorites_per_page, len(prefs.favorite_responses))
        
        for i, response in enumerate(prefs.favorite_responses[start_idx:end_idx], start_idx + 1):
            text += f"{i}. {response[:100]}{'...' if len(response) > 100 else ''}\n\n"
        
        keyboard = self._create_favorites_keyboard(page, total_pages)
        
        await self.bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            reply_markup=keyboard
        )
        await self.bot.answer_callback_query(call.id)

# Export for easy import
enhanced_commands = None

def initialize_enhanced_commands(bot: AsyncTeleBot, state_manager):
    """Initialize enhanced commands with bot and state manager"""
    global enhanced_commands
    enhanced_commands = EnhancedCommandHandlers(bot, state_manager)
    return enhanced_commands 