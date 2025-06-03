#!/usr/bin/env python3
"""
Административные команды для Telegram Stars/TON бота
Все команды для управления пользователями, премиумом и системой
"""

import telebot
from telebot import types
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from premium_system import premium_manager, SubscriptionTier

class AdminCommands:
    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot
        self.admin_ids = [int(x) for x in os.getenv('ADMIN_USER_IDS', '377917978').split(',')]
        
    def setup_admin_commands(self):
        """Настройка всех административных команд"""
        
        # === ОСНОВНЫЕ АДМИН КОМАНДЫ ===
        @self.bot.message_handler(commands=['admin'])
        def handle_admin_panel(message):
            if self.is_admin(message.from_user.id):
                self.show_admin_panel(message)
            else:
                self.bot.reply_to(message, "❌ Доступ запрещен")
        
        @self.bot.message_handler(commands=['grant_premium'])
        def handle_grant_premium(message):
            if self.is_admin(message.from_user.id):
                self.grant_premium_command(message)
            else:
                self.bot.reply_to(message, "❌ Только для администраторов")
        
        @self.bot.message_handler(commands=['test_mode'])
        def handle_test_mode(message):
            if self.is_admin(message.from_user.id):
                self.test_mode_command(message)
            else:
                self.bot.reply_to(message, "❌ Только для администраторов")
        
        @self.bot.message_handler(commands=['unlimited'])
        def handle_unlimited(message):
            if self.is_admin(message.from_user.id):
                self.unlimited_command(message)
            else:
                self.bot.reply_to(message, "❌ Только для администраторов")
        
        # === МОНИТОРИНГ ===
        @self.bot.message_handler(commands=['revenue'])
        def handle_revenue(message):
            if self.is_admin(message.from_user.id):
                self.show_revenue(message)
            else:
                self.bot.reply_to(message, "❌ Доступ запрещен")
        
        @self.bot.message_handler(commands=['stats'])
        def handle_stats(message):
            if self.is_admin(message.from_user.id):
                self.show_stats(message)
            else:
                self.bot.reply_to(message, "❌ Доступ запрещен")
        
        @self.bot.message_handler(commands=['users'])
        def handle_users(message):
            if self.is_admin(message.from_user.id):
                self.show_users(message)
            else:
                self.bot.reply_to(message, "❌ Доступ запрещен")
        
        # === СИСТЕМА ===
        @self.bot.message_handler(commands=['health_check'])
        def handle_health_check(message):
            if self.is_admin(message.from_user.id):
                self.health_check(message)
            else:
                self.bot.reply_to(message, "❌ Доступ запрещен")
        
        @self.bot.message_handler(commands=['confirm_ton'])
        def handle_confirm_ton(message):
            if self.is_admin(message.from_user.id):
                self.confirm_ton_payment(message)
            else:
                self.bot.reply_to(message, "❌ Только для администраторов")
        
        # === ПОМОЩЬ ===
        @self.bot.message_handler(commands=['help_admin'])
        def handle_help_admin(message):
            if self.is_admin(message.from_user.id):
                self.show_admin_help(message)
            else:
                self.bot.reply_to(message, "❌ Доступ запрещен")
        
        # === CALLBACK QUERY HANDLERS ===
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
        def handle_admin_callbacks(call):
            if self.is_admin(call.from_user.id):
                self.handle_admin_callback_query(call)
            else:
                self.bot.answer_callback_query(call.id, "❌ Доступ запрещен")

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in self.admin_ids

    def show_admin_panel(self, message):
        """Показать панель администратора"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # Управление пользователями
        markup.add(
            types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
            types.InlineKeyboardButton("💰 Доходы", callback_data="admin_revenue")
        )
        
        # Выдача премиума
        markup.add(
            types.InlineKeyboardButton("🎁 Выдать Premium", callback_data="admin_grant"),
            types.InlineKeyboardButton("🧪 Тест-режим", callback_data="admin_test")
        )
        
        # Система
        markup.add(
            types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            types.InlineKeyboardButton("🔧 Диагностика", callback_data="admin_health")
        )
        
        # TON платежи
        markup.add(
            types.InlineKeyboardButton("💎 Подтвердить TON", callback_data="admin_ton"),
            types.InlineKeyboardButton("📋 Справка", callback_data="admin_help")
        )
        
        admin_msg = """
🔥 **ПАНЕЛЬ АДМИНИСТРАТОРА** 🔥

👤 **Администратор:** {username}
🕐 **Время:** {time}
📊 **Пользователей:** {total_users}
💰 **Доход сегодня:** ${daily_revenue:.2f}

⚙️ **ДОСТУПНЫЕ ФУНКЦИИ:**
• Управление пользователями
• Мониторинг доходов  
• Выдача бесплатного премиума
• Подтверждение TON платежей
• Системная диагностика

🎯 **Выберите действие:**
        """.format(
            username=message.from_user.username or message.from_user.first_name,
            time=datetime.now().strftime("%H:%M:%S"),
            total_users=len(premium_manager.users),
            daily_revenue=premium_manager.get_daily_revenue(datetime.now().strftime("%Y-%m-%d"))['total_revenue']
        )
        
        if hasattr(message, 'message_id'):
            # Если это callback
            self.bot.edit_message_text(admin_msg, message.chat.id, message.message_id, 
                                     reply_markup=markup, parse_mode='Markdown')
        else:
            # Если это команда
            self.bot.send_message(message.chat.id, admin_msg, reply_markup=markup, parse_mode='Markdown')

    def grant_premium_command(self, message):
        """Выдача бесплатного премиума"""
        try:
            parts = message.text.split()
            if len(parts) < 4:
                help_msg = """
🎁 **ВЫДАЧА БЕСПЛАТНОГО ПРЕМИУМА**

**Формат команды:**
`/grant_premium @username тариф дни`

**Примеры:**
• `/grant_premium @testuser premium 7` - Premium на 7 дней
• `/grant_premium @reviewer vip 30` - VIP на 30 дней  
• `/grant_premium @tester ultimate 14` - Ultimate на 14 дней
• `/grant_premium 123456789 premium 7` - По ID пользователя

**Доступные тарифы:**
• `premium` - 500 сообщений/период
• `vip` - 2000 сообщений/период
• `ultimate` - 10000 сообщений/период
                """
                self.bot.reply_to(message, help_msg, parse_mode='Markdown')
                return
            
            # Парсинг параметров
            username_or_id = parts[1]
            tier_str = parts[2].lower()
            days = int(parts[3])
            
            # Определение пользователя
            if username_or_id.startswith('@'):
                username = username_or_id[1:]
                user_id = self.find_user_by_username(username)
                if not user_id:
                    self.bot.reply_to(message, f"❌ Пользователь @{username} не найден")
                    return
            else:
                user_id = int(username_or_id)
                username = self.get_username_by_id(user_id)
            
            # Маппинг тарифов
            tier_mapping = {
                "premium": SubscriptionTier.PREMIUM,
                "vip": SubscriptionTier.VIP,
                "ultimate": SubscriptionTier.ULTIMATE
            }
            
            if tier_str not in tier_mapping:
                self.bot.reply_to(message, "❌ Неверный тариф. Доступно: premium, vip, ultimate")
                return
            
            # Выдача премиума
            success = premium_manager.upgrade_subscription(
                user_id=user_id,
                tier=tier_mapping[tier_str],
                duration_days=days,
                payment_amount=0.0,  # Бесплатно
                payment_method="admin_grant",
                transaction_id=f"admin_{message.from_user.id}_{datetime.now().timestamp()}"
            )
            
            if success:
                success_msg = f"""
✅ **ПРЕМИУМ ВЫДАН УСПЕШНО!**

👤 **Пользователь:** @{username} (ID: {user_id})
💎 **Тариф:** {tier_str.upper()}
📅 **Период:** {days} дней
🎁 **Статус:** Бесплатная выдача
⏰ **Активен до:** {(datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')}

💌 Пользователь получит уведомление о активации.
                """
                self.bot.reply_to(message, success_msg, parse_mode='Markdown')
                
                # Уведомление пользователю
                try:
                    user_msg = f"""
🎉 **ПОЗДРАВЛЯЕМ!** 🎉

🎁 Вам выдан бесплатный доступ к **{tier_str.upper()}** тарифу!

📅 **Срок:** {days} дней
💎 **Включает:**
• {premium_manager.message_limits[tier_mapping[tier_str]]:,} сообщений
• Эксклюзивный контент
• Приоритетная поддержка

🔥 Наслаждайтесь премиум возможностями!
                    """
                    self.bot.send_message(user_id, user_msg, parse_mode='Markdown')
                except:
                    pass
            else:
                self.bot.reply_to(message, "❌ Ошибка при выдаче премиума")
                
        except Exception as e:
            self.bot.reply_to(message, f"❌ Ошибка: {e}")

    def test_mode_command(self, message):
        """Команда тест-режима"""
        try:
            parts = message.text.split()
            if len(parts) < 3:
                help_msg = """
🧪 **ТЕСТ-РЕЖИМ**

**Формат:**
`/test_mode @username on/off`

**Примеры:**
• `/test_mode @tester on` - Включить безлимит
• `/test_mode @reviewer off` - Выключить безлимит
• `/test_mode 123456789 on` - По ID пользователя

В тест-режиме пользователь получает безлимитные сообщения.
                """
                self.bot.reply_to(message, help_msg, parse_mode='Markdown')
                return
            
            username_or_id = parts[1]
            mode = parts[2].lower()
            
            if username_or_id.startswith('@'):
                username = username_or_id[1:]
                user_id = self.find_user_by_username(username)
                if not user_id:
                    self.bot.reply_to(message, f"❌ Пользователь @{username} не найден")
                    return
            else:
                user_id = int(username_or_id)
                username = self.get_username_by_id(user_id)
            
            if mode == 'on':
                # Включаем тест-режим (безлимит)
                premium_manager.set_test_mode(user_id, True)
                msg = f"✅ Тест-режим ВКЛЮЧЕН для @{username}\n💡 Безлимитные сообщения активированы"
            elif mode == 'off':
                # Выключаем тест-режим
                premium_manager.set_test_mode(user_id, False)
                msg = f"🔒 Тест-режим ВЫКЛЮЧЕН для @{username}\n📊 Вернулись обычные лимиты"
            else:
                self.bot.reply_to(message, "❌ Используйте 'on' или 'off'")
                return
            
            self.bot.reply_to(message, msg)
            
        except Exception as e:
            self.bot.reply_to(message, f"❌ Ошибка: {e}")

    def unlimited_command(self, message):
        """Команда безлимитных сообщений"""
        try:
            parts = message.text.split()
            if len(parts) < 2:
                help_msg = """
♾️ **БЕЗЛИМИТНЫЕ СООБЩЕНИЯ**

**Формат:**
`/unlimited @username`

**Пример:**
• `/unlimited @tester` - Сбросить лимит сообщений
• `/unlimited 123456789` - По ID пользователя

Сбрасывает текущий лимит сообщений на максимум.
                """
                self.bot.reply_to(message, help_msg, parse_mode='Markdown')
                return
            
            username_or_id = parts[1]
            
            if username_or_id.startswith('@'):
                username = username_or_id[1:]
                user_id = self.find_user_by_username(username)
                if not user_id:
                    self.bot.reply_to(message, f"❌ Пользователь @{username} не найден")
                    return
            else:
                user_id = int(username_or_id)
                username = self.get_username_by_id(user_id)
            
            # Сброс лимита сообщений
            user_sub = premium_manager.get_user_subscription(user_id)
            premium_manager.reset_message_limit(user_id)
            
            msg = f"""
♾️ **ЛИМИТ СБРОШЕН!**

👤 **Пользователь:** @{username}
📊 **Тариф:** {user_sub.tier.value}
💬 **Новый лимит:** {premium_manager.message_limits[user_sub.tier]:,} сообщений
            """
            
            self.bot.reply_to(message, msg, parse_mode='Markdown')
            
        except Exception as e:
            self.bot.reply_to(message, f"❌ Ошибка: {e}")

    def show_revenue(self, message):
        """Показать статистику доходов"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_revenue = premium_manager.get_daily_revenue(today)
        
        # Расчет доходов за период
        weekly_revenue = self.calculate_period_revenue(7)
        monthly_revenue = self.calculate_period_revenue(30)
        
        # Статистика пользователей
        total_users = len(premium_manager.users)
        premium_users = sum(1 for u in premium_manager.users.values() if u.tier != SubscriptionTier.FREE_TRIAL)
        
        revenue_msg = f"""
💰 **СТАТИСТИКА ДОХОДОВ** 💰

📅 **СЕГОДНЯ ({today}):**
• Доходы: ${today_revenue['total_revenue']:.2f}
• Новые подписчики: {today_revenue['new_subscribers']}
• Платежи: {len(today_revenue['payments'])}

📈 **НЕДЕЛЯ:**
• Общий доход: ${weekly_revenue:.2f}
• Средний в день: ${weekly_revenue/7:.2f}

📊 **МЕСЯЦ:**
• Общий доход: ${monthly_revenue:.2f}
• Средний в день: ${monthly_revenue/30:.2f}

👥 **ПОЛЬЗОВАТЕЛИ:**
• Всего: {total_users}
• Премиум: {premium_users}
• Конверсия: {(premium_users/total_users*100) if total_users > 0 else 0:.1f}%

🎯 **ПРОГНОЗ:**
• Месячный: ${monthly_revenue:.2f}
• Годовой: ${monthly_revenue * 12:.2f}
        """
        
        self.bot.send_message(message.chat.id, revenue_msg, parse_mode='Markdown')

    def show_stats(self, message):
        """Показать общую статистику"""
        stats = premium_manager.get_user_statistics()
        
        stats_msg = f"""
📊 **ОБЩАЯ СТАТИСТИКА** 📊

👥 **ПОЛЬЗОВАТЕЛИ:**
• Всего зарегистрировано: {stats['total_users']}
• Активных за сутки: {stats['active_24h']}
• Активных за неделю: {stats['active_week']}

💎 **ПОДПИСКИ:**
• Free Trial: {stats['free_trial_users']}
• Premium: {stats['premium_users']}
• VIP: {stats['vip_users']}
• Ultimate: {stats['ultimate_users']}

📈 **КОНВЕРСИЯ:**
• Общая конверсия: {stats['conversion_rate']:.1f}%
• Конверсия в Premium: {stats['premium_conversion']:.1f}%
• Конверсия в VIP+: {stats['vip_conversion']:.1f}%

💬 **АКТИВНОСТЬ:**
• Сообщений сегодня: {stats['messages_today']:,}
• Сообщений всего: {stats['total_messages']:,}
• Среднее на пользователя: {stats['avg_messages_per_user']:.1f}

⭐ **ПОПУЛЯРНЫЕ ТАРИФЫ:**
1. {stats['most_popular_tier']}
2. Premium
3. VIP
        """
        
        self.bot.send_message(message.chat.id, stats_msg, parse_mode='Markdown')

    def show_users(self, message):
        """Показать список пользователей"""
        users = list(premium_manager.users.values())[:20]  # Первые 20
        
        users_msg = "👥 **ПОЛЬЗОВАТЕЛИ (первые 20):**\n\n"
        
        for i, user in enumerate(users, 1):
            username = self.get_username_by_id(user.user_id) or "Unknown"
            tier_emoji = {"FREE_TRIAL": "🆓", "PREMIUM": "⭐", "VIP": "💎", "ULTIMATE": "👑"}
            emoji = tier_emoji.get(user.tier.value, "❓")
            
            users_msg += f"{i}. {emoji} @{username} ({user.tier.value})\n"
            users_msg += f"   💬 {user.messages_used}/{premium_manager.message_limits[user.tier]}\n"
            users_msg += f"   📅 До: {user.expires_at.strftime('%Y-%m-%d')}\n\n"
        
        if len(premium_manager.users) > 20:
            users_msg += f"... и еще {len(premium_manager.users) - 20} пользователей"
        
        self.bot.send_message(message.chat.id, users_msg, parse_mode='Markdown')

    def health_check(self, message):
        """Проверка здоровья системы"""
        health_msg = "🔧 **ДИАГНОСТИКА СИСТЕМЫ**\n\n"
        
        # Проверка API
        try:
            me = self.bot.get_me()
            health_msg += f"✅ Telegram API: @{me.username}\n"
        except Exception as e:
            health_msg += f"❌ Telegram API: {e}\n"
        
        # Проверка премиум системы
        try:
            stats = premium_manager.get_user_statistics()
            health_msg += f"✅ Premium система: {stats['total_users']} пользователей\n"
        except Exception as e:
            health_msg += f"❌ Premium система: {e}\n"
        
        # Проверка кеша
        try:
            from response_cache import response_cache
            cache_stats = response_cache.get_stats()
            health_msg += f"✅ Кеш: {cache_stats['hits']}/{cache_stats['total']} hit rate\n"
        except Exception as e:
            health_msg += f"❌ Кеш: {e}\n"
        
        # Проверка файлов
        important_files = ['adult_templates.py', 'premium_system.py', 'monetization_config.py']
        for file in important_files:
            if os.path.exists(file):
                health_msg += f"✅ {file}\n"
            else:
                health_msg += f"❌ {file} отсутствует\n"
        
        health_msg += f"\n🕐 Проверка: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.bot.send_message(message.chat.id, health_msg, parse_mode='Markdown')

    def confirm_ton_payment(self, message):
        """Подтверждение TON платежа"""
        try:
            parts = message.text.split()
            if len(parts) < 5:
                help_msg = """
💎 **ПОДТВЕРЖДЕНИЕ TON ПЛАТЕЖА**

**Формат:**
`/confirm_ton @username сумма_TON тариф дни`

**Примеры:**
• `/confirm_ton @user123 2.0 premium 7`
• `/confirm_ton 123456789 4.0 vip 30`

**Доступные тарифы:** premium, vip, ultimate
                """
                self.bot.reply_to(message, help_msg, parse_mode='Markdown')
                return
            
            username_or_id = parts[1]
            amount = float(parts[2])
            tier_str = parts[3].lower()
            days = int(parts[4])
            
            # Определение пользователя
            if username_or_id.startswith('@'):
                username = username_or_id[1:]
                user_id = self.find_user_by_username(username)
                if not user_id:
                    self.bot.reply_to(message, f"❌ Пользователь @{username} не найден")
                    return
            else:
                user_id = int(username_or_id)
                username = self.get_username_by_id(user_id)
            
            # Маппинг тарифов
            tier_mapping = {
                "premium": SubscriptionTier.PREMIUM,
                "vip": SubscriptionTier.VIP,
                "ultimate": SubscriptionTier.ULTIMATE
            }
            
            if tier_str not in tier_mapping:
                self.bot.reply_to(message, "❌ Неверный тариф")
                return
            
            # Подтверждение платежа
            success = premium_manager.upgrade_subscription(
                user_id=user_id,
                tier=tier_mapping[tier_str],
                duration_days=days,
                payment_amount=amount,
                payment_method="ton_crypto",
                transaction_id=f"ton_confirmed_{message.from_user.id}_{datetime.now().timestamp()}"
            )
            
            if success:
                success_msg = f"""
✅ **TON ПЛАТЕЖ ПОДТВЕРЖДЕН!**

👤 **Пользователь:** @{username}
💎 **Сумма:** {amount} TON
🎯 **Тариф:** {tier_str.upper()}
📅 **Период:** {days} дней
⏰ **Активен до:** {(datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')}
                """
                self.bot.reply_to(message, success_msg, parse_mode='Markdown')
                
                # Уведомление пользователю
                try:
                    user_msg = f"""
✅ **ПЛАТЕЖ ПОДТВЕРЖДЕН!** ✅

💎 Ваш TON платеж на сумму {amount} TON подтвержден!
🎯 Тариф **{tier_str.upper()}** активирован на {days} дней.

🔥 Наслаждайтесь премиум возможностями!
                    """
                    self.bot.send_message(user_id, user_msg, parse_mode='Markdown')
                except:
                    pass
            else:
                self.bot.reply_to(message, "❌ Ошибка при подтверждении платежа")
                
        except Exception as e:
            self.bot.reply_to(message, f"❌ Ошибка: {e}")

    def show_admin_help(self, message):
        """Показать справку по админ командам"""
        help_msg = """
📋 **СПРАВКА ПО АДМИН КОМАНДАМ**

🎁 **ВЫДАЧА ПРЕМИУМА:**
• `/grant_premium @user tier days` - Выдать премиум
• `/test_mode @user on/off` - Тест-режим
• `/unlimited @user` - Сбросить лимит

💰 **МОНИТОРИНГ:**
• `/revenue` - Статистика доходов
• `/stats` - Общая статистика  
• `/users` - Список пользователей

💎 **TON ПЛАТЕЖИ:**
• `/confirm_ton @user amount tier days` - Подтвердить TON

🔧 **СИСТЕМА:**
• `/health_check` - Диагностика
• `/admin` - Панель администратора

📖 **Полная документация:** ADMIN_GUIDE.txt
        """
        
        self.bot.send_message(message.chat.id, help_msg, parse_mode='Markdown')

    def handle_admin_callback_query(self, call):
        """🔥 Обработка всех админ callback queries"""
        try:
            self.bot.answer_callback_query(call.id)
            data = call.data
            
            if data == "admin_users":
                self.show_users_callback(call)
            elif data == "admin_revenue":
                self.show_revenue_callback(call)
            elif data == "admin_grant":
                self.show_grant_menu(call)
            elif data == "admin_test":
                self.show_test_mode_menu(call)
            elif data == "admin_stats":
                self.show_stats_callback(call)
            elif data == "admin_health":
                self.health_check_callback(call)
            elif data == "admin_ton":
                self.show_ton_confirmation_menu(call)
            elif data == "admin_help":
                self.show_admin_help_callback(call)
            elif data == "admin_panel":
                self.show_admin_panel(call.message)
            else:
                self.bot.edit_message_text("⚙️ Функция в разработке", 
                                         call.message.chat.id, call.message.message_id)
        except Exception as e:
            print(f"Admin callback error: {e}")

    def show_users_callback(self, call):
        """👥 Показать пользователей через callback"""
        users = list(premium_manager.users.values())[:15]  # Первые 15
        
        users_msg = "👥 **ПОЛЬЗОВАТЕЛИ СИСТЕМЫ** 👥\n\n"
        
        for i, user in enumerate(users, 1):
            username = self.get_username_by_id(user.user_id)
            tier_emoji = {"FREE_TRIAL": "🆓", "PREMIUM": "⭐", "VIP": "💎", "ULTIMATE": "👑"}
            emoji = tier_emoji.get(user.tier.value, "❓")
            
            users_msg += f"{i}. {emoji} @{username}\n"
            users_msg += f"   💬 {user.messages_used}/{premium_manager.message_limits[user.tier]}\n"
            users_msg += f"   📅 {user.expires_at.strftime('%d.%m.%Y')}\n"
            users_msg += f"   💰 ${user.total_paid:.2f}\n\n"
        
        if len(premium_manager.users) > 15:
            users_msg += f"... и еще {len(premium_manager.users) - 15} пользователей\n\n"
        
        users_msg += f"📊 **Всего пользователей:** {len(premium_manager.users)}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 Обновить", callback_data="admin_users"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        )
        markup.add(types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel"))
        
        self.bot.edit_message_text(users_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_revenue_callback(self, call):
        """💰 Показать доходы через callback"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_revenue = premium_manager.get_daily_revenue(today)
        
        weekly_revenue = self.calculate_period_revenue(7)
        monthly_revenue = self.calculate_period_revenue(30)
        
        total_users = len(premium_manager.users)
        premium_users = sum(1 for u in premium_manager.users.values() if u.tier != SubscriptionTier.FREE_TRIAL)
        
        revenue_msg = f"""
💰 **ДОХОДЫ И АНАЛИТИКА** 💰

📅 **СЕГОДНЯ ({today}):**
• 💵 Доходы: ${today_revenue['total_revenue']:.2f}
• 👥 Новые подписчики: {today_revenue['new_subscribers']}
• 💳 Платежи: {len(today_revenue['payments'])}

📈 **ПЕРИОД:**
• 📊 За неделю: ${weekly_revenue:.2f}
• 📊 За месяц: ${monthly_revenue:.2f}
• 📊 Средний день: ${weekly_revenue/7:.2f}

👥 **ПОЛЬЗОВАТЕЛИ:**
• 🔢 Всего: {total_users}
• 💎 Премиум: {premium_users}
• 📈 Конверсия: {(premium_users/total_users*100) if total_users > 0 else 0:.1f}%

🎯 **ПРОГНОЗЫ:**
• 📊 Месячный: ${monthly_revenue:.2f}
• 📊 Годовой: ${monthly_revenue * 12:.2f}
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 Обновить", callback_data="admin_revenue"),
            types.InlineKeyboardButton("📊 Детальная статистика", callback_data="admin_stats")
        )
        markup.add(types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel"))
        
        self.bot.edit_message_text(revenue_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_grant_menu(self, call):
        """🎁 Меню выдачи премиума"""
        grant_msg = """
🎁 **ВЫДАЧА БЕСПЛАТНОГО ПРЕМИУМА** 🎁

📝 **Используйте команды:**

`/grant_premium @username тариф дни`

🔸 **Примеры:**
• `/grant_premium @testuser premium 7`
• `/grant_premium 123456789 vip 30`
• `/grant_premium @reviewer ultimate 14`

🎯 **Доступные тарифы:**
• `premium` - 500 сообщений
• `vip` - 2000 сообщений  
• `ultimate` - 10000 сообщений

🧪 **Быстрые команды:**
• `/test_mode @user on` - Безлимит
• `/unlimited @user` - Сброс лимита
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
            types.InlineKeyboardButton("🧪 Тест-режим", callback_data="admin_test")
        )
        markup.add(types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel"))
        
        self.bot.edit_message_text(grant_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_test_mode_menu(self, call):
        """🧪 Меню тест-режима"""
        test_msg = """
🧪 **ТЕСТ-РЕЖИМ И ОТЛАДКА** 🧪

🔧 **Команды тестирования:**

`/test_mode @username on/off`
`/unlimited @username`  
`/reset_limit @username`

🎯 **Возможности:**
• 🔄 Безлимитные сообщения
• 🧪 Тестирование функций
• 🔓 Обход ограничений
• 🎁 Бесплатный доступ

⚠️ **Внимание:**
Тест-режим дает полный доступ ко всем функциям без списания сообщений.

📊 **Активные тестеры:**
        """
        
        # Добавляем список активных тестеров
        test_users = [user for user in premium_manager.users.values() if getattr(user, 'test_mode', False)]
        if test_users:
            for user in test_users[:5]:
                username = self.get_username_by_id(user.user_id)
                test_msg += f"• @{username} ({user.tier.value})\n"
        else:
            test_msg += "Нет активных тестеров\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("👥 Все пользователи", callback_data="admin_users"),
            types.InlineKeyboardButton("🎁 Выдать премиум", callback_data="admin_grant")
        )
        markup.add(types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel"))
        
        self.bot.edit_message_text(test_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_ton_confirmation_menu(self, call):
        """💎 Меню подтверждения TON платежей"""
        ton_msg = """
💎 **ПОДТВЕРЖДЕНИЕ TON ПЛАТЕЖЕЙ** 💎

💰 **TON Кошелек:**
`UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB`

📝 **Команда подтверждения:**
`/confirm_ton @username сумма_TON тариф дни`

🔸 **Примеры:**
• `/confirm_ton @user123 2.0 premium 7`
• `/confirm_ton 123456789 4.0 vip 30`  
• `/confirm_ton @customer 8.0 ultimate 14`

💎 **Тарифы TON:**
• Premium: 1.2 TON (день)
• VIP: 2.0 TON (день)
• Ultimate: 4.0 TON (день)

📊 **Недавние TON платежи:**
Пока нет платежей...
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("💰 Доходы", callback_data="admin_revenue"),
            types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")
        )
        markup.add(types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel"))
        
        self.bot.edit_message_text(ton_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_stats_callback(self, call):
        """📊 Детальная статистика через callback"""
        stats = premium_manager.get_user_statistics()
        
        stats_msg = f"""
📊 **ДЕТАЛЬНАЯ СТАТИСТИКА** 📊

👥 **ПОЛЬЗОВАТЕЛИ:**
• 🔢 Всего: {stats['total_users']}
• 🟢 Активных (24ч): {stats['active_24h']}
• 📅 Активных (неделя): {stats['active_week']}

💎 **ПОДПИСКИ:**
• 🆓 Free Trial: {stats['free_trial_users']}
• ⭐ Premium: {stats['premium_users']} 
• 💎 VIP: {stats['vip_users']}
• 👑 Ultimate: {stats['ultimate_users']}

📈 **КОНВЕРСИЯ:**
• 🎯 Общая: {stats['conversion_rate']:.1f}%
• ⭐ В Premium: {stats['premium_conversion']:.1f}%
• 💎 В VIP+: {stats['vip_conversion']:.1f}%

💬 **АКТИВНОСТЬ:**
• 📊 Сообщений всего: {stats['total_messages']:,}
• 📈 На пользователя: {stats['avg_messages_per_user']:.1f}

🏆 **ПОПУЛЯРНЫЙ ТАРИФ:** {stats['most_popular_tier'].title()}
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats"),
            types.InlineKeyboardButton("💰 Доходы", callback_data="admin_revenue")
        )
        markup.add(
            types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
            types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel")
        )
        
        self.bot.edit_message_text(stats_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def health_check_callback(self, call):
        """🔧 Диагностика системы через callback"""
        health_msg = "🔧 **ДИАГНОСТИКА СИСТЕМЫ** 🔧\n\n"
        
        # Проверка API
        try:
            me = self.bot.get_me()
            health_msg += f"✅ Telegram API: @{me.username}\n"
        except Exception as e:
            health_msg += f"❌ Telegram API: {str(e)[:50]}...\n"
        
        # Проверка премиум системы
        try:
            stats = premium_manager.get_user_statistics()
            health_msg += f"✅ Premium система: {stats['total_users']} пользователей\n"
        except Exception as e:
            health_msg += f"❌ Premium система: {str(e)[:50]}...\n"
        
        # Проверка кеша
        try:
            from response_cache import response_cache
            cache_stats = response_cache.get_stats()
            health_msg += f"✅ Кеш: {cache_stats['hits']}/{cache_stats['total']} запросов\n"
        except Exception as e:
            health_msg += f"❌ Кеш: {str(e)[:50]}...\n"
        
        # Проверка файлов
        important_files = ['adult_templates.py', 'premium_system.py', 'monetization_config.py']
        for file in important_files:
            if os.path.exists(file):
                health_msg += f"✅ {file}\n"
            else:
                health_msg += f"❌ {file} отсутствует\n"
        
        health_msg += f"\n🕐 Проверка: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 Повторить проверку", callback_data="admin_health"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        )
        markup.add(types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel"))
        
        self.bot.edit_message_text(health_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_admin_help_callback(self, call):
        """📋 Помощь по админ командам через callback"""
        help_msg = """
📋 **СПРАВКА ДЛЯ АДМИНИСТРАТОРА** 📋

🎁 **УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ:**
• `/grant_premium @user tier days` - Выдать премиум
• `/test_mode @user on/off` - Тест-режим
• `/unlimited @user` - Сбросить лимит

💰 **МОНИТОРИНГ:**
• `/revenue` - Доходы за день
• `/stats` - Общая статистика
• `/users` - Список пользователей

💎 **TON ПЛАТЕЖИ:**
• `/confirm_ton @user amount tier days` - Подтвердить TON

🔧 **СИСТЕМА:**
• `/health_check` - Диагностика
• `/admin` - Панель администратора

📚 **ПОЛНАЯ ДОКУМЕНТАЦИЯ:**
Смотрите файл `ADMIN_GUIDE.txt`
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🎁 Выдача премиума", callback_data="admin_grant"),
            types.InlineKeyboardButton("💎 TON платежи", callback_data="admin_ton")
        )
        markup.add(
            types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            types.InlineKeyboardButton("🔧 Диагностика", callback_data="admin_health")
        )
        markup.add(types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel"))
        
        self.bot.edit_message_text(help_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def find_user_by_username(self, username: str) -> Optional[int]:
        """Найти пользователя по username"""
        # Поиск по базе пользователей premium_manager
        for user_id, user_sub in premium_manager.users.items():
            # Простая реализация - возвращаем первый найденный ID
            # В реальном проекте здесь была бы связь с базой данных username->user_id
            if username.lower() in str(user_id):  # Простое сопоставление
                return user_id
        
        # Также можно попробовать парсить как ID
        try:
            potential_id = int(username)
            if potential_id in premium_manager.users:
                return potential_id
        except ValueError:
            pass
        
        return None
    
    def get_username_by_id(self, user_id: int) -> Optional[str]:
        """Получить username по ID"""
        # В идеале здесь была бы база данных с привязкой user_id -> username
        # Для демо-версии возвращаем форматированное имя
        if user_id in premium_manager.users:
            return f"user{user_id}"
        
        # Можно добавить кеш последних пользователей
        username_cache = {
            377917978: "admin",  # Известный админ
        }
        
        return username_cache.get(user_id, f"user{user_id}")
    
    def calculate_period_revenue(self, days: int) -> float:
        """Расчет доходов за период"""
        total_revenue = 0.0
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_revenue = premium_manager.get_daily_revenue(date)
            total_revenue += day_revenue['total_revenue']
        
        return total_revenue

# Функция для интеграции с основным ботом
def setup_admin_commands(bot: telebot.TeleBot):
    """Настройка админ команд в боте"""
    admin_commands = AdminCommands(bot)
    admin_commands.setup_admin_commands()
    return admin_commands 