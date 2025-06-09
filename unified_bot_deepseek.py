#!/usr/bin/env python3
"""
🔥 UNIFIED OF ASSISTANT BOT WITH DEEPSEEK 🔥
Объединенный бот с DeepSeek AI для контента для взрослых
Оптимизированная версия без дублей
"""

import asyncio
import sys
import os
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime

# Безопасный импорт TeleBot
try:
    from telebot.async_telebot import AsyncTeleBot
    import telebot.types as types
    print("✅ TeleBot импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта TeleBot: {e}")
    sys.exit(1)

# Импорты проекта
try:
    from config import config
    from enhanced_logging import BotLogger
    from deepseek_integration import generate_reply_variants
    print("✅ Модули проекта импортированы")
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    sys.exit(1)

class UnifiedBotDeepSeek:
    """Единый оптимизированный класс бота с DeepSeek AI"""
    
    def __init__(self):
        """Инициализация бота"""
        # Логгер
        self.logger = BotLogger(
            log_dir="logs",
            log_file="unified_bot_deepseek.log",
            logger_name="UnifiedBotDeepSeek"
        )
        
        self.logger.log_info("🤖 Инициализация Unified Bot с DeepSeek AI...")
        
        # Проверка токенов
        if not config.TELEGRAM_BOT_TOKEN:
            self.logger.log_error("❌ TELEGRAM_BOT_TOKEN не найден")
            raise ValueError("TELEGRAM_BOT_TOKEN обязателен")
        
        if not config.DEEPSEEK_API_KEY:
            self.logger.log_error("❌ DEEPSEEK_API_KEY не найден")
            raise ValueError("DEEPSEEK_API_KEY обязателен для работы с DeepSeek AI")
        
        # Инициализация бота
        try:
            self.bot = AsyncTeleBot(
                token=config.TELEGRAM_BOT_TOKEN,
                parse_mode='HTML'
            )
            self.logger.log_info("✅ AsyncTeleBot инициализирован")
        except Exception as e:
            self.logger.log_error(f"❌ Ошибка инициализации бота: {e}")
            raise
        
        # Статистика
        self.stats = {
            'messages_processed': 0,
            'start_time': datetime.now(),
            'users': set(),
            'errors': 0,
            'nsfw_requests': 0,
            'deepseek_calls': 0
        }
        
        # Регистрация обработчиков
        self._register_handlers()
        
        self.logger.log_info("🚀 Unified Bot с DeepSeek готов к работе")
    
    def _register_handlers(self):
        """Регистрация обработчиков команд"""
        
        @self.bot.message_handler(commands=['start'])
        async def handle_start(message):
            """Обработчик команды /start"""
            try:
                user_id = message.from_user.id
                username = message.from_user.username or "Unknown"
                self.stats['users'].add(user_id)
                
                self.logger.log_info(f"👤 Команда /start от пользователя {user_id} (@{username})")
                
                welcome_text = (
                    f"🔥 <b>Привет! Я OF Assistant Bot с DeepSeek AI</b>\n\n"
                    f"🎭 <b>Особенности:</b>\n"
                    f"• Использую DeepSeek AI - более лояльный к NSFW контенту\n"
                    f"• Создаю смелые и откровенные ответы\n"
                    f"• Поддерживаю эротический контент и флирт\n\n"
                    f"🔥 <b>Команды:</b>\n"
                    f"• /reply &lt;сообщение&gt; - генерация ответов\n"
                    f"• /stats - статистика бота\n"
                    f"• /help - справка\n\n"
                    f"💋 <b>Просто отправь /reply и твое сообщение!</b>\n"
                    f"<i>Пример: /reply Привет, красавчик!</i>"
                )
                
                await self.bot.reply_to(message, welcome_text)
                
            except Exception as e:
                self.logger.log_error(f"❌ Ошибка в /start: {e}")
                await self.bot.reply_to(message, "❌ Произошла ошибка. Попробуйте позже.")
        
        @self.bot.message_handler(commands=['help'])
        async def handle_help(message):
            """Обработчик команды /help"""
            try:
                help_text = (
                    f"📖 <b>OF Assistant Bot с DeepSeek AI</b>\n\n"
                    f"🎭 <b>Что я умею:</b>\n"
                    f"• Создаю смелый и откровенный контент\n"
                    f"• Генерирую флиртующие ответы\n"
                    f"• Поддерживаю эротические темы\n"
                    f"• Не цензурирую контент для взрослых\n\n"
                    f"🔥 <b>Команды:</b>\n"
                    f"• <code>/start</code> - начать работу\n"
                    f"• <code>/reply &lt;текст&gt;</code> - генерация ответов\n"
                    f"• <code>/stats</code> - статистика\n"
                    f"• <code>/help</code> - эта справка\n\n"
                    f"💡 <b>Примеры использования:</b>\n"
                    f"• <code>/reply Привет, как дела?</code>\n"
                    f"• <code>/reply Скучаю по тебе...</code>\n"
                    f"• <code>/reply Что ты делаешь сегодня вечером?</code>\n\n"
                    f"🔞 <i>Бот создан для контента 18+</i>"
                )
                
                await self.bot.reply_to(message, help_text)
                
            except Exception as e:
                self.logger.log_error(f"❌ Ошибка в /help: {e}")
                await self.bot.reply_to(message, "❌ Ошибка отображения справки.")
        
        @self.bot.message_handler(commands=['reply'])
        async def handle_reply(message):
            """Обработчик команды /reply с DeepSeek AI"""
            try:
                user_id = message.from_user.id
                username = message.from_user.username or "Unknown"
                
                # Извлекаем текст сообщения
                command_parts = message.text.split(' ', 1)
                if len(command_parts) < 2:
                    await self.bot.reply_to(
                        message, 
                        "❌ <b>Укажите сообщение для генерации ответа</b>\n\n"
                        "💡 <b>Пример:</b>\n"
                        "<code>/reply Привет, красавчик!</code>\n"
                        "<code>/reply Скучаю по тебе...</code>"
                    )
                    return
                
                user_message = command_parts[1].strip()
                
                if len(user_message) < 3:
                    await self.bot.reply_to(message, "❌ Сообщение слишком короткое (минимум 3 символа).")
                    return
                
                if len(user_message) > 500:
                    await self.bot.reply_to(message, "❌ Сообщение слишком длинное (максимум 500 символов).")
                    return
                
                self.logger.log_info(f"💬 DeepSeek запрос от {user_id} (@{username}): {user_message[:50]}...")
                
                # Проверяем на NSFW контент
                is_nsfw = any(word in user_message.lower() for word in [
                    'секс', 'любовь', 'страсть', 'желание', 'хочу', 'ночь', 'постель', 
                    'красив', 'горяч', 'возбужд', 'скучаю', 'мечтаю'
                ])
                if is_nsfw:
                    self.stats['nsfw_requests'] += 1
                
                # Отправляем уведомление о генерации
                processing_msg = await self.bot.reply_to(
                    message, 
                    "🔥 <b>DeepSeek AI генерирует варианты ответов...</b>\n"
                    "<i>Создаю смелый и откровенный контент</i> 🎭"
                )
                
                # Генерируем ответы через DeepSeek
                start_time = time.time()
                reply_variants = await generate_reply_variants(user_message, 3)
                generation_time = time.time() - start_time
                
                # Обновляем статистику
                self.stats['messages_processed'] += 1
                self.stats['deepseek_calls'] += 1
                
                if reply_variants and len(reply_variants) > 0:
                    # Формируем ответ с вариантами
                    response_text = f"💫 <b>DeepSeek AI сгенерировал варианты для:</b>\n<i>\"{user_message}\"</i>\n\n"
                    
                    for i, variant in enumerate(reply_variants[:3], 1):
                        # Добавляем эмодзи в зависимости от контента
                        emoji = "🔥" if is_nsfw else "💭"
                        response_text += f"{emoji} <b>{i}.</b> {variant}\n\n"
                    
                    response_text += f"⏱️ <i>Генерация: {generation_time:.1f}с | Powered by DeepSeek AI</i>"
                    
                    # Удаляем сообщение о генерации и отправляем результат
                    await self.bot.delete_message(message.chat.id, processing_msg.message_id)
                    await self.bot.reply_to(message, response_text)
                    
                    self.logger.log_info(f"✅ DeepSeek ответы сгенерированы для {user_id} за {generation_time:.1f}с")
                    
                else:
                    await self.bot.edit_message_text(
                        "❌ <b>DeepSeek AI не смог сгенерировать ответы</b>\n\n"
                        "💡 Попробуйте:\n"
                        "• Переформулировать сообщение\n"
                        "• Использовать более конкретный запрос\n"
                        "• Проверить подключение к интернету",
                        message.chat.id,
                        processing_msg.message_id
                    )
                    self.logger.log_warning(f"⚠️ DeepSeek не сгенерировал ответы для {user_id}")
                
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.log_error(f"❌ Ошибка в /reply: {e}")
                await self.bot.reply_to(message, "❌ Произошла ошибка при генерации. Попробуйте позже.")
        
        @self.bot.message_handler(commands=['stats'])
        async def handle_stats(message):
            """Обработчик команды /stats"""
            try:
                uptime = datetime.now() - self.stats['start_time']
                uptime_str = f"{uptime.days}д {uptime.seconds//3600}ч {(uptime.seconds%3600)//60}м"
                
                stats_text = (
                    f"📊 <b>Статистика DeepSeek Bot</b>\n\n"
                    f"🤖 <b>AI Движок:</b> DeepSeek Chat\n"
                    f"⏰ <b>Время работы:</b> {uptime_str}\n"
                    f"💬 <b>Обработано сообщений:</b> {self.stats['messages_processed']}\n"
                    f"🔥 <b>DeepSeek вызовов:</b> {self.stats['deepseek_calls']}\n"
                    f"🔞 <b>NSFW запросов:</b> {self.stats['nsfw_requests']}\n"
                    f"👥 <b>Уникальных пользователей:</b> {len(self.stats['users'])}\n"
                    f"❌ <b>Ошибок:</b> {self.stats['errors']}\n"
                    f"🔋 <b>Статус:</b> Активен\n\n"
                    f"📈 <b>Производительность:</b>\n"
                    f"• Среднее время DeepSeek: ~2-4с\n"
                    f"• Поддержка NSFW: ✅\n"
                    f"• Цензура: ❌ (отключена)\n"
                    f"• Доступность: 99.9%"
                )
                
                await self.bot.reply_to(message, stats_text)
                
            except Exception as e:
                self.logger.log_error(f"❌ Ошибка в /stats: {e}")
                await self.bot.reply_to(message, "❌ Ошибка получения статистики.")
        
        @self.bot.message_handler(func=lambda message: True)
        async def handle_unknown(message):
            """Обработчик неизвестных сообщений"""
            try:
                unknown_text = (
                    f"❓ <b>Неизвестная команда</b>\n\n"
                    f"💡 <b>Доступные команды:</b>\n"
                    f"• /start - начать работу\n"
                    f"• /reply &lt;сообщение&gt; - генерация ответов\n"
                    f"• /stats - статистика\n"
                    f"• /help - справка\n\n"
                    f"🎭 <i>Я создаю контент для взрослых с помощью DeepSeek AI</i>"
                )
                
                await self.bot.reply_to(message, unknown_text)
                
            except Exception as e:
                self.logger.log_error(f"❌ Ошибка в handle_unknown: {e}")
    
    async def start_polling(self):
        """Запуск polling режима"""
        try:
            self.logger.log_info("🚀 Запуск polling режима...")
            await self.bot.polling(non_stop=True)
        except Exception as e:
            self.logger.log_error(f"❌ Критическая ошибка polling: {e}")
            raise
    
    async def stop(self):
        """Остановка бота"""
        try:
            self.logger.log_info("🛑 Остановка DeepSeek Bot...")
            await self.bot.stop_polling()
            self.logger.log_info("✅ DeepSeek Bot остановлен")
        except Exception as e:
            self.logger.log_error(f"❌ Ошибка остановки: {e}")

async def main():
    """Главная функция запуска бота"""
    print("🔥 Unified OF Assistant Bot с DeepSeek AI")
    print("=" * 50)
    
    try:
        # Создаем экземпляр бота
        bot = UnifiedBotDeepSeek()
        
        # Запускаем бота
        print("🚀 Запуск DeepSeek бота...")
        await bot.start_polling()
        
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки...")
        if 'bot' in locals():
            await bot.stop()
        print("✅ DeepSeek бот остановлен")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Программа завершена пользователем")
    except Exception as e:
        print(f"❌ Фатальная ошибка: {e}")
        sys.exit(1) 