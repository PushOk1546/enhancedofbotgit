"""
Premium System for OF Bot - Monetization Focus
Система премиум-подписки с пробным периодом и отслеживанием доходов
"""

import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
from enum import Enum

class SubscriptionTier(Enum):
    FREE_TRIAL = "free_trial"
    PREMIUM = "premium" 
    VIP = "vip"
    ULTIMATE = "ultimate"

@dataclass
class UserSubscription:
    user_id: int
    tier: SubscriptionTier
    messages_used: int
    messages_limit: int
    subscription_start: datetime
    subscription_end: datetime
    total_paid: float
    payment_method: str
    is_active: bool
    trial_used: bool
    test_mode: bool = False  # Добавлено для тест-режима
    
    @property
    def expires_at(self) -> datetime:
        """Свойство для совместимости с админ командами"""
        return self.subscription_end

@dataclass
class PaymentRecord:
    user_id: int
    amount: float
    currency: str
    payment_method: str
    transaction_id: str
    timestamp: datetime
    subscription_tier: str
    duration_days: int

class PremiumManager:
    def __init__(self):
        self.users_file = "premium_users.json"
        self.revenue_file = "daily_revenue.json" 
        self.users: Dict[int, UserSubscription] = {}
        self.load_users()
        
        # Pricing in USD
        self.pricing = {
            SubscriptionTier.PREMIUM: {"daily": 2.99, "weekly": 14.99, "monthly": 39.99},
            SubscriptionTier.VIP: {"daily": 4.99, "weekly": 24.99, "monthly": 69.99},
            SubscriptionTier.ULTIMATE: {"daily": 9.99, "weekly": 49.99, "monthly": 129.99}
        }
        
        # Message limits
        self.message_limits = {
            SubscriptionTier.FREE_TRIAL: 50,
            SubscriptionTier.PREMIUM: 500,
            SubscriptionTier.VIP: 2000,
            SubscriptionTier.ULTIMATE: 10000
        }

    def load_users(self):
        """Load user subscriptions from file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id_str, user_data in data.items():
                        user_data['user_id'] = int(user_id_str)
                        user_data['tier'] = SubscriptionTier(user_data['tier'])
                        user_data['subscription_start'] = datetime.fromisoformat(user_data['subscription_start'])
                        user_data['subscription_end'] = datetime.fromisoformat(user_data['subscription_end'])
                        # Добавляем test_mode если его нет
                        if 'test_mode' not in user_data:
                            user_data['test_mode'] = False
                        self.users[int(user_id_str)] = UserSubscription(**user_data)
            except Exception as e:
                print(f"Error loading users: {e}")

    def save_users(self):
        """Save user subscriptions to file"""
        data = {}
        for user_id, user_sub in self.users.items():
            user_dict = asdict(user_sub)
            user_dict['tier'] = user_sub.tier.value
            user_dict['subscription_start'] = user_sub.subscription_start.isoformat()
            user_dict['subscription_end'] = user_sub.subscription_end.isoformat()
            data[str(user_id)] = user_dict
            
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_user_subscription(self, user_id: int) -> UserSubscription:
        """Get user subscription or create free trial"""
        if user_id not in self.users:
            # Create free trial for new user
            self.users[user_id] = UserSubscription(
                user_id=user_id,
                tier=SubscriptionTier.FREE_TRIAL,
                messages_used=0,
                messages_limit=50,
                subscription_start=datetime.now(),
                subscription_end=datetime.now() + timedelta(days=7),
                total_paid=0.0,
                payment_method="",
                is_active=True,
                trial_used=True,
                test_mode=False
            )
            self.save_users()
        
        return self.users[user_id]

    def can_send_message(self, user_id: int) -> tuple[bool, str]:
        """Check if user can send message and return reason if not"""
        user_sub = self.get_user_subscription(user_id)
        
        # Тест-режим дает безлимитные сообщения
        if user_sub.test_mode:
            return True, "test_mode"
        
        # Check if subscription is expired
        if datetime.now() > user_sub.subscription_end:
            user_sub.is_active = False
            self.save_users()
            return False, "subscription_expired"
        
        # Check message limit
        if user_sub.messages_used >= user_sub.messages_limit:
            return False, "message_limit_reached"
            
        return True, "allowed"

    def use_message(self, user_id: int) -> bool:
        """Use one message from user's quota"""
        can_send, reason = self.can_send_message(user_id)
        if not can_send:
            return False
            
        user_sub = self.get_user_subscription(user_id)
        # В тест-режиме не увеличиваем счетчик сообщений
        if not user_sub.test_mode:
            user_sub.messages_used += 1
        self.save_users()
        return True

    def upgrade_subscription(self, user_id: int, tier: SubscriptionTier, 
                           duration_days: int, payment_amount: float,
                           payment_method: str, transaction_id: str) -> bool:
        """Upgrade user subscription"""
        user_sub = self.get_user_subscription(user_id)
        
        # Reset message counter on upgrade
        user_sub.messages_used = 0
        user_sub.tier = tier
        user_sub.messages_limit = self.message_limits[tier]
        user_sub.subscription_end = datetime.now() + timedelta(days=duration_days)
        user_sub.total_paid += payment_amount
        user_sub.payment_method = payment_method
        user_sub.is_active = True
        
        # Record payment for revenue tracking
        self.record_payment(PaymentRecord(
            user_id=user_id,
            amount=payment_amount,
            currency="USD",
            payment_method=payment_method,
            transaction_id=transaction_id,
            timestamp=datetime.now(),
            subscription_tier=tier.value,
            duration_days=duration_days
        ))
        
        self.save_users()
        return True

    def set_test_mode(self, user_id: int, enabled: bool):
        """Включить/выключить тест-режим для пользователя"""
        user_sub = self.get_user_subscription(user_id)
        user_sub.test_mode = enabled
        self.save_users()

    def reset_message_limit(self, user_id: int):
        """Сбросить лимит сообщений пользователя"""
        user_sub = self.get_user_subscription(user_id)
        user_sub.messages_used = 0
        self.save_users()

    def get_user_statistics(self) -> Dict:
        """Получить статистику пользователей"""
        now = datetime.now()
        stats = {
            'total_users': len(self.users),
            'active_24h': 0,
            'active_week': 0,
            'free_trial_users': 0,
            'premium_users': 0,
            'vip_users': 0,
            'ultimate_users': 0,
            'conversion_rate': 0,
            'premium_conversion': 0,
            'vip_conversion': 0,
            'messages_today': 0,
            'total_messages': 0,
            'avg_messages_per_user': 0,
            'most_popular_tier': 'premium'
        }
        
        for user in self.users.values():
            # Подсчет по тарифам
            if user.tier == SubscriptionTier.FREE_TRIAL:
                stats['free_trial_users'] += 1
            elif user.tier == SubscriptionTier.PREMIUM:
                stats['premium_users'] += 1
            elif user.tier == SubscriptionTier.VIP:
                stats['vip_users'] += 1
            elif user.tier == SubscriptionTier.ULTIMATE:
                stats['ultimate_users'] += 1
            
            # Активность (примерная, так как у нас нет точной даты последней активности)
            if user.subscription_end > now:
                stats['active_week'] += 1
                if (now - user.subscription_start).days <= 1:
                    stats['active_24h'] += 1
            
            # Сообщения
            stats['total_messages'] += user.messages_used
        
        # Расчет конверсии
        paid_users = stats['premium_users'] + stats['vip_users'] + stats['ultimate_users']
        if stats['total_users'] > 0:
            stats['conversion_rate'] = (paid_users / stats['total_users']) * 100
            stats['premium_conversion'] = (stats['premium_users'] / stats['total_users']) * 100
            stats['vip_conversion'] = ((stats['vip_users'] + stats['ultimate_users']) / stats['total_users']) * 100
            stats['avg_messages_per_user'] = stats['total_messages'] / stats['total_users']
        
        # Популярный тариф
        tier_counts = {
            'premium': stats['premium_users'],
            'vip': stats['vip_users'],
            'ultimate': stats['ultimate_users']
        }
        stats['most_popular_tier'] = max(tier_counts, key=tier_counts.get)
        
        return stats

    def get_daily_revenue(self, date: str) -> Dict:
        """Получить доходы за определенную дату"""
        default_revenue = {
            'total_revenue': 0.0,
            'payments': [],
            'new_subscribers': 0,
            'upgrades': 0
        }
        
        if not os.path.exists(self.revenue_file):
            return default_revenue
        
        try:
            with open(self.revenue_file, 'r', encoding='utf-8') as f:
                revenue_data = json.load(f)
                return revenue_data.get(date, default_revenue)
        except Exception as e:
            print(f"Error loading revenue data: {e}")
            return default_revenue

    def record_payment(self, payment: PaymentRecord):
        """Record payment for revenue tracking"""
        revenue_data = {}
        if os.path.exists(self.revenue_file):
            with open(self.revenue_file, 'r', encoding='utf-8') as f:
                revenue_data = json.load(f)
        
        date_key = payment.timestamp.strftime("%Y-%m-%d")
        if date_key not in revenue_data:
            revenue_data[date_key] = {
                "total_revenue": 0,
                "payments": [],
                "new_subscribers": 0,
                "upgrades": 0
            }
        
        revenue_data[date_key]["total_revenue"] += payment.amount
        revenue_data[date_key]["payments"].append({
            "user_id": payment.user_id,
            "amount": payment.amount,
            "tier": payment.subscription_tier,
            "method": payment.payment_method,
            "time": payment.timestamp.isoformat()
        })
        
        if payment.subscription_tier != "free_trial":
            revenue_data[date_key]["new_subscribers"] += 1
            
        with open(self.revenue_file, 'w', encoding='utf-8') as f:
            json.dump(revenue_data, f, ensure_ascii=False, indent=2)

    def get_user_status_message(self, user_id: int) -> str:
        """Get user status message for display"""
        user_sub = self.get_user_subscription(user_id)
        
        tier_names = {
            SubscriptionTier.FREE_TRIAL: "🆓 Пробный период",
            SubscriptionTier.PREMIUM: "⭐ Premium",
            SubscriptionTier.VIP: "💎 VIP", 
            SubscriptionTier.ULTIMATE: "👑 Ultimate"
        }
        
        messages_left = user_sub.messages_limit - user_sub.messages_used
        days_left = (user_sub.subscription_end - datetime.now()).days
        
        status_msg = f"""
📊 **ВАШ СТАТУС:**
• Тариф: {tier_names[user_sub.tier]}
• Сообщений осталось: {messages_left:,}/{user_sub.messages_limit:,}
• Дней до окончания: {days_left}
• Всего потрачено: ${user_sub.total_paid:.2f}
        """
        
        if user_sub.test_mode:
            status_msg += "\n🧪 **ТЕСТ-РЕЖИМ АКТИВЕН** (безлимит)"
        
        return status_msg

    def get_pricing_message(self) -> str:
        """Get pricing information message"""
        pricing_msg = "💰 **ТАРИФЫ И ЦЕНЫ:**\n\n"
        
        tier_names = {
            SubscriptionTier.PREMIUM: "⭐ Premium",
            SubscriptionTier.VIP: "💎 VIP",
            SubscriptionTier.ULTIMATE: "👑 Ultimate"
        }
        
        for tier, name in tier_names.items():
            prices = self.pricing[tier]
            limit = self.message_limits[tier]
            
            pricing_msg += f"**{name}** ({limit:,} сообщений):\n"
            pricing_msg += f"• День: ${prices['daily']:.2f}\n"
            pricing_msg += f"• Неделя: ${prices['weekly']:.2f}\n" 
            pricing_msg += f"• Месяц: ${prices['monthly']:.2f}\n\n"
        
        return pricing_msg

# Global premium manager instance
premium_manager = PremiumManager() 