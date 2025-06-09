"""
Integration Module for Enhanced OF Bot
Combines new adult content system with existing architecture.
Maintains backward compatibility while adding new features.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from telebot.async_telebot import AsyncTeleBot
from telebot import types

# New modules
from adult_templates import ExplicitnessLevel, ContentMode, TemplateCategory
from response_generator import response_generator, GenerationMethod
from enhanced_commands import initialize_enhanced_commands

# New security modules
from src.core.rate_limiter import rate_limit_middleware
from input_validator import input_validator, validate_message

# Existing modules  
from state_manager import StateManager
from utils import get_main_keyboard

logger = logging.getLogger(__name__)

class IntegratedBotManager:
    """Enhanced bot manager with new adult content features"""
    
    def __init__(self, original_bot_manager) -> None:
        """Initialize with existing bot manager for compatibility"""
        self.original_manager = original_bot_manager
        self.bot = original_bot_manager.bot
        self.state_manager = original_bot_manager.state_manager
        self.enhanced_commands = None
        
        # Integration flags
        self.use_new_generation = True  # Feature flag
        self.fallback_to_original = True  # Backward compatibility
        self.enable_rate_limiting = True  # Rate limiting feature
        self.enable_input_validation = True  # Input validation feature
        
    async def initialize_enhanced_features(self) -> bool:
        """Initialize enhanced features on top of existing bot"""
        try:
            # Initialize enhanced commands
            self.enhanced_commands = initialize_enhanced_commands(
                self.bot, self.state_manager
            )
            
            # Register new command handlers
            await self._register_enhanced_handlers()
            
            # Patch existing text handler for new generation
            await self._patch_text_handler()
            
            logger.info("✅ Enhanced OF bot features initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced features: {str(e)}", exc_info=True)
            return False
    
    async def _register_enhanced_handlers(self) -> None:
        """Register new command handlers"""
        
        # Heat level command
        @self.bot.message_handler(commands=['heat'])
        async def heat_handler(message):
            await self._safe_enhanced_handler(
                self.enhanced_commands.handle_heat_command, message
            )
        
        # Mode switching command  
        @self.bot.message_handler(commands=['mode'])
        async def mode_handler(message):
            await self._safe_enhanced_handler(
                self.enhanced_commands.handle_mode_command, message
            )
        
        # Favorites command
        @self.bot.message_handler(commands=['fav'])
        async def fav_handler(message):
            await self._safe_enhanced_handler(
                self.enhanced_commands.handle_fav_command, message
            )
        
        # Statistics command
        @self.bot.message_handler(commands=['stats'])
        async def stats_handler(message):
            await self._safe_enhanced_handler(
                self.enhanced_commands.handle_stats_command, message
            )
        
        # Debug command
        @self.bot.message_handler(commands=['debug'])
        async def debug_handler(message):
            await self._safe_enhanced_handler(
                self.enhanced_commands.handle_debug_command, message
            )
        
        logger.info("✅ Enhanced command handlers registered")
    
    async def _patch_text_handler(self) -> None:
        """Patch existing text handler to use new generation system"""
        
        # Store original handler for fallback
        self.original_text_handler = self.original_manager._handle_text_message
        
        # Replace with enhanced handler
        self.original_manager._handle_text_message = self._enhanced_text_handler
        
        logger.info("✅ Text handler patched for enhanced generation")
    
    async def _enhanced_text_handler(self, message: types.Message) -> None:
        """Enhanced text message handler with new generation system"""
        try:
            user_id = message.from_user.id
            
            # Rate limiting check
            if self.enable_rate_limiting:
                is_allowed, rate_limit_msg = await self._check_rate_limit(user_id)
                if not is_allowed:
                    await self.bot.send_message(user_id, rate_limit_msg)
                    return
            
            # Input validation
            if self.enable_input_validation:
                is_valid, validation_msg = await self._validate_input(message.text)
                if not is_valid:
                    await self.bot.send_message(user_id, validation_msg)
                    return
            
            if not self.use_new_generation:
                # Use original handler if feature disabled
                return await self.original_text_handler(message)
            
            user = self.state_manager.get_user(user_id)
            text = message.text.strip()
            
            # Check for special states that should use original logic
            special_states = [
                'waiting_for_chat_name', 
                'waiting_for_reply_input',
                'in_survey'
            ]
            
            if any(getattr(user, state, False) for state in special_states):
                # Use original handler for special states
                return await self.original_text_handler(message)
            
            # Enhanced generation for regular chat
            await self._handle_enhanced_generation(message, user, text)
            
        except Exception as e:
            logger.error(f"Error in enhanced text handler: {str(e)}", exc_info=True)
            
            # Fallback to original handler
            if self.fallback_to_original:
                await self.original_text_handler(message)
            else:
                await self.bot.send_message(
                    message.from_user.id, 
                    "❌ Произошла ошибка. Попробуйте еще раз."
                )
    
    async def _check_rate_limit(self, user_id: int) -> tuple[bool, str]:
        """Check rate limiting for user"""
        try:
            return await rate_limit_middleware.check_rate_limit(user_id)
        except Exception as e:
            logger.error(f"Rate limit check error for user {user_id}: {e}")
            return True, ""  # Allow on error
    
    async def _validate_input(self, text: str) -> tuple[bool, str]:
        """Validate user input"""
        try:
            is_valid, error_msg, _ = await validate_message(text)
            if not is_valid:
                return False, f"❌ {error_msg}"
            return True, ""
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return True, ""  # Allow on error
    
    async def _handle_enhanced_generation(
        self, 
        message: types.Message, 
        user, 
        text: str
    ) -> None:
        """Handle message with enhanced generation system"""
        
        user_id = message.from_user.id
        
        # Prepare context for generation
        context = {
            'user_id': user_id,
            'user_message': text,
            'user_name': message.from_user.first_name or 'красавчик',
            'chat_id': message.chat.id,
            'model_id': getattr(user, 'selected_model', 'eco'),
            'flirt_style': getattr(user, 'flirt_style', 'игривый'),
            'ppv_style': getattr(user, 'ppv_style', 'провокационный'),
            'amount': '10'  # Default amount for PPV templates
        }
        
        try:
            # Generate response using new system
            response = await response_generator.generate_response(text, context)
            
            # Create enhanced keyboard with new options
            keyboard = self._create_enhanced_keyboard(user)
            
            # Send response with enhanced features
            sent_message = await self.bot.send_message(
                user_id, 
                response, 
                reply_markup=keyboard
            )
            
            # Add reaction buttons for feedback
            await self._add_feedback_buttons(sent_message, response)
            
        except Exception as e:
            logger.error(f"Enhanced generation failed: {str(e)}", exc_info=True)
            
            # Fallback to original system
            if self.fallback_to_original:
                await self.original_text_handler(message)
    
    def _create_enhanced_keyboard(self, user) -> types.InlineKeyboardMarkup:
        """Create enhanced keyboard with new options"""
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Keep original functionality
        keyboard.add(
            types.InlineKeyboardButton("💬 Продолжить", callback_data="continue_writing"),
            types.InlineKeyboardButton("😘 Флирт", callback_data="add_flirt")
        )
        
        keyboard.add(
            types.InlineKeyboardButton("💰 PPV предложение", callback_data="quick_ppv"),
            types.InlineKeyboardButton("🎁 Чаевые", callback_data="quick_tips")
        )
        
        # New enhanced options
        keyboard.add(
            types.InlineKeyboardButton(
                "🌡️ Настроить уровень", 
                callback_data="heat_settings"
            ),
            types.InlineKeyboardButton(
                "💬 Сменить режим", 
                callback_data="mode_settings"
            )
        )
        
        keyboard.add(
            types.InlineKeyboardButton(
                "📊 Чаты", 
                callback_data="chat_management"
            ),
            types.InlineKeyboardButton(
                "🏠 Главное меню", 
                callback_data="main_menu"
            )
        )
        
        return keyboard
    
    async def _add_feedback_buttons(
        self, 
        sent_message: types.Message, 
        response: str
    ) -> None:
        """Add feedback buttons to response for quality tracking"""
        
        feedback_keyboard = types.InlineKeyboardMarkup(row_width=5)
        
        # Star rating buttons
        star_buttons = [
            types.InlineKeyboardButton(
                f"{i}⭐", 
                callback_data=f"rate_{i}_{sent_message.message_id}"
            )
            for i in range(1, 6)
        ]
        feedback_keyboard.add(*star_buttons)
        
        # Additional feedback options
        feedback_keyboard.add(
            types.InlineKeyboardButton(
                "💝 В избранное", 
                callback_data=f"fav_add_{sent_message.message_id}"
            ),
            types.InlineKeyboardButton(
                "🔄 Другой ответ", 
                callback_data=f"regenerate_{sent_message.message_id}"
            )
        )
        
        # Edit message to add feedback buttons
        try:
            await self.bot.edit_message_reply_markup(
                sent_message.chat.id,
                sent_message.message_id,
                reply_markup=feedback_keyboard
            )
        except Exception as e:
            logger.debug(f"Could not add feedback buttons: {str(e)}")
    
    async def _handle_enhanced_callbacks(self, call: types.CallbackQuery) -> bool:
        """Handle enhanced callback queries"""
        
        data = call.data
        user_id = call.from_user.id
        
        try:
            # Rate limiting for callbacks
            if self.enable_rate_limiting:
                is_allowed, rate_limit_msg = await self._check_rate_limit(user_id)
                if not is_allowed:
                    await self.bot.answer_callback_query(call.id, rate_limit_msg)
                    return True
            
            # Enhanced settings callbacks
            if data == "heat_settings":
                await self.enhanced_commands.handle_heat_command(
                    self._create_mock_message(call)
                )
                await self.bot.answer_callback_query(call.id)
                
            elif data == "mode_settings":
                await self.enhanced_commands.handle_mode_command(
                    self._create_mock_message(call)
                )
                await self.bot.answer_callback_query(call.id)
            
            # Rating callbacks
            elif data.startswith("rate_"):
                await self._handle_rating_callback(call)
            
            # Favorite callbacks
            elif data.startswith("fav_add_"):
                await self._handle_favorite_callback(call)
            
            # Regenerate callbacks  
            elif data.startswith("regenerate_"):
                await self._handle_regenerate_callback(call)
                
            # Enhanced command callbacks
            elif any(data.startswith(prefix) for prefix in ['heat_', 'mode_', 'fav_']):
                handlers = self.enhanced_commands.get_callback_handlers()
                
                for prefix, handler in handlers.items():
                    if data.startswith(prefix):
                        await handler(call)
                        break
            
            else:
                # Let original handler deal with it
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error in enhanced callback: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка")
            return True
    
    def _create_mock_message(self, call: types.CallbackQuery) -> types.Message:
        """Create mock message for command handlers"""
        return types.Message(
            message_id=0,
            from_user=call.from_user,
            date=0,
            chat=call.message.chat,
            content_type='text',
            options={},
            json_string=""
        )
    
    async def _handle_rating_callback(self, call: types.CallbackQuery) -> None:
        """Handle rating callback"""
        try:
            parts = call.data.split('_')
            rating = int(parts[1])
            message_id = parts[2]
            
            # Find the response in metrics and rate it
            user_id = call.from_user.id
            prefs = response_generator.get_user_preferences(user_id)
            
            if rating >= 4:
                prefs.positive_feedback += 1
            
            await self.bot.answer_callback_query(
                call.id, 
                f"Спасибо за оценку: {rating}⭐"
            )
            
            # Remove feedback buttons
            await self.bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
            
        except Exception as e:
            logger.error(f"Error in rating callback: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка оценки")
    
    async def _handle_favorite_callback(self, call: types.CallbackQuery) -> None:
        """Handle add to favorites callback"""
        try:
            user_id = call.from_user.id
            
            # Get message text to save as favorite
            message_text = call.message.text
            if message_text:
                await response_generator.save_favorite_response(
                    user_id, 
                    message_text
                )
                
                await self.bot.answer_callback_query(
                    call.id, 
                    "💝 Добавлено в избранное!"
                )
            else:
                await self.bot.answer_callback_query(
                    call.id, 
                    "❌ Не удалось сохранить"
                )
                
        except Exception as e:
            logger.error(f"Error in favorite callback: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка")
    
    async def _handle_regenerate_callback(self, call: types.CallbackQuery) -> None:
        """Handle regenerate response callback"""
        try:
            user_id = call.from_user.id
            
            # This would need access to original message to regenerate
            await self.bot.answer_callback_query(
                call.id, 
                "🔄 Генерирую новый ответ..."
            )
            
            # Simple regeneration (in real implementation, would need context)
            context = {
                'user_id': user_id,
                'user_message': 'Привет',  # Placeholder
                'user_name': call.from_user.first_name or 'красавчик'
            }
            
            new_response = await response_generator.generate_response(
                "Привет", 
                context
            )
            
            await self.bot.send_message(
                user_id,
                f"🔄 Новый вариант:\n\n{new_response}"
            )
            
        except Exception as e:
            logger.error(f"Error in regenerate callback: {str(e)}", exc_info=True)
            await self.bot.answer_callback_query(call.id, "❌ Ошибка генерации")
    
    async def _safe_enhanced_handler(
        self, 
        handler_func, 
        *args, 
        **kwargs
    ) -> None:
        """Safe execution of enhanced handlers with fallback"""
        try:
            await handler_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in enhanced handler {handler_func.__name__}: {str(e)}", exc_info=True)
            
            # Try to send error message to user
            try:
                if args and hasattr(args[0], 'from_user'):
                    await self.bot.send_message(
                        args[0].from_user.id,
                        "❌ Произошла ошибка. Попробуйте позже."
                    )
            except:
                pass
    
    def patch_original_callback_handler(self) -> None:
        """Patch original callback handler to include enhanced callbacks"""
        
        original_callback_handler = self.original_manager._handle_callback_query
        
        async def enhanced_callback_handler(call: types.CallbackQuery):
            # Try enhanced callbacks first
            handled = await self._handle_enhanced_callbacks(call)
            
            if not handled:
                # Fall back to original handler
                await original_callback_handler(call)
        
        # Replace the original handler
        self.original_manager._handle_callback_query = enhanced_callback_handler
        
        logger.info("✅ Callback handler patched for enhanced features")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        original_status = {
            'bot_running': self.original_manager.is_running,
            'state_manager': self.state_manager is not None,
            'chat_handlers': self.original_manager.chat_handlers is not None
        }
        
        enhanced_status = {
            'enhanced_features': self.enhanced_commands is not None,
            'response_generator': response_generator is not None,
            'template_repo_size': len(
                response_generator.template_repo.templates
            ),
            'cache_size': response_generator.cache.get_stats()['size'],
            'active_users': len(response_generator.user_preferences),
            'rate_limiting': self.enable_rate_limiting,
            'input_validation': self.enable_input_validation
        }
        
        performance_stats = response_generator.get_performance_stats()
        
        return {
            'original': original_status,
            'enhanced': enhanced_status,
            'performance': performance_stats,
            'timestamp': asyncio.get_event_loop().time()
        }

async def integrate_enhanced_features(original_bot_manager) -> Optional[IntegratedBotManager]:
    """Main integration function"""
    
    logger.info("🚀 Starting OF bot enhancement integration...")
    
    # Create integrated manager
    integrated_manager = IntegratedBotManager(original_bot_manager)
    
    # Initialize enhanced features
    success = await integrated_manager.initialize_enhanced_features()
    
    if not success:
        logger.error("❌ Failed to initialize enhanced features")
        return None
    
    # Patch callback handler
    integrated_manager.patch_original_callback_handler()
    
    # Get system status
    status = await integrated_manager.get_system_status()
    
    logger.info("✅ OF bot enhancement integration completed successfully")
    logger.info(f"📊 System status: {status['enhanced']}")
    
    return integrated_manager 