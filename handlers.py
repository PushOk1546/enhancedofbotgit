"""
Обработчики команд для OF Assistant Bot с DeepSeek-R1
"""

import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from api_handler import deepseek_handler
from services.ai_integration import ai_service
from enhanced_logging import BotLogger
import config

# Инициализация
logger = BotLogger(
    log_dir="logs",
    log_file="handlers.log",
    logger_name="Handlers"
)

# Планировщик задач
scheduler = AsyncIOScheduler()

class BotHandlers:
    """Класс обработчиков команд бота"""
    
    def __init__(self, bot: AsyncTeleBot):
        self.bot = bot
        self.active_chats = set()  # Чаты с активными пользователями
        self.register_handlers()
        self.setup_scheduler()
        
    def register_handlers(self):
        """Регистрация всех обработчиков"""
        
        @self.bot.message_handler(commands=['start'])
        async def start_command(message):
            await self.handle_start(message)
            
        @self.bot.message_handler(commands=['test_deepseek'])
        async def test_deepseek_cmd(message):
            await self.test_deepseek_handler(message)
            
        @self.bot.message_handler(commands=['flirt'])
        async def flirt_command(message):
            await self.handle_flirt(message)
            
        @self.bot.message_handler(commands=['ppv'])
        async def ppv_command(message):
            await self.handle_ppv(message)
            
        @self.bot.message_handler(commands=['stats'])
        async def stats_command(message):
            await self.handle_stats(message)
            
        @self.bot.message_handler(commands=['generate_ppv'])
        async def generate_ppv_command(message):
            await self.handle_generate_ppv(message)
            
        # ОБРАБОТЧИКИ CALLBACK (КНОПОК)
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('style:'))
        async def handle_style_callback(call):
            await self.handle_style_selection(call)
            
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('select_reply:'))
        async def handle_select_reply_callback(call):
            await self.handle_reply_selection(call)
            
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('ppv_'))
        async def handle_ppv_callback(call):
            await self.handle_ppv_action(call)
            
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('flirt_'))
        async def handle_flirt_callback(call):
            await self.handle_flirt_action(call)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        async def handle_other_callbacks(call):
            await self.handle_general_callback(call)

        @self.bot.message_handler(func=lambda message: True)
        async def handle_all_messages(message):
            await self.process_user_message(message)
    
    def setup_scheduler(self):
        """Настройка планировщика PPV напоминаний"""
        
        # PPV напоминалка в 12:00 (обед)
        scheduler.add_job(
            self.ppv_reminder,
            'cron',
            hour=12,
            minute=0,
            args=[self.bot],
            id='ppv_reminder_noon'
        )
        
        # Вечернее напоминание в 20:00  
        scheduler.add_job(
            self.ppv_reminder,
            'cron', 
            hour=20,
            minute=0,
            args=[self.bot],
            id='ppv_reminder_evening'
        )
        
        # Ночное напоминание в 23:00 (пик активности)
        scheduler.add_job(
            self.ppv_reminder,
            'cron',
            hour=23,
            minute=0,
            args=[self.bot],
            id='ppv_reminder_night'
        )
        
        scheduler.start()
        logger.log_info("✅ Планировщик PPV напоминаний запущен (3 раза в день)")

    async def handle_start(self, message):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        self.active_chats.add(message.chat.id)
        
        welcome_text = f"""
🔥 <b>Добро пожаловать в OF Assistant Bot!</b>

Привет, {message.from_user.first_name}! 
Я твой личный AI-ассистент для OnlyFans с DeepSeek-R1! 

<b>💬 Выбери что хочешь сделать:</b>
        """
        
        # Создаем главное меню с кнопками
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("💕 Начать флирт", callback_data="flirt_start"),
            types.InlineKeyboardButton("💰 PPV Меню", callback_data="ppv_menu")
        )
        keyboard.row(
            types.InlineKeyboardButton("🧠 Тест AI", callback_data="test_ai"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="show_stats")
        )
        keyboard.row(
            types.InlineKeyboardButton("🎬 Генерация PPV", callback_data="generate_ppv_menu")
        )
        
        await self.bot.send_message(
            message.chat.id, 
            welcome_text, 
            parse_mode='HTML',
            reply_markup=keyboard
        )
        logger.log_info(f"👋 Новый пользователь: {user_id}")

    async def test_deepseek_handler(self, message):
        """Тестовый обработчик для проверки DeepSeek"""
        try:
            await self.bot.send_message(message.chat.id, "🧠 Тестирую DeepSeek-R1...")
            
            response = await deepseek_handler.ask_deepseek(
                "Привет! Ты работаешь? Ответь кратко и позитивно."
            )
            
            reply_text = f"✅ <b>DeepSeek-R1 работает!</b>\n\n💬 <i>Ответ:</i> {response}"
            await self.bot.send_message(message.chat.id, reply_text, parse_mode='HTML')
            
            logger.log_info(f"✅ DeepSeek тест успешен для пользователя {message.from_user.id}")
            
        except Exception as e:
            error_text = f"❌ <b>Ошибка DeepSeek:</b>\n<code>{str(e)}</code>"
            await self.bot.send_message(message.chat.id, error_text, parse_mode='HTML')
            logger.log_error(f"💥 Ошибка теста DeepSeek: {e}")

    async def handle_flirt(self, message):
        """Обработчик команды флирта"""
        flirt_prompt = "Начни соблазнительный диалог с новым подписчиком"
        
        try:
            response = await deepseek_handler.generate_flirt_response(
                flirt_prompt,
                {"command": "flirt_start", "user_id": message.from_user.id}
            )
            
            await self.bot.send_message(message.chat.id, f"💕 {response}")
            logger.log_info(f"💋 Флирт инициирован для пользователя {message.from_user.id}")
            
        except Exception as e:
            await self.bot.send_message(message.chat.id, "😘 Извини, что-то с настроением... Попробуй еще раз!")
            logger.log_error(f"💥 Ошибка флирта: {e}")

    async def handle_ppv(self, message):
        """Обработчик PPV команды"""
        ppv_menu = """
💰 <b>PPV Контент Меню</b>

Выбери тип контента:
        """
        
        # Создаем меню PPV с кнопками
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("📸 Фото - 15$", callback_data="ppv_photo_15"),
            types.InlineKeyboardButton("🎥 Видео - 25$", callback_data="ppv_video_25")
        )
        keyboard.row(
            types.InlineKeyboardButton("🔥 Эксклюзив - 50$", callback_data="ppv_exclusive_50"),
            types.InlineKeyboardButton("💕 Персональное - 100$", callback_data="ppv_personal_100")
        )
        keyboard.row(
            types.InlineKeyboardButton("🎬 Создать свой PPV", callback_data="ppv_custom"),
            types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        )
        
        await self.bot.send_message(
            message.chat.id, 
            ppv_menu, 
            parse_mode='HTML',
            reply_markup=keyboard
        )
        logger.log_info(f"💰 PPV меню показано пользователю {message.from_user.id}")

    async def process_user_message(self, message):
        """Обработка обычных сообщений пользователя"""
        try:
            user_text = message.text
            user_id = message.from_user.id
            
            # Добавляем чат в активные
            self.active_chats.add(message.chat.id)
            
            # Создаем сообщение для выбора стиля ответа
            await self.show_style_selection(message, user_text)
            
        except Exception as e:
            await self.bot.send_message(
                message.chat.id, 
                "😘 Извини, милый, что-то я задумалась... Напиши еще раз?"
            )
            logger.log_error(f"💥 Ошибка обработки сообщения: {e}")
    
    async def show_style_selection(self, message, user_text):
        """Показать выбор стиля ответа"""
        style_text = f"""
💬 <b>Сообщение:</b> <i>"{user_text[:100]}..."</i>

🎨 <b>Выбери стиль ответа:</b>
        """
        
        # Клавиатура выбора стиля
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("😊 Дружелюбный", callback_data=f"style:friendly:{message.message_id}"),
            types.InlineKeyboardButton("😘 Флиртующий", callback_data=f"style:flirty:{message.message_id}")
        )
        keyboard.row(
            types.InlineKeyboardButton("🔥 Страстный", callback_data=f"style:passionate:{message.message_id}"),
            types.InlineKeyboardButton("💕 Романтичный", callback_data=f"style:romantic:{message.message_id}")
        )
        keyboard.row(
            types.InlineKeyboardButton("💼 Профессиональный", callback_data=f"style:professional:{message.message_id}")
        )
        
        await self.bot.send_message(
            message.chat.id,
            style_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        # Сохраняем исходное сообщение для генерации ответов
        if not hasattr(self, 'pending_messages'):
            self.pending_messages = {}
        self.pending_messages[message.message_id] = {
            'text': user_text,
            'user_id': message.from_user.id,
            'chat_id': message.chat.id,
            'username': message.from_user.username or "Anonymous",
            'first_name': message.from_user.first_name or "Красавчик"
        }

    async def ppv_reminder(self, bot):
        """PPV напоминалка для всех активных чатов"""
        now = datetime.now().strftime("%d.%m %H:%M")
        
        reminder_messages = [
            f"🔥 <b>Время жарких новинок!</b>\n\n💕 Сегодня у меня особенное настроение... Загляни в PPV! 😈\n\n<i>⏰ {now}</i>",
            f"💰 <b>Эксклюзивный контент ждет!</b>\n\n🎯 Не проспи горячие предложения дня! 🔥\n\n<i>⏰ {now}</i>",
            f"😈 <b>Сюрприз готов!</b>\n\n💋 Специально для тебя что-то особенное... Проверь PPV! 💕\n\n<i>⏰ {now}</i>"
        ]
        
        import random
        message_text = random.choice(reminder_messages)
        
        sent_count = 0
        for chat_id in list(self.active_chats):
            try:
                await bot.send_message(chat_id, message_text, parse_mode='HTML')
                sent_count += 1
                await asyncio.sleep(0.1)  # Небольшая задержка между отправками
                
            except Exception as e:
                logger.log_error(f"❌ Ошибка отправки напоминания в чат {chat_id}: {e}")
                # Удаляем неактивный чат
                self.active_chats.discard(chat_id)
        
        logger.log_info(f"📢 PPV напоминание отправлено в {sent_count} чатов")

    async def handle_stats(self, message):
        """Обработчик команды статистики"""
        try:
            # Статистика AI сервиса
            ai_stats = ai_service.get_stats()
            
            # Статистика бота
            bot_stats = {
                "active_chats": len(self.active_chats),
                "user_id": message.from_user.id
            }
            
            stats_text = f"""
📊 <b>Статистика OF Assistant Bot</b>

🤖 <b>AI Сервис (DeepSeek):</b>
• Всего запросов: {ai_stats['total_requests']}
• Успешных: {ai_stats['successful_requests']}
• Ошибок: {ai_stats['failed_requests']}
• Кэш попаданий: {ai_stats['cache_hits']}
• Успешность: {ai_stats['success_rate']}%
• Размер кэша: {ai_stats['cache_size']}

💬 <b>Бот:</b>
• Активных чатов: {bot_stats['active_chats']}
• Ваш ID: {bot_stats['user_id']}

<i>🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            await self.bot.send_message(message.chat.id, stats_text, parse_mode='HTML')
            logger.log_info(f"📊 Статистика показана пользователю {message.from_user.id}")
            
        except Exception as e:
            await self.bot.send_message(message.chat.id, "❌ Ошибка получения статистики")
            logger.log_error(f"💥 Ошибка статистики: {e}")
    
    async def handle_generate_ppv(self, message):
        """Обработчик генерации PPV контента"""
        try:
            # Парсинг команды: /generate_ppv тип цена описание
            args = message.text.split()[1:] if len(message.text.split()) > 1 else []
            
            if len(args) < 3:
                help_text = """
🎬 <b>Генерация PPV Контента</b>

<b>Использование:</b>
<code>/generate_ppv [тип] [цена] [описание]</code>

<b>Примеры:</b>
<code>/generate_ppv фото 15 горячее селфи в ванной</code>
<code>/generate_ppv видео 25 танец в нижнем белье</code>
<code>/generate_ppv персональное 100 видео с твоим именем</code>

<b>Типы контента:</b> фото, видео, персональное, эксклюзив
                """
                await self.bot.send_message(message.chat.id, help_text, parse_mode='HTML')
                return
            
            content_type = args[0]
            try:
                price = int(args[1])
            except ValueError:
                await self.bot.send_message(message.chat.id, "❌ Цена должна быть числом!")
                return
            
            description = " ".join(args[2:])
            
            # Генерация через AI
            await self.bot.send_message(message.chat.id, "🎬 Создаю соблазнительное описание...")
            
            ppv_content = await ai_service.generate_ppv_content(
                content_type=content_type,
                price=price,
                description=description
            )
            
            result_text = f"""
🔥 <b>PPV Контент Готов!</b>

💰 <b>Цена:</b> ${price}
🎯 <b>Тип:</b> {content_type}

📝 <b>Описание:</b>
{ppv_content}

<i>🤖 Сгенерировано DeepSeek AI</i>
            """
            
            await self.bot.send_message(message.chat.id, result_text, parse_mode='HTML')
            logger.log_info(f"🎬 PPV контент сгенерирован для пользователя {message.from_user.id}")
            
        except Exception as e:
            await self.bot.send_message(message.chat.id, "❌ Ошибка генерации PPV контента")
            logger.log_error(f"💥 Ошибка генерации PPV: {e}")

    # ======= ОБРАБОТЧИКИ CALLBACK КНОПОК =======
    
    async def handle_style_selection(self, call):
        """Обработчик выбора стиля ответа"""
        try:
            # Парсим callback_data: "style:friendly:12345"
            _, style, message_id = call.data.split(':')
            message_id = int(message_id)
            
            # Получаем исходное сообщение
            if not hasattr(self, 'pending_messages') or message_id not in self.pending_messages:
                await self.bot.answer_callback_query(call.id, "❌ Сообщение не найдено")
                return
            
            original_msg = self.pending_messages[message_id]
            
            # Показываем процесс генерации
            await self.bot.edit_message_text(
                "🧠 Генерирую варианты ответов...",
                call.message.chat.id,
                call.message.message_id
            )
            
            # Генерируем несколько вариантов ответа
            responses = await self.generate_style_responses(original_msg['text'], style, original_msg)
            
            # Показываем варианты для выбора
            await self.show_response_variants(call, responses, style, message_id)
            
            await self.bot.answer_callback_query(call.id, f"✅ Стиль '{style}' выбран!")
            
        except Exception as e:
            await self.bot.answer_callback_query(call.id, "❌ Ошибка обработки")
            logger.log_error(f"💥 Ошибка выбора стиля: {e}")
    
    async def handle_reply_selection(self, call):
        """Обработчик выбора конкретного варианта ответа"""
        try:
            # Парсим callback_data: "select_reply:0:12345"
            _, variant_index, message_id = call.data.split(':')
            variant_index = int(variant_index)
            message_id = int(message_id)
            
            if not hasattr(self, 'response_variants') or message_id not in self.response_variants:
                await self.bot.answer_callback_query(call.id, "❌ Варианты не найдены")
                return
            
            responses = self.response_variants[message_id]
            selected_response = responses[variant_index]
            
            # Отправляем выбранный ответ
            await self.bot.edit_message_text(
                f"✅ <b>Отправлено:</b>\n\n{selected_response}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            
            # Очищаем временные данные
            del self.pending_messages[message_id]
            del self.response_variants[message_id]
            
            await self.bot.answer_callback_query(call.id, f"✅ Вариант #{variant_index + 1} отправлен!")
            
        except Exception as e:
            await self.bot.answer_callback_query(call.id, "❌ Ошибка отправки")
            logger.log_error(f"💥 Ошибка выбора ответа: {e}")
    
    async def handle_ppv_action(self, call):
        """Обработчик действий PPV"""
        try:
            action = call.data  # "ppv_photo_15", "ppv_video_25", etc.
            
            if action == "ppv_menu":
                await self.show_ppv_menu(call)
            elif action == "ppv_custom":
                await self.show_custom_ppv_form(call)
            elif action.startswith("ppv_"):
                await self.handle_ppv_type_selection(call, action)
            
        except Exception as e:
            await self.bot.answer_callback_query(call.id, "❌ Ошибка PPV")
            logger.log_error(f"💥 Ошибка PPV: {e}")
    
    async def handle_flirt_action(self, call):
        """Обработчик действий флирта"""
        try:
            if call.data == "flirt_start":
                await self.start_flirt_conversation(call)
            
        except Exception as e:
            await self.bot.answer_callback_query(call.id, "❌ Ошибка флирта")
            logger.log_error(f"💥 Ошибка флирта: {e}")
    
    async def handle_general_callback(self, call):
        """Обработчик общих callback действий"""
        try:
            if call.data == "main_menu":
                await self.show_main_menu(call)
            elif call.data == "test_ai":
                await self.test_ai_callback(call)
            elif call.data == "show_stats":
                await self.show_stats_callback(call)
            elif call.data == "generate_ppv_menu":
                await self.show_generate_ppv_menu(call)
            else:
                await self.bot.answer_callback_query(call.id, "🔄 Функция в разработке")
                
        except Exception as e:
            await self.bot.answer_callback_query(call.id, "❌ Ошибка")
            logger.log_error(f"💥 Ошибка callback: {e}")
    
    # ======= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =======
    
    async def generate_style_responses(self, user_text, style, context):
        """Генерация нескольких вариантов ответа в выбранном стиле"""
        try:
            # Используем AI для генерации 3 вариантов
            responses = []
            for i in range(3):
                response = await deepseek_handler.generate_response_with_style(
                    user_text, style, context, variant_number=i+1
                )
                responses.append(response)
            return responses
            
        except Exception as e:
            logger.log_error(f"💥 Ошибка генерации: {e}")
            # Fallback варианты
            return [
                f"Спасибо за сообщение! 😊",
                f"Интересно, расскажи больше! 💕", 
                f"Отличное сообщение! 🌟"
            ]
    
    async def show_response_variants(self, call, responses, style, message_id):
        """Показать варианты ответов для выбора"""
        if not hasattr(self, 'response_variants'):
            self.response_variants = {}
        
        self.response_variants[message_id] = responses
        
        # Создаем текст с вариантами
        style_names = {
            'friendly': 'Дружелюбный',
            'flirty': 'Флиртующий', 
            'passionate': 'Страстный',
            'romantic': 'Романтичный',
            'professional': 'Профессиональный'
        }
        
        variants_text = f"🎨 <b>Стиль:</b> {style_names.get(style, style)}\n\n<b>💬 Варианты ответов:</b>\n\n"
        
        # Клавиатура с вариантами
        keyboard = types.InlineKeyboardMarkup()
        
        for i, response in enumerate(responses):
            variants_text += f"<b>{i+1}.</b> {response}\n\n"
            keyboard.add(
                types.InlineKeyboardButton(
                    f"{i+1}. {response[:50]}{'...' if len(response) > 50 else ''}",
                    callback_data=f"select_reply:{i}:{message_id}"
                )
            )
        
        variants_text += "👆 <b>Выберите понравившийся вариант:</b>"
        
        await self.bot.edit_message_text(
            variants_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    async def show_main_menu(self, call):
        """Показать главное меню"""
        welcome_text = """
🔥 <b>OF Assistant Bot - Главное меню</b>

💬 Выбери что хочешь сделать:
        """
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("💕 Начать флирт", callback_data="flirt_start"),
            types.InlineKeyboardButton("💰 PPV Меню", callback_data="ppv_menu")
        )
        keyboard.row(
            types.InlineKeyboardButton("🧠 Тест AI", callback_data="test_ai"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="show_stats")
        )
        keyboard.row(
            types.InlineKeyboardButton("🎬 Генерация PPV", callback_data="generate_ppv_menu")
        )
        
        await self.bot.edit_message_text(
            welcome_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        await self.bot.answer_callback_query(call.id, "🏠 Главное меню")
    
    async def show_ppv_menu(self, call):
        """Показать PPV меню"""
        ppv_menu = """
💰 <b>PPV Контент Меню</b>

Выбери тип контента:
        """
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("📸 Фото - 15$", callback_data="ppv_photo_15"),
            types.InlineKeyboardButton("🎥 Видео - 25$", callback_data="ppv_video_25")
        )
        keyboard.row(
            types.InlineKeyboardButton("🔥 Эксклюзив - 50$", callback_data="ppv_exclusive_50"),
            types.InlineKeyboardButton("💕 Персональное - 100$", callback_data="ppv_personal_100")
        )
        keyboard.row(
            types.InlineKeyboardButton("🎬 Создать свой PPV", callback_data="ppv_custom"),
            types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        )
        
        await self.bot.edit_message_text(
            ppv_menu,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        await self.bot.answer_callback_query(call.id, "💰 PPV Меню")

# Функция для инициализации обработчиков
def setup_handlers(bot: AsyncTeleBot) -> BotHandlers:
    """Инициализация обработчиков команд"""
    handlers = BotHandlers(bot)
    logger.log_info("🎯 Обработчики команд настроены")
    return handlers 