"""
Payment Commands and Revenue Tracking - Monetization Focus
Handles payment processing, crypto instructions, and revenue analytics
"""

import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from premium_system import premium_manager, SubscriptionTier

class PaymentHandler:
    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot
        self.revenue_file = "daily_revenue.json"
        
        # Crypto wallet addresses (REPLACE WITH YOUR REAL ADDRESSES)
        self.crypto_wallets = {
            "bitcoin": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",  # Example Bitcoin address
            "ethereum": "0x742f35Cc6Cc4F9E7C8E3C9b24b8f4b345E4Fcd4E",  # Example Ethereum address
            "usdt": "TQn9Y2khEsLMJ2hJZAz1dqwMN4UfE4B4bA",  # Example USDT (TRC20) address
            "bnb": "bnb1xy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"   # Example BNB address
        }
        
        # Payment processing URLs
        self.payment_urls = {
            "paypal": "https://www.paypal.me/yourusername",
            "cashapp": "$yourusername",
            "venmo": "@yourusername"
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

    def show_payment_options(self, message):
        """Show payment options with upgrade tiers"""
        user_sub = premium_manager.get_user_subscription(message.from_user.id)
        
        # Create payment options keyboard
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # Tier upgrade buttons
        if user_sub.tier == SubscriptionTier.FREE_TRIAL:
            markup.add(
                types.InlineKeyboardButton("⭐ PREMIUM - $2.99/day", callback_data="payment_premium_daily"),
                types.InlineKeyboardButton("💎 VIP - $4.99/day", callback_data="payment_vip_daily")
            )
            markup.add(
                types.InlineKeyboardButton("👑 ULTIMATE - $9.99/day", callback_data="payment_ultimate_daily")
            )
        elif user_sub.tier == SubscriptionTier.PREMIUM:
            markup.add(
                types.InlineKeyboardButton("💎 Upgrade to VIP - $4.99/day", callback_data="payment_vip_daily"),
                types.InlineKeyboardButton("👑 Upgrade to ULTIMATE - $9.99/day", callback_data="payment_ultimate_daily")
            )
        elif user_sub.tier == SubscriptionTier.VIP:
            markup.add(
                types.InlineKeyboardButton("👑 Upgrade to ULTIMATE - $9.99/day", callback_data="payment_ultimate_daily")
            )
        
        # Weekly/Monthly options
        markup.add(
            types.InlineKeyboardButton("📅 Weekly Plans", callback_data="payment_weekly"),
            types.InlineKeyboardButton("📅 Monthly Plans", callback_data="payment_monthly")
        )
        
        # Payment methods
        markup.add(
            types.InlineKeyboardButton("₿ Crypto Payment", callback_data="payment_crypto"),
            types.InlineKeyboardButton("💳 PayPal/Card", callback_data="payment_traditional")
        )
        
        status_msg = premium_manager.get_user_status_message(message.from_user.id)
        
        payment_msg = f"""
🔥 **PREMIUM UPGRADE** 🔥

{status_msg}

💰 **EXCLUSIVE BENEFITS:**
⭐ **PREMIUM**: 500 messages/period + explicit content
💎 **VIP**: 2000 messages + fetish content + priority
👑 **ULTIMATE**: 10000 messages + extreme content + custom requests

🎁 **LIMITED TIME OFFERS:**
• Weekly plans: 30% OFF
• Monthly plans: 50% OFF
• Lifetime deals available!

💳 **PAYMENT METHODS:**
• Bitcoin, Ethereum, USDT, BNB
• PayPal, Credit Card, Cash App
• Instant activation guaranteed!

Choose your upgrade below:
        """
        
        self.bot.send_message(message.chat.id, payment_msg, reply_markup=markup, parse_mode='Markdown')

    def show_pricing(self, message):
        """Show detailed pricing information"""
        pricing_msg = premium_manager.get_pricing_message()
        
        # Add special offers
        pricing_msg += "\n\n🔥 **SPECIAL OFFERS** 🔥\n"
        pricing_msg += "• First time buyers: 20% OFF\n"
        pricing_msg += "• Weekly plans: 30% OFF\n"
        pricing_msg += "• Monthly plans: 50% OFF\n"
        pricing_msg += "• Lifetime VIP: $199 (90% OFF)\n\n"
        pricing_msg += "💌 Message me after payment for instant activation!"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Upgrade Now", callback_data="payment_upgrade"))
        
        self.bot.send_message(message.chat.id, pricing_msg, reply_markup=markup, parse_mode='Markdown')

    def process_payment_callback(self, call):
        """Process payment callback actions"""
        data = call.data.replace('payment_', '')
        
        if data == 'crypto':
            self.show_crypto_payment(call)
        elif data == 'traditional':
            self.show_traditional_payment(call)
        elif data == 'weekly':
            self.show_weekly_plans(call)
        elif data == 'monthly':
            self.show_monthly_plans(call)
        elif data.startswith('confirm_'):
            self.show_payment_confirmation(call, data)
        elif data == 'upgrade':
            self.show_payment_options(call.message)

    def show_crypto_payment(self, call):
        """Show cryptocurrency payment options"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            types.InlineKeyboardButton("₿ Bitcoin", callback_data="payment_confirm_bitcoin"),
            types.InlineKeyboardButton("🔷 Ethereum", callback_data="payment_confirm_ethereum")
        )
        markup.add(
            types.InlineKeyboardButton("💎 USDT", callback_data="payment_confirm_usdt"),
            types.InlineKeyboardButton("🟡 BNB", callback_data="payment_confirm_bnb")
        )
        markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="payment_upgrade"))
        
        crypto_msg = """
🪙 **CRYPTOCURRENCY PAYMENT** 🪙

💰 **ADVANTAGES:**
• 10% discount on all crypto payments
• Instant activation (no waiting)
• Complete privacy and anonymity
• No chargebacks or reversals

🔐 **ACCEPTED CRYPTOCURRENCIES:**
₿ Bitcoin (BTC)
🔷 Ethereum (ETH) 
💎 USDT (Tether)
🟡 BNB (Binance Coin)

⚡ Choose your preferred cryptocurrency:
        """
        
        self.bot.edit_message_text(crypto_msg, call.message.chat.id, call.message.message_id, 
                                 reply_markup=markup, parse_mode='Markdown')

    def show_payment_confirmation(self, call, payment_data):
        """Show payment confirmation with wallet address"""
        crypto_type = payment_data.replace('confirm_', '')
        
        if crypto_type in self.crypto_wallets:
            wallet_address = self.crypto_wallets[crypto_type]
            
            # Calculate discounted prices (10% off for crypto)
            prices = {
                "premium_daily": 2.69,  # $2.99 - 10%
                "vip_daily": 4.49,     # $4.99 - 10%
                "ultimate_daily": 8.99  # $9.99 - 10%
            }
            
            confirmation_msg = f"""
💳 **PAYMENT CONFIRMATION** 💳

**Cryptocurrency:** {crypto_type.upper()}
**Wallet Address:**
`{wallet_address}`

💰 **PRICING (10% CRYPTO DISCOUNT):**
⭐ PREMIUM Daily: ${prices['premium_daily']}
💎 VIP Daily: ${prices['vip_daily']} 
👑 ULTIMATE Daily: ${prices['ultimate_daily']}

📋 **PAYMENT INSTRUCTIONS:**
1. Send exact amount to the wallet address above
2. Take screenshot of transaction
3. Send screenshot to this chat
4. Account upgraded within 5 minutes!

⚠️ **IMPORTANT:**
• Send EXACT amount shown
• Include transaction ID in message
• Don't send from exchange (use personal wallet)

🎁 Your access will be activated immediately after confirmation!
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("💰 I Sent Payment", callback_data="payment_sent"),
                types.InlineKeyboardButton("❓ Need Help", callback_data="payment_help")
            )
            
            self.bot.edit_message_text(confirmation_msg, call.message.chat.id, call.message.message_id,
                                     reply_markup=markup, parse_mode='Markdown')

    def show_traditional_payment(self, call):
        """Show traditional payment options"""
        traditional_msg = f"""
💳 **TRADITIONAL PAYMENT** 💳

💰 **PAYMENT OPTIONS:**

**PayPal:**
Send to: {self.payment_urls['paypal']}

**Cash App:**
Send to: {self.payment_urls['cashapp']}

**Venmo:**
Send to: {self.payment_urls['venmo']}

📋 **INSTRUCTIONS:**
1. Send payment using any method above
2. Include your Telegram username in payment note
3. Send confirmation screenshot here
4. Access activated within 30 minutes!

⭐ **PREMIUM DAILY:** $2.99
💎 **VIP DAILY:** $4.99
👑 **ULTIMATE DAILY:** $9.99

🔄 Crypto payments get 10% discount!
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("💰 I Sent Payment", callback_data="payment_sent"),
            types.InlineKeyboardButton("⬅️ Back to Crypto", callback_data="payment_crypto")
        )
        
        self.bot.edit_message_text(traditional_msg, call.message.chat.id, call.message.message_id,
                                 reply_markup=markup, parse_mode='Markdown')

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
• Conversion Rate: {(premium_users/total_users*100):.1f}%

💎 **TOP EARNERS:**
{self.get_top_revenue_days()}

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

    def get_top_revenue_days(self) -> str:
        """Get top revenue generating days"""
        revenue_data = {}
        if os.path.exists(premium_manager.revenue_file):
            with open(premium_manager.revenue_file, 'r', encoding='utf-8') as f:
                revenue_data = json.load(f)
        
        # Sort by revenue
        sorted_days = sorted(revenue_data.items(), key=lambda x: x[1]['total_revenue'], reverse=True)
        
        top_days = ""
        for i, (date, data) in enumerate(sorted_days[:3]):
            top_days += f"{i+1}. {date}: ${data['total_revenue']:.2f}\n"
        
        return top_days if top_days else "No revenue data yet"

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        # Add your admin user IDs here
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids

    def record_payment_attempt(self, user_id: int, amount: float, method: str):
        """Record payment attempt for analytics"""
        attempts_file = "payment_attempts.json"
        
        attempt_data = {
            "user_id": user_id,
            "amount": amount,
            "method": method,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        attempts = []
        if os.path.exists(attempts_file):
            with open(attempts_file, 'r', encoding='utf-8') as f:
                attempts = json.load(f)
        
        attempts.append(attempt_data)
        
        with open(attempts_file, 'w', encoding='utf-8') as f:
            json.dump(attempts, f, ensure_ascii=False, indent=2)

# Usage example for bot integration
def setup_payment_system(bot: telebot.TeleBot):
    """Setup payment system with the bot"""
    payment_handler = PaymentHandler(bot)
    payment_handler.setup_payment_commands()
    return payment_handler 