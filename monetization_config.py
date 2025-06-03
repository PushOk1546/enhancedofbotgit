"""
Monetization Configuration - Updated for Telegram Stars and TON
All settings for premium system, pricing, and revenue optimization
"""

import os
from typing import List

class MonetizationConfig:
    """Configuration class for monetized OF bot with Telegram Stars and TON support"""
    
    # Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    GROQ_KEY = os.getenv('GROQ_KEY', 'YOUR_GROQ_KEY_HERE')
    
    # Premium System Settings
    TEMPLATE_USAGE_RATIO = float(os.getenv('TEMPLATE_USAGE_RATIO', '0.85'))
    CONVERSION_TRIGGER_THRESHOLD = float(os.getenv('CONVERSION_TRIGGER_THRESHOLD', '0.8'))
    
    # Cache Settings for Cost Reduction
    CACHE_SIZE = int(os.getenv('CACHE_SIZE', '15000'))
    CACHE_TTL_HOURS = int(os.getenv('CACHE_TTL_HOURS', '336'))
    API_COST_PER_REQUEST = float(os.getenv('API_COST_PER_REQUEST', '0.002'))
    
    # TON Wallet Configuration
    TON_WALLET_ADDRESS = os.getenv('TON_WALLET', 'UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB')
    
    # Telegram Stars Pricing (1 Star ≈ $0.01-0.02)
    STARS_PRICING = {
        'premium': {
            'daily': int(os.getenv('PREMIUM_DAILY_STARS', '150')),      # ~$2.99
            'weekly': int(os.getenv('PREMIUM_WEEKLY_STARS', '750')),    # ~$14.99 (20% off)
            'monthly': int(os.getenv('PREMIUM_MONTHLY_STARS', '2000'))  # ~$39.99 (50% off)
        },
        'vip': {
            'daily': int(os.getenv('VIP_DAILY_STARS', '250')),          # ~$4.99
            'weekly': int(os.getenv('VIP_WEEKLY_STARS', '1250')),       # ~$24.99 (20% off)
            'monthly': int(os.getenv('VIP_MONTHLY_STARS', '3500'))      # ~$69.99 (50% off)
        },
        'ultimate': {
            'daily': int(os.getenv('ULTIMATE_DAILY_STARS', '500')),     # ~$9.99
            'weekly': int(os.getenv('ULTIMATE_WEEKLY_STARS', '2500')),  # ~$49.99 (20% off)
            'monthly': int(os.getenv('ULTIMATE_MONTHLY_STARS', '6500')) # ~$129.99 (50% off)
        }
    }
    
    # TON Cryptocurrency Pricing (approximate conversion)
    TON_PRICING = {
        'premium': {
            'daily': float(os.getenv('PREMIUM_DAILY_TON', '1.2')),      # ~$2.99
            'weekly': float(os.getenv('PREMIUM_WEEKLY_TON', '6.0')),    # ~$14.99 (20% off)
            'monthly': float(os.getenv('PREMIUM_MONTHLY_TON', '16.0'))  # ~$39.99 (50% off)
        },
        'vip': {
            'daily': float(os.getenv('VIP_DAILY_TON', '2.0')),          # ~$4.99
            'weekly': float(os.getenv('VIP_WEEKLY_TON', '10.0')),       # ~$24.99 (20% off)
            'monthly': float(os.getenv('VIP_MONTHLY_TON', '28.0'))      # ~$69.99 (50% off)
        },
        'ultimate': {
            'daily': float(os.getenv('ULTIMATE_DAILY_TON', '4.0')),     # ~$9.99
            'weekly': float(os.getenv('ULTIMATE_WEEKLY_TON', '20.0')),  # ~$49.99 (20% off)
            'monthly': float(os.getenv('ULTIMATE_MONTHLY_TON', '52.0')) # ~$129.99 (50% off)
        }
    }
    
    # Admin Configuration
    ADMIN_USER_IDS = [int(x) for x in os.getenv('ADMIN_USER_IDS', '377917978').split(',')]
    
    # Free Trial Settings
    FREE_TRIAL_MESSAGES = int(os.getenv('FREE_TRIAL_MESSAGES', '50'))
    FREE_TRIAL_DAYS = int(os.getenv('FREE_TRIAL_DAYS', '7'))
    
    # Payment Bonuses
    TON_BONUS_PERCENT = int(os.getenv('TON_BONUS_PERCENT', '5'))  # 5% extra content for TON payments
    WEEKLY_DISCOUNT = int(os.getenv('WEEKLY_DISCOUNT', '20'))      # 20% off weekly plans
    MONTHLY_DISCOUNT = int(os.getenv('MONTHLY_DISCOUNT', '50'))    # 50% off monthly plans
    
    # Message Limits
    MESSAGE_LIMITS = {
        'free_trial': FREE_TRIAL_MESSAGES,
        'premium': int(os.getenv('PREMIUM_MESSAGE_LIMIT', '500')),
        'vip': int(os.getenv('VIP_MESSAGE_LIMIT', '2000')),
        'ultimate': int(os.getenv('ULTIMATE_MESSAGE_LIMIT', '10000'))
    }
    
    # Content Settings
    EXPLICIT_CONTENT_ENABLED = os.getenv('EXPLICIT_CONTENT_ENABLED', 'true').lower() == 'true'
    CONVERSION_MESSAGES_ENABLED = os.getenv('CONVERSION_MESSAGES_ENABLED', 'true').lower() == 'true'
    UPSELL_FREQUENCY = float(os.getenv('UPSELL_FREQUENCY', '0.3'))
    
    # Analytics and Tracking
    REVENUE_TRACKING_ENABLED = os.getenv('REVENUE_TRACKING_ENABLED', 'true').lower() == 'true'
    CACHE_ANALYTICS_ENABLED = os.getenv('CACHE_ANALYTICS_ENABLED', 'true').lower() == 'true'
    USER_BEHAVIOR_TRACKING = os.getenv('USER_BEHAVIOR_TRACKING', 'true').lower() == 'true'
    
    # Conversion Messaging (Russian)
    CONVERSION_MESSAGES = {
        'trial_ending': "🚨 Ваш пробный период скоро закончится! Апгрейд для продолжения: /payment 🔥",
        'limit_50': "📊 Половина сообщений использована! Апгрейд для безлимитного доступа: /payment ⭐",
        'limit_80': "⚠️ 80% сообщений использовано! Не дай себе заблокироваться - апгрейд: /payment 💎",
        'limit_95': "🚨 ПОСЛЕДНИЕ 5% СООБЩЕНИЙ! Апгрейд СЕЙЧАС: /payment 🚨",
        'limit_reached': "🚫 Лимит сообщений достигнут! Апгрейд сейчас: /payment 💰",
        'expired': "⏰ Подписка истекла! Продлить для продолжения: /payment 🔄"
    }
    
    # Revenue Targets (for analytics)
    DAILY_REVENUE_TARGET = float(os.getenv('DAILY_REVENUE_TARGET', '100.0'))
    MONTHLY_REVENUE_TARGET = float(os.getenv('MONTHLY_REVENUE_TARGET', '3000.0'))
    CONVERSION_RATE_TARGET = float(os.getenv('CONVERSION_RATE_TARGET', '15.0'))  # 15%
    
    # Performance Metrics
    TARGET_CACHE_HIT_RATE = float(os.getenv('TARGET_CACHE_HIT_RATE', '80.0'))  # 80%
    TARGET_COST_REDUCTION = float(os.getenv('TARGET_COST_REDUCTION', '80.0'))  # 80%
    
    # Payment Method Messages
    PAYMENT_MESSAGES = {
        'stars_advantage': """
⭐ **TELEGRAM STARS ПРЕИМУЩЕСТВА:**
• Мгновенная оплата в приложении
• Никаких внешних приложений
• Безопасный официальный метод
• Немедленная активация
        """,
        'ton_advantage': """
💎 **TON КРИПТОВАЛЮТА ПРЕИМУЩЕСТВА:**
• Децентрализованные и приватные платежи
• Нативный блокчейн Telegram
• Быстрые транзакции (2-5 секунд)  
• Низкие комиссии (~0.01 TON)
• Дополнительные 5% бонус контента
        """
    }
    
    @classmethod
    def get_stars_price(cls, tier: str, duration: str) -> int:
        """Get Telegram Stars price for tier and duration"""
        return cls.STARS_PRICING[tier][duration]
    
    @classmethod
    def get_ton_price(cls, tier: str, duration: str) -> float:
        """Get TON price for tier and duration"""
        return cls.TON_PRICING[tier][duration]
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in cls.ADMIN_USER_IDS
    
    @classmethod
    def get_message_limit(cls, tier: str) -> int:
        """Get message limit for tier"""
        return cls.MESSAGE_LIMITS.get(tier, cls.FREE_TRIAL_MESSAGES)
    
    @classmethod
    def format_stars_pricing(cls) -> str:
        """Format Telegram Stars pricing for display"""
        pricing_text = "⭐ **TELEGRAM STARS PRICING:**\n\n"
        
        tier_names = {"premium": "⭐ PREMIUM", "vip": "💎 VIP", "ultimate": "👑 ULTIMATE"}
        
        for tier, prices in cls.STARS_PRICING.items():
            pricing_text += f"**{tier_names[tier]}**\n"
            pricing_text += f"• Daily: ⭐{prices['daily']} Stars\n"
            pricing_text += f"• Weekly: ⭐{prices['weekly']} Stars ({cls.WEEKLY_DISCOUNT}% OFF)\n"
            pricing_text += f"• Monthly: ⭐{prices['monthly']} Stars ({cls.MONTHLY_DISCOUNT}% OFF)\n"
            pricing_text += f"• Messages: {cls.MESSAGE_LIMITS[tier]:,}/period\n\n"
        
        return pricing_text
    
    @classmethod
    def format_ton_pricing(cls) -> str:
        """Format TON pricing for display"""
        pricing_text = "💎 **TON CRYPTO PRICING:**\n\n"
        
        tier_names = {"premium": "⭐ PREMIUM", "vip": "💎 VIP", "ultimate": "👑 ULTIMATE"}
        
        for tier, prices in cls.TON_PRICING.items():
            pricing_text += f"**{tier_names[tier]}**\n"
            pricing_text += f"• Daily: {prices['daily']} TON\n"
            pricing_text += f"• Weekly: {prices['weekly']} TON ({cls.WEEKLY_DISCOUNT}% OFF)\n"
            pricing_text += f"• Monthly: {prices['monthly']} TON ({cls.MONTHLY_DISCOUNT}% OFF)\n\n"
        
        return pricing_text

# Export config instance
config = MonetizationConfig() 