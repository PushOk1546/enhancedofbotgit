#!/usr/bin/env python3
"""
Простой стартер Telegram Stars/TON бота
Без автоматического управления процессами
"""

import os
import time
from datetime import datetime

def print_banner():
    """Баннер"""
    print("=" * 60)
    print("🔥 TELEGRAM STARS & TON BOT - SIMPLE START 🔥")
    print("=" * 60)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def main():
    """Простой запуск без проверок процессов"""
    print_banner()
    
    # Проверка токена
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ BOT_TOKEN не установлен!")
        print("📝 Используйте: set BOT_TOKEN=ваш_токен")
        input("Нажмите Enter для выхода...")
        return
    
    print(f"✅ Токен: ...{token[-8:]}")
    
    try:
        import telebot
        print("✅ pyTelegramBotAPI импортирован")
        
        # Создание простого бота
        bot = telebot.TeleBot(token)
        
        # Очистка webhook
        try:
            bot.remove_webhook()
            print("✅ Webhook очищен")
        except:
            print("⚠️ Не удалось очистить webhook")
        
        # Тест API
        me = bot.get_me()
        print(f"✅ API: @{me.username}")
        
        # Импорт и запуск монетизированного бота
        from monetized_bot import MonetizedBot
        
        monetized_bot = MonetizedBot()
        print("✅ Монетизированный бот создан")
        
        print("\n🔥 БОТ ЗАПУЩЕН!")
        print("⭐ Telegram Stars: АКТИВНЫ")
        print("💎 TON платежи: АКТИВНЫ")
        print("🔞 Эксплицитный контент: ЗАГРУЖЕН")
        print("📱 Начните чат в Telegram!")
        print("⏹️ Ctrl+C для остановки")
        print()
        
        # Запуск polling
        monetized_bot.bot.polling(
            none_stop=True,
            timeout=60,
            long_polling_timeout=60
        )
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if "409" in str(e):
            print("💡 Ошибка 409: Возможно, запущен другой экземпляр")
            print("📝 Подождите 30 секунд и попробуйте снова")
    finally:
        print("\n⏹️ Бот остановлен")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main() 