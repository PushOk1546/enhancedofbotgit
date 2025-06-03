"""
Telegram Stars and TON Payment System - Monetization Focus
Handles Telegram Stars and TON payments for maximum conversion
"""

import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from premium_system import premium_manager, SubscriptionTier

class TelegramPaymentHandler:
    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot
        self.revenue_file = "daily_revenue.json"
        
        # TON wallet address provided by user
        self.ton_wallet = "UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB"
        
        # Telegram Stars pricing (1 Star = ~$0.01-0.02 USD)
        # Converted from USD pricing to Stars
        self.stars_pricing = {
            "premium": {
                "daily": 150,    # ~$2.99 -> 150 Stars
                "weekly": 750,   # ~$14.99 -> 750 Stars  
                "monthly": 2000  # ~$39.99 -> 2000 Stars
            },
            "vip": {
                "daily": 250,    # ~$4.99 -> 250 Stars
                "weekly": 1250,  # ~$24.99 -> 1250 Stars
                "monthly": 3500  # ~$69.99 -> 3500 Stars
            },
            "ultimate": {
                "daily": 500,    # ~$9.99 -> 500 Stars
                "weekly": 2500,  # ~$49.99 -> 2500 Stars
                "monthly": 6500  # ~$129.99 -> 6500 Stars
            }
        }
        
        # TON pricing (converted from USD, approximately)
        self.ton_pricing = {
            "premium": {
                "daily": 1.2,     # ~$2.99 -> 1.2 TON
                "weekly": 6.0,    # ~$14.99 -> 6.0 TON
                "monthly": 16.0   # ~$39.99 -> 16.0 TON
            },
            "vip": {
                "daily": 2.0,     # ~$4.99 -> 2.0 TON
                "weekly": 10.0,   # ~$24.99 -> 10.0 TON
                "monthly": 28.0   # ~$69.99 -> 28.0 TON
            },
            "ultimate": {
                "daily": 4.0,     # ~$9.99 -> 4.0 TON
                "weekly": 20.0,   # ~$49.99 -> 20.0 TON
                "monthly": 52.0   # ~$129.99 -> 52.0 TON
            }
        }

    def setup_payment_commands(self):
        """Setup all payment-related command handlers"""
        
        @self.bot.message_handler(commands=['payment', 'pay', 'upgrade'])
        def handle_payment_command(message):
            self.show_payment_options(message)
        
        @self.bot.message_handler(commands=['prices', 'pricing'])
        def handle_pricing_command(message):
            self.show_pricing(message)
        
        @self.bot.message_handler(commands=['revenue', 'earnings'])
        def handle_revenue_command(message):
            if self.is_admin(message.from_user.id):
                self.show_revenue_stats(message)
            else:
                self.bot.reply_to(message, "❌ Admin access required")
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('payment_'))
        def handle_payment_callback(call):
            self.process_payment_callback(call)
        
        # Handle Telegram Stars payments
        @self.bot.pre_checkout_query_handler(func=lambda query: True)
        def handle_pre_checkout(pre_checkout_query):
            self.handle_stars_pre_checkout(pre_checkout_query)
        
        @self.bot.message_handler(content_types=['successful_payment'])
        def handle_successful_payment(message):
            self.handle_stars_success(message)

    def show_payment_options(self, message):
        """Show payment options with upgrade tiers"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        # Create payment options keyboard
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # Show available upgrades based on current tier
        if user_sub.tier == SubscriptionTier.FREE_TRIAL:
            markup.add(
                types.InlineKeyboardButton("⭐ PREMIUM (⭐150)", callback_data="payment_premium_daily_stars"),
                types.InlineKeyboardButton("💎 VIP (⭐250)", callback_data="payment_vip_daily_stars")
            )
            markup.add(
                types.InlineKeyboardButton("👑 ULTIMATE (⭐500)", callback_data="payment_ultimate_daily_stars")
            )
        elif user_sub.tier == SubscriptionTier.PREMIUM:
            markup.add(
                types.InlineKeyboardButton("💎 VIP (⭐250)", callback_data="payment_vip_daily_stars"),
                types.InlineKeyboardButton("👑 ULTIMATE (⭐500)", callback_data="payment_ultimate_daily_stars")
            )
        elif user_sub.tier == SubscriptionTier.VIP:
            markup.add(
                types.InlineKeyboardButton("👑 ULTIMATE (⭐500)", callback_data="payment_ultimate_daily_stars")
            )
        
        # Payment method selection
        markup.add(
            types.InlineKeyboardButton("⭐ Telegram Stars", callback_data="payment_method_stars"),
            types.InlineKeyboardButton("💎 TON Crypto", callback_data="payment_method_ton")
        )
        
        # Weekly/Monthly discounts
        markup.add(
            types.InlineKeyboardButton("📅 Weekly Plans (20% OFF)", callback_data="payment_weekly_options"),
            types.InlineKeyboardButton("📅 Monthly Plans (50% OFF)", callback_data="payment_monthly_options")
        )
        
        status_msg = premium_manager.get_user_status_message(message.from_user.id)
        
        payment_msg = f"""
🔥 **PREMIUM UPGRADE** 🔥

{status_msg}

💰 **EXCLUSIVE BENEFITS:**
⭐ **PREMIUM**: 500 messages + explicit content
💎 **VIP**: 2000 messages + fetish content + priority  
👑 **ULTIMATE**: 10000 messages + extreme content + custom requests

🎁 **PAYMENT OPTIONS:**
⭐ **Telegram Stars**: Instant payment in-app
💎 **TON Crypto**: Decentralized, private payments
📱 **Weekly/Monthly**: Big discounts available!

✨ **SPECIAL OFFERS:**
• Weekly subscriptions: 20% OFF
• Monthly subscriptions: 50% OFF  
• TON payments: Extra 5% bonus content

Choose your upgrade below:
        """
        
        self.bot.send_message(message.chat.id, payment_msg, reply_markup=markup, parse_mode='Markdown')

    def show_pricing(self, message):
        """Show detailed pricing information"""
        pricing_msg = """
💰 **PREMIUM PRICING** 💰

⭐ **TELEGRAM STARS PRICING:**

**⭐ PREMIUM**
• Daily: ⭐150 Stars
• Weekly: ⭐750 Stars (20% OFF)
• Monthly: ⭐2000 Stars (50% OFF)
• Messages: 500/period

**💎 VIP**  
• Daily: ⭐250 Stars
• Weekly: ⭐1250 Stars (20% OFF)
• Monthly: ⭐3500 Stars (50% OFF)
• Messages: 2,000/period

**👑 ULTIMATE**
• Daily: ⭐500 Stars  
• Weekly: ⭐2500 Stars (20% OFF)
• Monthly: ⭐6500 Stars (50% OFF)
• Messages: 10,000/period

💎 **TON CRYPTO PRICING:**

**⭐ PREMIUM**
• Daily: 1.2 TON
• Weekly: 6.0 TON (20% OFF)
• Monthly: 16.0 TON (50% OFF)

**💎 VIP**
• Daily: 2.0 TON
• Weekly: 10.0 TON (20% OFF)  
• Monthly: 28.0 TON (50% OFF)

**👑 ULTIMATE**
• Daily: 4.0 TON
• Weekly: 20.0 TON (20% OFF)
• Monthly: 52.0 TON (50% OFF)

🎁 **FREE TRIAL**: 50 messages for 7 days
⚡ **ACTIVATION**: Instant after payment
🔐 **SECURE**: Built into Telegram
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Upgrade Now", callback_data="payment_upgrade"))
        
        self.bot.send_message(message.chat.id, pricing_msg, reply_markup=markup, parse_mode='Markdown')

    def process_payment_callback(self, call):
        """Process payment callback actions"""
        data = call.data.replace('payment_', '')
        
        if data == 'method_stars':
            self.show_stars_payment_options(call)
        elif data == 'method_ton':
            self.show_ton_payment_options(call)
        elif data == 'weekly_options':
            self.show_weekly_plans(call)
        elif data == 'monthly_options':
            self.show_monthly_plans(call)
        elif data.endswith('_stars'):
            self.initiate_stars_payment(call, data)
        elif data.endswith('_ton'):
            self.show_ton_payment_details(call, data)
        elif data == 'upgrade':
            self.show_payment_options(call.message)

    def show_stars_payment_options(self, call):
        """Show Telegram Stars payment options"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        markup.add(
            types.InlineKeyboardButton("⭐ PREMIUM Daily - ⭐150", callback_data="payment_premium_daily_stars"),
            types.InlineKeyboardButton("💎 VIP Daily - ⭐250", callback_data="payment_vip_daily_stars"),
            types.InlineKeyboardButton("👑 ULTIMATE Daily - ⭐500", callback_data="payment_ultimate_daily_stars")
        )
        
        markup.add(
            types.InlineKeyboardButton("📅 Weekly Plans (20% OFF)", callback_data="payment_weekly_stars"),
            types.InlineKeyboardButton("📅 Monthly Plans (50% OFF)", callback_data="payment_monthly_stars")
        )
        
        markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="payment_upgrade"))
        
        stars_msg = """
⭐ **TELEGRAM STARS PAYMENT** ⭐

💰 **ADVANTAGES:**
• Instant payment within Telegram
• No external apps needed
• Secure and official payment method
• Immediate activation after payment

✨ **HOW IT WORKS:**
1. Select your subscription tier
2. Pay with Telegram Stars
3. Access activated instantly!

🎁 **BONUS:**
• Stars payments get priority support
• Exclusive Stars-only content previews
• No hidden fees or charges

Choose your subscription:
        """
        
        self.bot.edit_message_text(stars_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def show_ton_payment_options(self, call):
        """Show TON cryptocurrency payment options"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        markup.add(
            types.InlineKeyboardButton("⭐ PREMIUM Daily - 1.2 TON", callback_data="payment_premium_daily_ton"),
            types.InlineKeyboardButton("💎 VIP Daily - 2.0 TON", callback_data="payment_vip_daily_ton"),
            types.InlineKeyboardButton("👑 ULTIMATE Daily - 4.0 TON", callback_data="payment_ultimate_daily_ton")
        )
        
        markup.add(
            types.InlineKeyboardButton("📅 Weekly Plans (20% OFF)", callback_data="payment_weekly_ton"),
            types.InlineKeyboardButton("📅 Monthly Plans (50% OFF)", callback_data="payment_monthly_ton")
        )
        
        markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="payment_upgrade"))
        
        ton_msg = """
💎 **TON CRYPTOCURRENCY PAYMENT** 💎

💰 **ADVANTAGES:**
• Decentralized and private
• Native Telegram blockchain
• Fast transactions (2-5 seconds)
• Low fees (~0.01 TON)
• Extra 5% bonus content

🔐 **TON WALLET ADDRESS:**
`UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB`

📱 **HOW TO PAY:**
1. Open TON Wallet in Telegram (@wallet)
2. Send exact amount to address above
3. Include your username in comment
4. Send screenshot for verification

Choose your subscription:
        """
        
        self.bot.edit_message_text(ton_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def initiate_stars_payment(self, call, payment_data):
        """Initiate Telegram Stars payment"""
        # Parse payment data
        parts = payment_data.replace('_stars', '').split('_')
        tier = parts[0]  # premium, vip, ultimate
        duration = parts[1]  # daily, weekly, monthly
        
        # Get price in stars
        stars_amount = self.stars_pricing[tier][duration]
        
        # Create invoice
        tier_names = {"premium": "⭐ PREMIUM", "vip": "💎 VIP", "ultimate": "👑 ULTIMATE"}
        duration_names = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}
        
        title = f"{tier_names[tier]} {duration_names[duration]} Subscription"
        description = f"Premium adult chat access - {tier.upper()} tier for {duration} period"
        
        # Create invoice
        prices = [types.LabeledPrice(label=title, amount=stars_amount)]
        
        self.bot.send_invoice(
            call.message.chat.id,
            title=title,
            description=description,
            payload=f"{tier}_{duration}_{call.from_user.id}",
            provider_token="",  # Empty for Stars
            currency="XTR",  # Telegram Stars currency
            prices=prices,
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            send_phone_number_to_provider=False,
            send_email_to_provider=False,
            is_flexible=False
        )

    def show_ton_payment_details(self, call, payment_data):
        """Show detailed TON payment instructions"""
        # Parse payment data
        parts = payment_data.replace('_ton', '').split('_')
        tier = parts[0]
        duration = parts[1]
        
        ton_amount = self.ton_pricing[tier][duration]
        
        tier_names = {"premium": "⭐ PREMIUM", "vip": "💎 VIP", "ultimate": "👑 ULTIMATE"}
        duration_names = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}
        
        payment_msg = f"""
💎 **TON PAYMENT CONFIRMATION** 💎

**Subscription:** {tier_names[tier]} {duration_names[duration]}
**Amount:** {ton_amount} TON

💰 **TON WALLET ADDRESS:**
`UQA4rDEmGdIYKcrjEDwfZGLnISYd-gCYLEpcbSdwcuAW_FXB`

📋 **PAYMENT INSTRUCTIONS:**
1. Open @wallet bot in Telegram
2. Send exactly {ton_amount} TON to address above
3. Add comment: "Premium {tier} {duration} @{call.from_user.username}"
4. Send transaction screenshot here
5. Account upgraded within 5 minutes!

⚠️ **IMPORTANT:**
• Send EXACT amount: {ton_amount} TON
• Include your username in comment
• Use @wallet bot for best compatibility
• Transaction usually takes 2-5 seconds

🎁 **BONUS CONTENT:**
TON payments get 5% extra exclusive content!
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("💰 I Sent Payment", callback_data="payment_ton_sent"),
            types.InlineKeyboardButton("❓ Need Help", callback_data="payment_ton_help")
        )
        
        self.bot.edit_message_text(payment_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

    def handle_stars_pre_checkout(self, pre_checkout_query):
        """Handle Telegram Stars pre-checkout query"""
        self.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    def handle_stars_success(self, message):
        """Handle successful Telegram Stars payment"""
        # Parse payment info
        payment_info = message.successful_payment
        payload_parts = payment_info.invoice_payload.split('_')
        
        tier = payload_parts[0]
        duration = payload_parts[1]
        user_id = int(payload_parts[2])
        
        # Map tier string to enum
        tier_mapping = {
            "premium": SubscriptionTier.PREMIUM,
            "vip": SubscriptionTier.VIP,
            "ultimate": SubscriptionTier.ULTIMATE
        }
        
        # Map duration to days
        duration_days = {"daily": 1, "weekly": 7, "monthly": 30}
        
        # Upgrade subscription
        success = premium_manager.upgrade_subscription(
            user_id=user_id,
            tier=tier_mapping[tier],
            duration_days=duration_days[duration],
            payment_amount=payment_info.total_amount / 100,  # Convert from stars
            payment_method="telegram_stars",
            transaction_id=payment_info.telegram_payment_charge_id
        )
        
        if success:
            success_msg = f"""
🎉 **PAYMENT SUCCESSFUL!** 🎉

✅ **SUBSCRIPTION ACTIVATED:**
• Tier: {tier.upper()}
• Duration: {duration_days[duration]} days
• Messages: {premium_manager.message_limits[tier_mapping[tier]]}

🔥 **YOU NOW HAVE ACCESS TO:**
• Explicit adult content
• Premium chat features
• Priority support
• Exclusive content library

Ready to have some fun? 😈
Start chatting now!
            """
            
            self.bot.send_message(user_id, success_msg, parse_mode='Markdown')
        else:
            self.bot.send_message(user_id, "❌ Payment processed but upgrade failed. Contact support.")

    def show_revenue_stats(self, message):
        """Show revenue statistics for admin"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_revenue = premium_manager.get_daily_revenue(today)
        
        # Calculate weekly and monthly revenue
        weekly_revenue = self.calculate_period_revenue(7)
        monthly_revenue = self.calculate_period_revenue(30)
        
        # Get subscriber stats
        total_users = len(premium_manager.users)
        premium_users = sum(1 for u in premium_manager.users.values() if u.tier != SubscriptionTier.FREE_TRIAL)
        
        revenue_msg = f"""
📊 **REVENUE DASHBOARD** 📊

💰 **TODAY ({today}):**
• Revenue: ${today_revenue['total_revenue']:.2f}
• New Subscribers: {today_revenue['new_subscribers']}
• Payments: {len(today_revenue['payments'])}

📈 **WEEKLY STATS:**
• Total Revenue: ${weekly_revenue:.2f}
• Avg Daily: ${weekly_revenue/7:.2f}

📅 **MONTHLY STATS:**
• Total Revenue: ${monthly_revenue:.2f}
• Avg Daily: ${monthly_revenue/30:.2f}

👥 **SUBSCRIBER STATS:**
• Total Users: {total_users}
• Premium Users: {premium_users}
• Conversion Rate: {(premium_users/total_users*100) if total_users > 0 else 0:.1f}%

⭐ **PAYMENT METHODS:**
• Telegram Stars: High conversion
• TON Crypto: Premium users preferred

🎯 **PROJECTIONS:**
• Weekly: ${weekly_revenue * 4:.2f}
• Monthly: ${monthly_revenue:.2f}
• Yearly: ${monthly_revenue * 12:.2f}
        """
        
        self.bot.send_message(message.chat.id, revenue_msg, parse_mode='Markdown')

    def calculate_period_revenue(self, days: int) -> float:
        """Calculate revenue for specified period"""
        total_revenue = 0.0
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_revenue = premium_manager.get_daily_revenue(date)
            total_revenue += day_revenue['total_revenue']
        
        return total_revenue

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        # Add your admin user IDs here
        admin_ids = [377917978]  # Updated with actual admin ID
        return user_id in admin_ids

# Usage example for bot integration
def setup_telegram_payment_system(bot: telebot.TeleBot):
    """Setup Telegram payment system with the bot"""
    payment_handler = TelegramPaymentHandler(bot)
    payment_handler.setup_payment_commands()
    return payment_handler 