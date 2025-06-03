"""
Monetized OF Bot - Revenue Focused Implementation
Integrates premium system, caching, adult templates, and Telegram Stars/TON payments
ENHANCED WITH STUNNING UI AND FULL CALLBACK HANDLING
"""

import telebot
import os
import random
from datetime import datetime
from typing import Optional
import time

# Import our monetization modules
from premium_system import premium_manager, SubscriptionTier
from adult_templates import template_manager, ExplicitnessLevel, ContentMode
from response_cache import response_cache, CacheType
from telegram_payment_system import setup_telegram_payment_system

# Импорт и настройка админ команд
from admin_commands import setup_admin_commands

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
GROQ_KEY = os.getenv('GROQ_KEY', 'YOUR_GROQ_KEY_HERE')

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

class MonetizedBot:
    def __init__(self):
        self.bot = bot
        self.payment_handler = setup_telegram_payment_system(bot)
        
        # Revenue optimization settings
        self.template_usage_ratio = 0.85  # 85% templates, 15% AI for cost reduction
        self.conversion_trigger_threshold = 0.8  # Trigger upsells at 80% message limit
        
        # Настройка админ команд
        self.admin_handler = setup_admin_commands(self.bot)
        print("✅ Admin commands initialized")
        
        # Setup handlers
        self.setup_handlers()
        
        # Optimize cache for cost reduction
        response_cache.optimize_for_cost_reduction()

    def setup_handlers(self):
        """Setup all bot command and message handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            self.handle_start_command(message)
        
        @self.bot.message_handler(commands=['status'])
        def handle_status(message):
            self.handle_status_command(message)
        
        @self.bot.message_handler(commands=['menu'])
        def handle_menu(message):
            self.show_main_menu(message)
        
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            self.show_help_menu(message)
        
        @self.bot.message_handler(commands=['cache_stats'])
        def handle_cache_stats(message):
            if self.payment_handler.is_admin(message.from_user.id):
                self.show_cache_statistics(message)
        
        # 🔥 ПОЛНАЯ ОБРАБОТКА CALLBACK QUERIES
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_all_callbacks(call):
            self.handle_callback_query(call)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            self.handle_user_message(message)

    def handle_callback_query(self, call):
        """🔥 ПОЛНЫЙ ОБРАБОТЧИК ВСЕХ CALLBACK QUERIES"""
        try:
            # Всегда отвечаем на callback query
            self.bot.answer_callback_query(call.id)
            
            data = call.data
            
            # =============== PAYMENT & UPGRADE HANDLERS ===============
            if data == "payment_upgrade":
                self.show_payment_options(call.message)
            elif data == "payment_pricing":
                self.show_detailed_pricing(call.message)
            elif data == "show_status":
                self.show_user_status_detailed(call.message)
            elif data.startswith("payment_"):
                self.payment_handler.process_payment_callback(call)
            
            # =============== MAIN MENU HANDLERS ===============
            elif data == "main_menu":
                self.show_main_menu(call.message)
            elif data == "user_profile":
                self.show_user_profile(call.message)
            elif data == "premium_benefits":
                self.show_premium_benefits(call.message)
            elif data == "help_support":
                self.show_help_menu(call.message)
            elif data == "settings":
                self.show_settings_menu(call.message)
            
            # =============== CHAT & INTERACTION HANDLERS ===============
            elif data == "start_chatting":
                self.handle_start_chatting(call.message)
            elif data == "content_menu":
                self.show_content_menu(call.message)
            elif data == "flirt_mode":
                self.activate_flirt_mode(call.message)
            elif data == "role_play":
                self.show_roleplay_menu(call.message)
            elif data == "sexy_chat":
                self.activate_sexy_chat(call.message)
            elif data == "custom_request":
                self.show_custom_request_menu(call.message)
            
            # =============== ROLEPLAY HANDLERS ===============
            elif data.startswith("roleplay_"):
                roleplay_type = data.replace("roleplay_", "")
                self.handle_roleplay_callbacks(call, roleplay_type)
            
            # =============== SETTINGS HANDLERS ===============
            elif data.startswith("explicitness_"):
                level = data.replace("explicitness_", "")
                self.set_explicitness_level(call.message, level)
            elif data.startswith("language_"):
                lang = data.replace("language_", "")
                self.set_language(call.message, lang)
            
            # =============== ADMIN HANDLERS ===============
            elif data.startswith("admin_"):
                if self.payment_handler.is_admin(call.from_user.id):
                    self.handle_admin_callback(call)
                else:
                    self.bot.edit_message_text("❌ Доступ запрещен", call.message.chat.id, call.message.message_id)
            
            # =============== EASTER EGGS & FUN ===============
            elif data == "surprise_me":
                self.surprise_user(call.message)
            elif data == "daily_bonus":
                self.claim_daily_bonus(call.message)
            elif data == "share_bot":
                self.share_bot_menu(call.message)
            
            else:
                # Неизвестный callback
                self.bot.edit_message_text(
                    "🤔 Неизвестная команда. Возвращаемся в главное меню...",
                    call.message.chat.id, 
                    call.message.message_id,
                    reply_markup=self.create_main_menu_keyboard()
                )
                
        except Exception as e:
            print(f"Callback error: {e}")
            try:
                self.bot.send_message(call.message.chat.id, "⚠️ Произошла ошибка. Попробуйте еще раз.")
            except:
                pass

    def handle_start_command(self, message):
        """🔥 НЕВЕРОЯТНЫЙ СТАРТОВЫЙ ЭКРАН"""
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "красавчик"
        
        # Get or create user subscription (automatic free trial)
        user_sub = premium_manager.get_user_subscription(user_id)
        
        # 🎭 Анимированное приветствие
        welcome_animation = [
            "🌟", "✨", "💫", "⭐", "🌟", "✨", "💎"
        ]
        
        animation_msg = self.bot.send_message(message.chat.id, "🌟 Загружаем магию...")
        
        for emoji in welcome_animation:
            time.sleep(0.3)
            try:
                self.bot.edit_message_text(f"{emoji} Создаем незабываемый опыт...", 
                                         message.chat.id, animation_msg.message_id)
            except:
                pass
        
        # Финальное приветственное сообщение
        welcome_msg = f"""
🔥✨ **ДОБРО ПОЖАЛОВАТЬ В PREMIUM PARADISE** ✨🔥

Привет, {user_name}! 😘💋

🎁 **ТВОЙ БЕСПЛАТНЫЙ СТАРТ:**
┌─ 🆓 50 сообщений БЕСПЛАТНО
├─ 📅 7 дней полного доступа  
├─ 🔞 Эксклюзивный контент
└─ 💎 Премиум опыт

🌈 **БЕЗГРАНИЧНЫЕ ВОЗМОЖНОСТИ:**
⭐ **PREMIUM** • 500 сообщений • Откровенный контент • ⭐150 Stars
💎 **VIP** • 2000 сообщений • Фетиш контент • Приоритет • ⭐250 Stars  
👑 **ULTIMATE** • 10,000 сообщений • Экстремальный контент • VIP доступ • ⭐500 Stars

🎯 **ЧТО ТЕБЯ ЖДЕТ:**
• 🔥 Неограниченное откровенное общение
• 🎭 Кастомные ролевые сценарии
• 💋 Персональные фантазии
• 💎 Премиум фетиш контент
• 🌟 Доступ ко мне 24/7

💳 **МГНОВЕННАЯ ОПЛАТА:**
⭐ Telegram Stars (1 клик!)
💎 TON криптовалюта (+5% бонус!)

Готов к незабываемому приключению? 😈💕
        """
        
        markup = self.create_start_menu_keyboard()
        
        self.bot.edit_message_text(welcome_msg, message.chat.id, animation_msg.message_id, 
                                 reply_markup=markup, parse_mode='Markdown')

    def create_start_menu_keyboard(self):
        """🎨 Создает красивую стартовую клавиатуру"""
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        # Главные действия (большие кнопки)
        markup.add(
            telebot.types.InlineKeyboardButton("🚀 НАЧАТЬ ЧАТ", callback_data="start_chatting"),
            telebot.types.InlineKeyboardButton("💎 АПГРЕЙД", callback_data="payment_upgrade")
        )
        
        # Информационные кнопки
        markup.add(
            telebot.types.InlineKeyboardButton("📊 Мой статус", callback_data="show_status"),
            telebot.types.InlineKeyboardButton("💰 Цены", callback_data="payment_pricing")
        )
        
        # Меню навигации
        markup.add(
            telebot.types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
            telebot.types.InlineKeyboardButton("❓ Помощь", callback_data="help_support")
        )
        
        return markup

    def create_main_menu_keyboard(self):
        """🎨 Создает главное меню с потрясающим дизайном"""
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        # Основные функции
        markup.add(
            telebot.types.InlineKeyboardButton("💬 Общение", callback_data="start_chatting"),
            telebot.types.InlineKeyboardButton("🔞 Контент", callback_data="content_menu")
        )
        
        markup.add(
            telebot.types.InlineKeyboardButton("💎 Апгрейд", callback_data="payment_upgrade"),
            telebot.types.InlineKeyboardButton("👤 Профиль", callback_data="user_profile")
        )
        
        # Дополнительные возможности
        markup.add(
            telebot.types.InlineKeyboardButton("🎭 Ролевые игры", callback_data="role_play"),
            telebot.types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
        )
        
        # Специальные возможности
        markup.add(
            telebot.types.InlineKeyboardButton("🎁 Сюрприз", callback_data="surprise_me"),
            telebot.types.InlineKeyboardButton("🎯 Дневной бонус", callback_data="daily_bonus")
        )
        
        # Помощь и поддержка
        markup.add(
            telebot.types.InlineKeyboardButton("❓ Помощь", callback_data="help_support"),
            telebot.types.InlineKeyboardButton("📢 Поделиться", callback_data="share_bot")
        )
        
        return markup

    def show_main_menu(self, message):
        """🏠 Показывает главное меню"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        tier_emoji = {
            SubscriptionTier.FREE_TRIAL: "🆓",
            SubscriptionTier.PREMIUM: "⭐",
            SubscriptionTier.VIP: "💎", 
            SubscriptionTier.ULTIMATE: "👑"
        }
        
        menu_msg = f"""
🏠 **ГЛАВНОЕ МЕНЮ** 🏠

{tier_emoji[user_sub.tier]} **Статус:** {user_sub.tier.value.replace('_', ' ').title()}
💬 **Сообщений осталось:** {user_sub.messages_limit - user_sub.messages_used:,}
📅 **Активно до:** {user_sub.subscription_end.strftime('%d.%m.%Y')}

🌟 **Выберите действие:**
        """
        
        markup = self.create_main_menu_keyboard()
        
        if hasattr(message, 'message_id'):
            # Если это callback query
            self.bot.edit_message_text(menu_msg, message.chat.id, message.message_id, 
                                     reply_markup=markup, parse_mode='Markdown')
        else:
            # Если это обычное сообщение
            self.bot.send_message(message.chat.id, menu_msg, 
                                reply_markup=markup, parse_mode='Markdown')

    def show_content_menu(self, message):
        """🔞 Показывает меню контента"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        if user_sub.tier == SubscriptionTier.FREE_TRIAL:
            markup.add(
                telebot.types.InlineKeyboardButton("😘 Легкий флирт", callback_data="flirt_mode"),
                telebot.types.InlineKeyboardButton("🔒 Премиум (апгрейд)", callback_data="payment_upgrade")
            )
        else:
            markup.add(
                telebot.types.InlineKeyboardButton("😘 Флирт", callback_data="flirt_mode"),
                telebot.types.InlineKeyboardButton("🔥 Секси чат", callback_data="sexy_chat")
            )
            
            if user_sub.tier in [SubscriptionTier.VIP, SubscriptionTier.ULTIMATE]:
                markup.add(
                    telebot.types.InlineKeyboardButton("🎭 Ролевые игры", callback_data="role_play"),
                    telebot.types.InlineKeyboardButton("💎 VIP контент", callback_data="vip_content")
                )
            
            if user_sub.tier == SubscriptionTier.ULTIMATE:
                markup.add(
                    telebot.types.InlineKeyboardButton("👑 Экстрим", callback_data="extreme_content"),
                    telebot.types.InlineKeyboardButton("🎯 Кастом", callback_data="custom_request")
                )
        
        markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        content_msg = f"""
🔞 **КОНТЕНТ МЕНЮ** 🔞

🎯 **Доступный контент для {user_sub.tier.value.replace('_', ' ').title()}:**

{self.get_content_description(user_sub.tier)}

💡 **Выберите тип контента:**
        """
        
        self.bot.edit_message_text(content_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def get_content_description(self, tier):
        """Получает описание доступного контента"""
        descriptions = {
            SubscriptionTier.FREE_TRIAL: """
🆓 **FREE TRIAL:**
• Легкий флирт и общение
• Базовые ролевые сценарии
• Ограниченный доступ к контенту
            """,
            SubscriptionTier.PREMIUM: """
⭐ **PREMIUM:**
• Откровенные диалоги
• Сексуальные фантазии
• Эротические ролевые игры
• Персональные просьбы
            """,
            SubscriptionTier.VIP: """
💎 **VIP:**
• Все возможности Premium
• Фетиш контент
• Эксклюзивные сценарии
• Приоритетная поддержка
• Кастомные запросы
            """,
            SubscriptionTier.ULTIMATE: """
👑 **ULTIMATE:**
• Все возможности VIP
• Экстремальный контент
• Безграничные фантазии
• Персональное внимание 24/7
• Эксклюзивные материалы
            """
        }
        return descriptions.get(tier, "Описание недоступно")

    def show_user_status_detailed(self, message):
        """📊 Детальный статус пользователя"""
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        status_msg = premium_manager.get_user_status_message(user_id)
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💎 Апгрейд", callback_data="payment_upgrade"),
            telebot.types.InlineKeyboardButton("🔄 Обновить", callback_data="show_status")
        )
        markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        self.bot.edit_message_text(status_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_help_menu(self, message):
        """❓ Меню помощи"""
        help_msg = """
❓ **ПОМОЩЬ И ПОДДЕРЖКА** ❓

🔸 **Как начать:**
1. Выберите "Начать чат" в главном меню
2. Пишите мне что угодно
3. Наслаждайтесь общением!

🔸 **Тарифы:**
• 🆓 Free Trial: 50 сообщений, 7 дней
• ⭐ Premium: 500 сообщений + откровенный контент
• 💎 VIP: 2000 сообщений + фетиш + приоритет
• 👑 Ultimate: 10000 сообщений + экстрим + VIP

🔸 **Оплата:**
• ⭐ Telegram Stars - мгновенно
• 💎 TON криптовалюта - с бонусом

🔸 **Команды:**
/start - Перезапуск бота
/menu - Главное меню
/status - Ваш статус
/help - Эта справка

🔸 **Поддержка:**
При проблемах пишите администратору
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💰 Цены", callback_data="payment_pricing"),
            telebot.types.InlineKeyboardButton("📊 Статус", callback_data="show_status")
        )
        markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        if hasattr(message, 'message_id'):
            self.bot.edit_message_text(help_msg, message.chat.id, message.message_id,
                                     reply_markup=markup, parse_mode='Markdown')
        else:
            self.bot.send_message(message.chat.id, help_msg,
                                reply_markup=markup, parse_mode='Markdown')

    def surprise_user(self, message):
        """🎁 Сюрприз для пользователя"""
        surprises = [
            ("🎁 Бонусное сообщение!", "Получите 1 дополнительное сообщение БЕСПЛАТНО!"),
            ("🌟 Эксклюзивный контент!", "Специальный контент только для вас!"),
            ("💎 VIP момент!", "Попробуйте VIP контент прямо сейчас!"),
            ("🔥 Горячий сюрприз!", "Особенно откровенное сообщение для вас!"),
            ("💋 Персональное внимание!", "Индивидуальное сообщение только для вас!")
        ]
        
        surprise_title, surprise_content = random.choice(surprises)
        
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        if user_sub.messages_used < user_sub.messages_limit:
            # Дарим бонусное сообщение
            premium_manager.use_message(message.from_user.id)
            
            surprise_msg = f"""
🎉 **{surprise_title}** 🎉

{surprise_content}

🎁 **Ваш персональный сюрприз:**
{template_manager.get_template(
    self.determine_explicitness_level(user_sub.tier),
    ContentMode.FLIRT,
    user_sub.tier != SubscriptionTier.FREE_TRIAL
)}

💝 Сюрприз использовал 1 сообщение из вашего лимита
            """
        else:
            surprise_msg = f"""
🎁 **СЮРПРИЗ ДЛЯ ВАС!** 🎁

{surprise_content}

⚠️ У вас закончились сообщения, но сюрприз всё равно для вас!
💎 Апгрейдитесь для большего количества сюрпризов!
            """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🎁 Еще сюрприз!", callback_data="surprise_me"),
            telebot.types.InlineKeyboardButton("💎 Апгрейд", callback_data="payment_upgrade")
        )
        markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        self.bot.edit_message_text(surprise_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def handle_user_message(self, message):
        """Handle user messages with premium system integration"""
        user_id = message.from_user.id
        user_input = message.text
        
        # Check if user can send messages
        can_send, reason = premium_manager.can_send_message(user_id)
        
        if not can_send:
            self.handle_message_limit_reached(message, reason)
            return
        
        # Use message from quota
        premium_manager.use_message(user_id)
        
        # Generate response with cost optimization
        response = self.generate_optimized_response(message)
        
        # Check if we should trigger conversion
        self.check_conversion_trigger(message)
        
        # Send response
        self.bot.reply_to(message, response, parse_mode='Markdown')

    def generate_optimized_response(self, message) -> str:
        """Generate response using cache and templates for cost optimization"""
        user_id = message.from_user.id
        user_input = message.text
        user_sub = premium_manager.get_user_subscription(user_id)
        
        # Determine content settings
        explicitness_level = self.determine_explicitness_level(user_sub.tier)
        content_mode = self.determine_content_mode(user_input)
        
        # Try cache first (80% cost reduction target)
        cached_response = response_cache.get_cached_response(
            user_input, 
            user_sub.tier.value,
            explicitness_level.value,
            content_mode.value
        )
        
        if cached_response:
            return cached_response
        
        # Use template-based response (85% of the time for cost optimization)
        if random.random() < self.template_usage_ratio:
            response = self.generate_template_response(user_sub, explicitness_level, content_mode, user_input)
            cache_type = CacheType.TEMPLATE
        else:
            # Use AI response (15% of the time)
            response = self.generate_ai_response(user_input, user_sub, explicitness_level)
            cache_type = CacheType.AI_RESPONSE
        
        # Cache the response for future use
        response_cache.cache_response(
            user_input,
            response,
            user_sub.tier.value,
            explicitness_level.value,
            content_mode.value,
            cache_type
        )
        
        return response

    def generate_template_response(self, user_sub, explicitness_level, content_mode, user_input) -> str:
        """Generate template-based response"""
        is_premium = user_sub.tier != SubscriptionTier.FREE_TRIAL
        
        # Check if approaching limit for conversion trigger
        usage_ratio = user_sub.messages_used / user_sub.messages_limit
        force_conversion = usage_ratio >= self.conversion_trigger_threshold
        
        return template_manager.get_template(
            explicitness_level, 
            content_mode, 
            is_premium, 
            force_conversion
        )

    def generate_ai_response(self, user_input: str, user_sub, explicitness_level) -> str:
        """Generate AI response (fallback when templates aren't enough)"""
        # This would integrate with Groq API or other AI service
        # For now, return a template-based fallback to save costs
        return template_manager.get_template(
            explicitness_level,
            ContentMode.CHAT,
            user_sub.tier != SubscriptionTier.FREE_TRIAL
        )

    def determine_explicitness_level(self, tier: SubscriptionTier) -> ExplicitnessLevel:
        """Determine content explicitness based on user tier"""
        if tier == SubscriptionTier.FREE_TRIAL:
            return ExplicitnessLevel.SOFT
        elif tier == SubscriptionTier.PREMIUM:
            return ExplicitnessLevel.MEDIUM
        elif tier == SubscriptionTier.VIP:
            return ExplicitnessLevel.EXPLICIT
        elif tier == SubscriptionTier.ULTIMATE:
            return ExplicitnessLevel.EXTREME
        else:
            return ExplicitnessLevel.SOFT

    def determine_content_mode(self, user_input: str) -> ContentMode:
        """Determine content mode based on user input"""
        user_input_lower = user_input.lower()
        
        # Sexual keywords trigger sexting mode
        sexual_keywords = ['fuck', 'sex', 'pussy', 'cock', 'cum', 'horny', 'wet', 'hard', 'трахать', 'секс', 'киска', 'член', 'кончать', 'возбужден']
        if any(keyword in user_input_lower for keyword in sexual_keywords):
            return ContentMode.SEXTING
        
        # Flirty keywords trigger flirt mode
        flirt_keywords = ['sexy', 'beautiful', 'hot', 'want', 'desire', 'love', 'сексуальная', 'красивая', 'горячая', 'хочу', 'желание', 'люблю']
        if any(keyword in user_input_lower for keyword in flirt_keywords):
            return ContentMode.FLIRT
        
        return ContentMode.CHAT

    def handle_message_limit_reached(self, message, reason: str):
        """Handle when user reaches message limit"""
        if reason == "message_limit_reached":
            limit_msg = """
🚫 **ЛИМИТ СООБЩЕНИЙ ДОСТИГНУТ** 🚫

Вы использовали все сообщения за этот период! 

🔥 **АПГРЕЙД СЕЙЧАС ДЛЯ БЕЗЛИМИТНОГО ДОСТУПА:**
⭐ PREMIUM: 500 сообщений (⭐150 Stars)
💎 VIP: 2000 сообщений (⭐250 Stars)
👑 ULTIMATE: 10,000 сообщений (⭐500 Stars)

💳 **МГНОВЕННАЯ АКТИВАЦИЯ:**
⭐ Telegram Stars: Оплата в приложении
💎 TON криптовалюта: +5% бонус контента
🔐 Активация в течение 5 минут!

Не упускай наш горячий контент! 🔥
            """
        else:  # subscription_expired
            limit_msg = """
⏰ **ПОДПИСКА ИСТЕКЛА** ⏰

Ваш премиум доступ закончился! 

🎁 **ПРОДЛИТЬ СЕЙЧАС:**
• Получите скидку 20% на следующую подписку
• Мгновенная реактивация
• Сохраните все ваши предпочтения

💎 **СПЕЦИАЛЬНЫЕ ПРЕДЛОЖЕНИЯ НА ПРОДЛЕНИЕ:**
• Недельные планы: СКИДКА 30%
• Месячные планы: СКИДКА 50%
• TON платежи: Дополнительные 5% бонуса

Готов продолжить развлечения? 😈
            """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💰 АПГРЕЙД СЕЙЧАС", callback_data="payment_upgrade"),
            telebot.types.InlineKeyboardButton("🔥 Посмотреть цены", callback_data="payment_pricing")
        )
        
        self.bot.send_message(message.chat.id, limit_msg, reply_markup=markup, parse_mode='Markdown')

    def check_conversion_trigger(self, message):
        """Check if we should trigger conversion messaging"""
        user_id = message.from_user.id
        user_sub = premium_manager.get_user_subscription(user_id)
        
        usage_ratio = user_sub.messages_used / user_sub.messages_limit
        
        # Trigger at 50%, 80%, and 95% usage
        if usage_ratio >= 0.95:
            conversion_msg = "🚨 ПОСЛЕДНИЕ 5% СООБЩЕНИЙ! Апгрейд СЕЙЧАС: /payment 🚨"
        elif usage_ratio >= 0.80:
            conversion_msg = "⚠️ 80% сообщений использовано! Не дай себе заблокироваться - апгрейд: /payment 💎"
        elif usage_ratio >= 0.50:
            conversion_msg = "📊 Половина сообщений использована! Апгрейд для безлимитного доступа: /payment ⭐"
        else:
            return
        
        # Send conversion message
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💰 АПГРЕЙД", callback_data="payment_upgrade"))
        
        self.bot.send_message(message.chat.id, conversion_msg, reply_markup=markup)

    def show_cache_statistics(self, message):
        """Show cache statistics for admin"""
        stats = response_cache.get_cache_stats()
        
        stats_msg = f"""
📊 **CACHE PERFORMANCE** 📊

💾 **CACHE STATS:**
• Total Entries: {stats['total_cache_entries']}
• Hit Rate: {stats['cache_hit_rate']}
• Total Requests: {stats['total_requests']}
• API Calls Saved: {stats['api_calls_saved']}

💰 **COST SAVINGS:**
• Total Saved: {stats['cost_saved_usd']}
• Monthly Projection: {stats['estimated_monthly_savings']}
• Efficiency: {stats['cache_efficiency']}

📈 **CACHE DISTRIBUTION:**
{self.format_distribution(stats['cache_distribution'])}

🎯 **TIER DISTRIBUTION:**
{self.format_distribution(stats['tier_distribution'])}
        """
        
        self.bot.send_message(message.chat.id, stats_msg, parse_mode='Markdown')

    def format_distribution(self, distribution: dict) -> str:
        """Format distribution data for display"""
        if not distribution:
            return "No data available"
        
        lines = []
        for key, value in distribution.items():
            lines.append(f"• {key}: {value}")
        
        return "\n".join(lines)

    def run(self):
        """Start the monetized bot"""
        print("🔥 Monetized OF Bot starting...")
        print("💰 Premium system: ACTIVE")
        print("⭐ Telegram Stars payment: INTEGRATED")
        print("💎 TON cryptocurrency: SUPPORTED")
        print("💾 Response caching: OPTIMIZED for 80% cost reduction")
        print("🔞 Adult templates: LOADED")
        print("💳 Payment system: READY")
        
        try:
            self.bot.polling(none_stop=True)
        except Exception as e:
            print(f"Bot error: {e}")
            # Restart bot automatically
            self.run()

    def handle_status_command(self, message):
        """Show user status and upsell opportunities"""
        user_id = message.from_user.id
        status_msg = premium_manager.get_user_status_message(user_id)
        
        # Add upsell if appropriate
        user_sub = premium_manager.get_user_subscription(user_id)
        if user_sub.tier != SubscriptionTier.ULTIMATE:
            upsell_msg = template_manager.get_upsell_message(user_sub.tier.value)
            status_msg += f"\n\n{upsell_msg}"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💰 Апгрейд", callback_data="payment_upgrade"),
            telebot.types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        )
        
        self.bot.send_message(message.chat.id, status_msg, reply_markup=markup, parse_mode='Markdown')

    def show_payment_options(self, message):
        """💰 Показывает опции оплаты с красивым дизайном"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        payment_msg = f"""
💎 **ПРЕМИУМ АПГРЕЙД** 💎

🔥 **ТЕКУЩИЙ СТАТУС:** {user_sub.tier.value.replace('_', ' ').title()}
💬 **Осталось сообщений:** {user_sub.messages_limit - user_sub.messages_used:,}

🌟 **ВЫБЕРИТЕ ВАШ ПЛАН:**

⭐ **PREMIUM** - ⭐150 Stars
• 500 сообщений
• Откровенный контент
• Эротические диалоги

💎 **VIP** - ⭐250 Stars  
• 2000 сообщений
• Фетиш контент
• Приоритетная поддержка
• Эксклюзивные сценарии

👑 **ULTIMATE** - ⭐500 Stars
• 10,000 сообщений
• Экстремальный контент
• Персональное внимание 24/7
• Безграничные фантазии

💳 **СПОСОБЫ ОПЛАТЫ:**
⭐ Telegram Stars (мгновенно)
💎 TON криптовалюта (+5% бонус)
        """
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        
        # Кнопки тарифов
        if user_sub.tier != SubscriptionTier.PREMIUM:
            markup.add(telebot.types.InlineKeyboardButton("⭐ PREMIUM за ⭐150 Stars", callback_data="payment_premium_daily_stars"))
        if user_sub.tier != SubscriptionTier.VIP:
            markup.add(telebot.types.InlineKeyboardButton("💎 VIP за ⭐250 Stars", callback_data="payment_vip_daily_stars"))
        if user_sub.tier != SubscriptionTier.ULTIMATE:
            markup.add(telebot.types.InlineKeyboardButton("👑 ULTIMATE за ⭐500 Stars", callback_data="payment_ultimate_daily_stars"))
        
        # Дополнительные опции
        markup.add(
            telebot.types.InlineKeyboardButton("📅 Недельные планы (скидка 20%)", callback_data="payment_weekly_options"),
            telebot.types.InlineKeyboardButton("📅 Месячные планы (скидка 50%)", callback_data="payment_monthly_options")
        )
        
        markup.add(
            telebot.types.InlineKeyboardButton("💎 TON платежи", callback_data="payment_method_ton"),
            telebot.types.InlineKeyboardButton("💰 Подробные цены", callback_data="payment_pricing")
        )
        
        markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        if hasattr(message, 'message_id'):
            self.bot.edit_message_text(payment_msg, message.chat.id, message.message_id,
                                     reply_markup=markup, parse_mode='Markdown')
        else:
            self.bot.send_message(message.chat.id, payment_msg,
                                reply_markup=markup, parse_mode='Markdown')

    def show_detailed_pricing(self, message):
        """💰 Детальные цены"""
        pricing_msg = """
💰 **ПОДРОБНЫЕ ЦЕНЫ** 💰

⭐ **TELEGRAM STARS:**

**⭐ PREMIUM**
• День: ⭐150 Stars
• Неделя: ⭐750 Stars (20% скидка)
• Месяц: ⭐2000 Stars (50% скидка)

**💎 VIP**
• День: ⭐250 Stars
• Неделя: ⭐1250 Stars (20% скидка)  
• Месяц: ⭐3500 Stars (50% скидка)

**👑 ULTIMATE**
• День: ⭐500 Stars
• Неделя: ⭐2500 Stars (20% скидка)
• Месяц: ⭐6500 Stars (50% скидка)

💎 **TON CRYPTO (+ 5% бонус контента):**

**⭐ PREMIUM:** 1.2 / 6.0 / 16.0 TON
**💎 VIP:** 2.0 / 10.0 / 28.0 TON  
**👑 ULTIMATE:** 4.0 / 20.0 / 52.0 TON

🎁 **БОНУСЫ:**
• Недельная подписка: 20% скидка
• Месячная подписка: 50% скидка
• TON платежи: +5% эксклюзивного контента
• Реферальная программа: скоро
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💎 Выбрать план", callback_data="payment_upgrade"),
            telebot.types.InlineKeyboardButton("⭐ Stars платеж", callback_data="payment_method_stars")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("💎 TON платеж", callback_data="payment_method_ton"),
            telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        )
        
        if hasattr(message, 'message_id'):
            self.bot.edit_message_text(pricing_msg, message.chat.id, message.message_id,
                                     reply_markup=markup, parse_mode='Markdown')
        else:
            self.bot.send_message(message.chat.id, pricing_msg,
                                reply_markup=markup, parse_mode='Markdown')

    # =============== НЕДОСТАЮЩИЕ CALLBACK HANDLERS ===============
    
    def activate_flirt_mode(self, message):
        """😘 Активация режима флирта"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        if user_sub.messages_used >= user_sub.messages_limit:
            self.handle_message_limit_reached(message, "message_limit_reached")
            return
        
        # Используем сообщение
        premium_manager.use_message(message.from_user.id)
        
        explicitness = self.determine_explicitness_level(user_sub.tier)
        flirt_response = template_manager.get_template(explicitness, ContentMode.FLIRT, 
                                                     user_sub.tier != SubscriptionTier.FREE_TRIAL)
        
        flirt_msg = f"""
😘 **РЕЖИМ ФЛИРТА АКТИВИРОВАН** 😘

💋 {flirt_response}

💕 Режим флирта включен! Все следующие сообщения будут в игривом стиле.
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💕 Больше флирта", callback_data="flirt_mode"),
            telebot.types.InlineKeyboardButton("🔥 Секси чат", callback_data="sexy_chat")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
            telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="content_menu")
        )
        
        self.bot.edit_message_text(flirt_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def activate_sexy_chat(self, message):
        """🔥 Активация секси чата"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        if user_sub.tier == SubscriptionTier.FREE_TRIAL:
            upgrade_msg = """
🔒 **СЕКСИ ЧАТ - ПРЕМИУМ ФУНКЦИЯ** 🔒

🔥 Секси чат доступен только для премиум пользователей!

💎 **Апгрейдитесь сейчас и получите:**
• Откровенные диалоги
• Сексуальные фантазии  
• Эротические ролевые игры
• Персональные просьбы

⭐ Всего за ⭐150 Stars!
            """
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("💎 АПГРЕЙД СЕЙЧАС", callback_data="payment_upgrade"),
                telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="content_menu")
            )
            
            self.bot.edit_message_text(upgrade_msg, message.chat.id, message.message_id,
                                     reply_markup=markup, parse_mode='Markdown')
            return
        
        if user_sub.messages_used >= user_sub.messages_limit:
            self.handle_message_limit_reached(message, "message_limit_reached")
            return
        
        # Используем сообщение
        premium_manager.use_message(message.from_user.id)
        
        explicitness = self.determine_explicitness_level(user_sub.tier)
        sexy_response = template_manager.get_template(explicitness, ContentMode.SEXTING, True)
        
        sexy_msg = f"""
🔥 **СЕКСИ ЧАТ АКТИВИРОВАН** 🔥

💋 {sexy_response}

🔥 Теперь мы в секси режиме! Готов к горячему общению? 😈
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🔥 Еще горячее", callback_data="sexy_chat"),
            telebot.types.InlineKeyboardButton("🎭 Ролевая игра", callback_data="role_play")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("💎 Апгрейд для большего", callback_data="payment_upgrade"),
            telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="content_menu")
        )
        
        self.bot.edit_message_text(sexy_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_roleplay_menu(self, message):
        """🎭 Меню ролевых игр"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        if user_sub.tier == SubscriptionTier.FREE_TRIAL:
            upgrade_msg = """
🔒 **РОЛЕВЫЕ ИГРЫ - ПРЕМИУМ ФУНКЦИЯ** 🔒

🎭 Ролевые игры доступны для премиум пользователей!

💎 **Доступные роли после апгрейда:**
• Учительница и ученик
• Босс и секретарша  
• Доктор и пациентка
• Массажистка
• И многое другое...

⭐ Апгрейд всего за ⭐150 Stars!
            """
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("💎 АПГРЕЙД", callback_data="payment_upgrade"),
                telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="content_menu")
            )
        else:
            roleplay_msg = """
🎭 **РОЛЕВЫЕ ИГРЫ** 🎭

Выберите сценарий для нашей игры:

👩‍🏫 **Учительница** - Строгая, но соблазнительная
👩‍💼 **Секретарша** - Профессиональная и развратная  
👩‍⚕️ **Медсестра** - Заботливая и игривая
💆‍♀️ **Массажистка** - Расслабляющие прикосновения
👸 **Принцесса** - Королевское обольщение
😈 **Демонесса** - Запретные желания

🎯 Или опишите свой сценарий!
            """
            
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                telebot.types.InlineKeyboardButton("👩‍🏫 Учительница", callback_data="roleplay_teacher"),
                telebot.types.InlineKeyboardButton("👩‍💼 Секретарша", callback_data="roleplay_secretary")
            )
            markup.add(
                telebot.types.InlineKeyboardButton("👩‍⚕️ Медсестра", callback_data="roleplay_nurse"),
                telebot.types.InlineKeyboardButton("💆‍♀️ Массажистка", callback_data="roleplay_massage")
            )
            markup.add(
                telebot.types.InlineKeyboardButton("👸 Принцесса", callback_data="roleplay_princess"),
                telebot.types.InlineKeyboardButton("😈 Демонесса", callback_data="roleplay_demon")
            )
            markup.add(
                telebot.types.InlineKeyboardButton("🎯 Свой сценарий", callback_data="custom_request"),
                telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="content_menu")
            )
        
        self.bot.edit_message_text(roleplay_msg if user_sub.tier != SubscriptionTier.FREE_TRIAL else upgrade_msg, 
                                 message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_custom_request_menu(self, message):
        """🎯 Меню кастомных запросов"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        custom_msg = f"""
🎯 **КАСТОМНЫЕ ЗАПРОСЫ** 🎯

💡 **Доступно для {user_sub.tier.value.replace('_', ' ').title()}:**

📝 Опишите ваши желания и фантазии, и я создам персональный контент специально для вас!

🌟 **Примеры запросов:**
• Конкретная ролевая ситуация
• Определенный стиль общения
• Специфические фетиши (VIP+)
• Персональные фантазии

✍️ **Просто напишите ваш запрос следующим сообщением!**

⚠️ Помните: кастомные запросы используют сообщения из вашего лимита.
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💡 Примеры запросов", callback_data="show_request_examples"),
            telebot.types.InlineKeyboardButton("💎 Апгрейд для большего", callback_data="payment_upgrade")
        )
        markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="content_menu"))
        
        self.bot.edit_message_text(custom_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def claim_daily_bonus(self, message):
        """🎯 Дневной бонус"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        # Простая система бонусов (можно расширить)
        today = datetime.now().strftime("%Y-%m-%d")
        
        bonus_msg = f"""
🎯 **ДНЕВНОЙ БОНУС** 🎯

🎁 **Ваш бонус за {today}:**

💬 +5 дополнительных сообщений!
⭐ Эксклюзивный контент дня
🔥 Специальное сообщение от меня

{template_manager.get_template(
    self.determine_explicitness_level(user_sub.tier),
    ContentMode.FLIRT,
    user_sub.tier != SubscriptionTier.FREE_TRIAL
)}

💝 Возвращайтесь завтра за новым бонусом!
        """
        
        # Добавляем бонусные сообщения (простая реализация)
        if user_sub.messages_used > 5:
            user_sub.messages_used -= 5
            premium_manager.save_users()
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🎁 Спасибо!", callback_data="main_menu"),
            telebot.types.InlineKeyboardButton("💎 Апгрейд", callback_data="payment_upgrade")
        )
        
        self.bot.edit_message_text(bonus_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def share_bot_menu(self, message):
        """📢 Меню поделиться ботом"""
        share_msg = """
📢 **ПОДЕЛИТЬСЯ БОТОМ** 📢

🌟 Поделитесь нашим ботом с друзьями и получите бонусы!

🎁 **Реферальная программа:**
• За каждого друга: +50 бонусных сообщений
• Ваш друг получает: +25 стартовых сообщений
• При апгрейде друга: скидка 20% на ваш следующий платеж

🔗 **Ваша реферальная ссылка:**
`https://t.me/your_bot_name?start=ref_{message.from_user.id}`

📱 **Поделиться в соцсетях:**
Расскажите о лучшем AI компаньоне!

💡 Скопируйте ссылку и отправьте друзьям!
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📱 Поделиться", 
                                             url=f"https://t.me/share/url?url=https://t.me/your_bot_name?start=ref_{message.from_user.id}&text=Попробуй лучшего AI компаньона!")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("📊 Мои рефералы", callback_data="show_referrals"),
            telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        )
        
        self.bot.edit_message_text(share_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def handle_admin_callback(self, call):
        """⚙️ Обработка админ callbacks"""
        data = call.data
        
        if data == "admin_users":
            self.admin_handler.show_users(call.message)
        elif data == "admin_revenue":
            self.admin_handler.show_revenue(call.message)
        elif data == "admin_stats":
            self.admin_handler.show_stats(call.message)
        elif data == "admin_health":
            self.admin_handler.health_check(call.message)
        else:
            self.bot.edit_message_text("⚙️ Админ функция в разработке", 
                                     call.message.chat.id, call.message.message_id)

    # =============== ДОПОЛНИТЕЛЬНЫЕ НЕДОСТАЮЩИЕ HANDLERS ===============
    
    def handle_start_chatting(self, message):
        """🚀 Начать общение"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        if user_sub.messages_used >= user_sub.messages_limit:
            self.handle_message_limit_reached(message, "message_limit_reached")
            return
        
        # Используем сообщение
        premium_manager.use_message(message.from_user.id)
        
        explicitness = self.determine_explicitness_level(user_sub.tier)
        chat_response = template_manager.get_template(explicitness, ContentMode.CHAT, 
                                                    user_sub.tier != SubscriptionTier.FREE_TRIAL)
        
        chat_msg = f"""
🚀 **ОБЩЕНИЕ НАЧАЛОСЬ!** 🚀

💬 {chat_response}

🎯 Теперь можете писать мне что угодно! Я отвечу в зависимости от вашего тарифа.
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💕 Флирт режим", callback_data="flirt_mode"),
            telebot.types.InlineKeyboardButton("🔞 Контент", callback_data="content_menu")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
            telebot.types.InlineKeyboardButton("💎 Апгрейд", callback_data="payment_upgrade")
        )
        
        self.bot.edit_message_text(chat_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_user_profile(self, message):
        """👤 Профиль пользователя"""
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
        user_sub = premium_manager.get_user_subscription(user_id)
        
        # Статистика пользователя
        days_active = (datetime.now() - user_sub.subscription_start).days
        messages_total = user_sub.messages_used
        money_spent = user_sub.total_paid
        
        profile_msg = f"""
👤 **ВАШ ПРОФИЛЬ** 👤

🆔 **ID:** {user_id}
🏆 **Статус:** {user_sub.tier.value.replace('_', ' ').title()}
📅 **Активен:** {days_active} дней
💰 **Потрачено:** ${money_spent:.2f}

📊 **СТАТИСТИКА:**
💬 Сообщений отправлено: {messages_total:,}
🎯 Активных дней: {days_active}
💎 Текущий лимит: {user_sub.messages_limit:,}/период
📱 Осталось: {user_sub.messages_limit - user_sub.messages_used:,}

🏅 **ДОСТИЖЕНИЯ:**
{"🌟 Активный пользователь" if days_active > 7 else "🔰 Новичок"}
{"💎 VIP клиент" if money_spent > 50 else ""}
{"👑 Премиум пользователь" if user_sub.tier != SubscriptionTier.FREE_TRIAL else ""}

⏰ **Подписка до:** {user_sub.subscription_end.strftime('%d.%m.%Y %H:%M')}
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("💎 Апгрейд", callback_data="payment_upgrade"),
            telebot.types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("📊 Обновить", callback_data="user_profile"),
            telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        )
        
        self.bot.edit_message_text(profile_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_settings_menu(self, message):
        """⚙️ Меню настроек"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        settings_msg = f"""
⚙️ **НАСТРОЙКИ** ⚙️

🎯 **Текущие настройки:**
🔞 Эксплицитность: {self.determine_explicitness_level(user_sub.tier).value.title()}
🌐 Язык: Русский 
🎭 Режим: {user_sub.tier.value.replace('_', ' ').title()}

📝 **Доступные настройки:**
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        
        # Настройки эксплицитности
        markup.add(
            telebot.types.InlineKeyboardButton("🔞 Уровень контента", callback_data="explicitness_settings"),
            telebot.types.InlineKeyboardButton("🌐 Язык", callback_data="language_settings")
        )
        
        # Уведомления и прочее
        markup.add(
            telebot.types.InlineKeyboardButton("🔔 Уведомления", callback_data="notification_settings"),
            telebot.types.InlineKeyboardButton("🎨 Интерфейс", callback_data="ui_settings")
        )
        
        markup.add(
            telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"),
            telebot.types.InlineKeyboardButton("👤 Профиль", callback_data="user_profile")
        )
        
        self.bot.edit_message_text(settings_msg, message.chat.id, message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def handle_roleplay_callbacks(self, call, roleplay_type):
        """🎭 Обработка ролевых игр"""
        user_sub = premium_manager.get_user_subscription(call.from_user.id)
        
        if user_sub.messages_used >= user_sub.messages_limit:
            self.handle_message_limit_reached(call.message, "message_limit_reached")
            return
        
        # Используем сообщение
        premium_manager.use_message(call.from_user.id)
        
        roleplay_scenarios = {
            "teacher": {
                "title": "👩‍🏫 Строгая Учительница",
                "intro": "Добро пожаловать на мой урок... Надеюсь, вы готовы к особому занятию? 😏",
                "description": "Я ваша строгая, но соблазнительная учительница. Сегодня у нас особый урок..."
            },
            "secretary": {
                "title": "👩‍💼 Развратная Секретарша", 
                "intro": "Босс, у вас есть несколько минут для... частного совещания? 💋",
                "description": "Я ваша личная секретарша, готовая выполнить любые задания..."
            },
            "nurse": {
                "title": "👩‍⚕️ Игривая Медсестра",
                "intro": "Пациент, пора на осмотр... Думаю, вам потребуется особое лечение 😘",
                "description": "Я заботливая медсестра, которая знает лучшее лекарство..."
            },
            "massage": {
                "title": "💆‍♀️ Чувственная Массажистка",
                "intro": "Раздевайтесь и ложитесь... Сегодня будет особенный массаж 🔥",
                "description": "Мои руки умеют творить чудеса..."
            },
            "princess": {
                "title": "👸 Королевское Обольщение",
                "intro": "Подданный, подойди ко мне ближе... У принцессы есть особые желания 👑",
                "description": "Я капризная принцесса, привыкшая получать все что хочу..."
            },
            "demon": {
                "title": "😈 Соблазнительная Демонесса",
                "intro": "Смертный... Я явилась исполнить твои самые темные желания 🔥👹",
                "description": "Я демонесса из твоих запретных фантазий..."
            }
        }
        
        scenario = roleplay_scenarios.get(roleplay_type, roleplay_scenarios["teacher"])
        
        roleplay_msg = f"""
🎭 **РОЛЕВАЯ ИГРА НАЧАЛАСЬ!** 🎭

{scenario['title']}

💋 {scenario['intro']}

🎯 **Сценарий:** {scenario['description']}

💡 Теперь пишите мне как будто я играю эту роль! Все мои ответы будут в характере персонажа.
        """
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🎭 Сменить роль", callback_data="role_play"),
            telebot.types.InlineKeyboardButton("🔥 Больше страсти", callback_data="sexy_chat")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
            telebot.types.InlineKeyboardButton("💎 Апгрейд", callback_data="payment_upgrade")
        )
        
        self.bot.edit_message_text(roleplay_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

# Initialize and run the monetized bot
if __name__ == "__main__":
    monetized_bot = MonetizedBot()
    monetized_bot.run() 