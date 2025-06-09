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

<b>🎯 Доступные команды:</b>
/test_deepseek - Тест DeepSeek AI
/flirt - Начать флирт 💕
/ppv - Управление PPV контентом 💰

<b>💬 Просто пиши мне сообщения</b> - я отвечу соблазнительно! 😘

<i>Powered by DeepSeek-R1 🚀</i>
        """
        
        await self.bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')
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

Выбери действие:
• 📸 Новое фото - 15$
• 🎥 Видео (5 мин) - 25$ 
• 🔥 Эксклюзив - 50$
• 💕 Персональное видео - 100$

<i>Пиши номер или описание желаемого контента!</i>
        """
        
        await self.bot.send_message(message.chat.id, ppv_menu, parse_mode='HTML')
        logger.log_info(f"💰 PPV меню показано пользователю {message.from_user.id}")

    async def process_user_message(self, message):
        """Обработка обычных сообщений пользователя"""
        try:
            user_text = message.text
            user_id = message.from_user.id
            
            # Добавляем чат в активные
            self.active_chats.add(message.chat.id)
            
            # Генерируем ответ через DeepSeek
            context = {
                "user_id": user_id,
                "username": message.from_user.username or "Anonymous",
                "first_name": message.from_user.first_name or "Красавчик"
            }
            
            response = await deepseek_handler.generate_flirt_response(user_text, context)
            
            await self.bot.send_message(message.chat.id, response)
            logger.log_info(f"💬 Ответ отправлен пользователю {user_id}")
            
        except Exception as e:
            await self.bot.send_message(
                message.chat.id, 
                "😘 Извини, милый, что-то я задумалась... Напиши еще раз?"
            )
            logger.log_error(f"💥 Ошибка обработки сообщения: {e}")

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

# Функция для инициализации обработчиков
def setup_handlers(bot: AsyncTeleBot) -> BotHandlers:
    """Инициализация обработчиков команд"""
    handlers = BotHandlers(bot)
    logger.log_info("🎯 Обработчики команд настроены")
    return handlers 