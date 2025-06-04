#!/usr/bin/env python3
"""
🔔 СИСТЕМА УВЕДОМЛЕНИЙ И АЛЕРТОВ 🔔
Отправка критических уведомлений администраторам
Поддержка Telegram, Email, Webhook уведомлений
"""

import os
import json
import time
import asyncio
import smtplib
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from dataclasses import dataclass
from enum import Enum
import threading
from queue import Queue

class AlertLevel(Enum):
    """Уровни алертов"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class NotificationType(Enum):
    """Типы уведомлений"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"

@dataclass
class Alert:
    """Структура алерта"""
    id: str
    timestamp: str
    level: AlertLevel
    title: str
    message: str
    source: str
    details: Dict[str, Any] = None
    resolved: bool = False

@dataclass
class NotificationChannel:
    """Канал уведомлений"""
    type: NotificationType
    config: Dict[str, Any]
    enabled: bool = True
    min_level: AlertLevel = AlertLevel.WARNING

class NotificationSystem:
    def __init__(self):
        self.alert_queue = Queue()
        self.active_alerts = {}
        self.notification_channels = []
        self.rate_limits = {}
        self.alert_history = []
        
        # Настройка каналов уведомлений
        self.setup_notification_channels()
        
        # Запуск обработчика уведомлений
        self.running = True
        self.notification_thread = threading.Thread(target=self.process_notifications)
        self.notification_thread.daemon = True
        self.notification_thread.start()
        
        print("🔔 Notification System: АКТИВИРОВАН")

    def setup_notification_channels(self):
        """Настройка каналов уведомлений"""
        
        # Telegram канал для админов
        if os.getenv('BOT_TOKEN') and os.getenv('ADMIN_USER_IDS'):
            self.notification_channels.append(NotificationChannel(
                type=NotificationType.TELEGRAM,
                config={
                    'bot_token': os.getenv('BOT_TOKEN'),
                    'admin_ids': [int(x) for x in os.getenv('ADMIN_USER_IDS', '').split(',') if x]
                },
                min_level=AlertLevel.WARNING
            ))
        
        # Email канал
        if os.getenv('SMTP_EMAIL') and os.getenv('SMTP_PASSWORD'):
            self.notification_channels.append(NotificationChannel(
                type=NotificationType.EMAIL,
                config={
                    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                    'email': os.getenv('SMTP_EMAIL'),
                    'password': os.getenv('SMTP_PASSWORD'),
                    'recipients': os.getenv('ADMIN_EMAILS', '').split(',')
                },
                min_level=AlertLevel.CRITICAL
            ))
        
        # Webhook канал (например, Slack, Discord)
        if os.getenv('WEBHOOK_URL'):
            self.notification_channels.append(NotificationChannel(
                type=NotificationType.WEBHOOK,
                config={
                    'url': os.getenv('WEBHOOK_URL'),
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'}
                },
                min_level=AlertLevel.WARNING
            ))

    def send_alert(self, level: AlertLevel, title: str, message: str, 
                   source: str = "system", details: Dict[str, Any] = None) -> str:
        """Отправка алерта"""
        alert_id = f"{int(time.time())}_{len(self.active_alerts)}"
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now().isoformat(),
            level=level,
            title=title,
            message=message,
            source=source,
            details=details or {}
        )
        
        # Проверка дублирования алертов
        if not self.is_duplicate_alert(alert):
            self.alert_queue.put(alert)
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Ограничиваем историю
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-500:]
        
        return alert_id

    def process_notifications(self):
        """Обработка очереди уведомлений"""
        while self.running:
            try:
                if not self.alert_queue.empty():
                    alert = self.alert_queue.get()
                    self.deliver_alert(alert)
                time.sleep(1)
            except Exception as e:
                print(f"❌ Notification processing error: {e}")
                time.sleep(5)

    def deliver_alert(self, alert: Alert):
        """Доставка алерта через все подходящие каналы"""
        for channel in self.notification_channels:
            if not channel.enabled:
                continue
            
            # Проверка минимального уровня
            if self.should_send_to_channel(alert, channel):
                try:
                    if channel.type == NotificationType.TELEGRAM:
                        self.send_telegram_alert(alert, channel)
                    elif channel.type == NotificationType.EMAIL:
                        self.send_email_alert(alert, channel)
                    elif channel.type == NotificationType.WEBHOOK:
                        self.send_webhook_alert(alert, channel)
                    
                    # Логируем успешную отправку
                    print(f"✅ Alert {alert.id} sent via {channel.type.value}")
                    
                except Exception as e:
                    print(f"❌ Failed to send alert via {channel.type.value}: {e}")

    def send_telegram_alert(self, alert: Alert, channel: NotificationChannel):
        """Отправка алерта через Telegram"""
        bot_token = channel.config['bot_token']
        admin_ids = channel.config['admin_ids']
        
        # Определяем эмодзи по уровню
        level_emojis = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨",
            AlertLevel.EMERGENCY: "🔥"
        }
        
        emoji = level_emojis.get(alert.level, "📢")
        
        # Форматируем сообщение
        message = f"""
{emoji} **{alert.level.value.upper()} ALERT**

📋 **{alert.title}**
💬 {alert.message}
🕐 {datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
🔍 Source: {alert.source}

🆔 Alert ID: `{alert.id}`
        """
        
        # Добавляем детали если есть
        if alert.details:
            details_text = "\n".join([f"• {k}: {v}" for k, v in alert.details.items()])
            message += f"\n\n📊 **Details:**\n{details_text}"
        
        # Отправляем всем админам
        for admin_id in admin_ids:
            if self.check_rate_limit(f"telegram_{admin_id}", alert.level):
                try:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data = {
                        'chat_id': admin_id,
                        'text': message,
                        'parse_mode': 'Markdown',
                        'disable_web_page_preview': True
                    }
                    
                    response = requests.post(url, data=data, timeout=10)
                    if response.status_code != 200:
                        print(f"❌ Telegram API error: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Telegram send error: {e}")

    def send_email_alert(self, alert: Alert, channel: NotificationChannel):
        """Отправка алерта через Email"""
        config = channel.config
        
        # Создаем сообщение
        msg = MimeMultipart()
        msg['From'] = config['email']
        msg['Subject'] = f"[{alert.level.value.upper()}] {alert.title}"
        
        # HTML тело сообщения
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert-header {{ background-color: {self.get_alert_color(alert.level)}; color: white; padding: 15px; border-radius: 5px; }}
                .alert-content {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }}
                .details {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="alert-header">
                <h2>{alert.level.value.upper()} ALERT: {alert.title}</h2>
            </div>
            <div class="alert-content">
                <p><strong>Message:</strong> {alert.message}</p>
                <p><strong>Time:</strong> {datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Source:</strong> {alert.source}</p>
                <p><strong>Alert ID:</strong> {alert.id}</p>
                
                {f'<div class="details"><h4>Details:</h4><ul>{"".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in alert.details.items()])}</ul></div>' if alert.details else ''}
            </div>
        </body>
        </html>
        """
        
        msg.attach(MimeText(html_body, 'html'))
        
        # Отправляем всем получателям
        try:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['email'], config['password'])
            
            for recipient in config['recipients']:
                if recipient and self.check_rate_limit(f"email_{recipient}", alert.level):
                    msg['To'] = recipient
                    server.send_message(msg)
                    del msg['To']
            
            server.quit()
            
        except Exception as e:
            print(f"❌ Email send error: {e}")

    def send_webhook_alert(self, alert: Alert, channel: NotificationChannel):
        """Отправка алерта через Webhook"""
        config = channel.config
        
        # Формируем payload
        payload = {
            'alert_id': alert.id,
            'timestamp': alert.timestamp,
            'level': alert.level.value,
            'title': alert.title,
            'message': alert.message,
            'source': alert.source,
            'details': alert.details
        }
        
        # Специальное форматирование для Slack
        if 'slack' in config.get('url', '').lower():
            payload = self.format_slack_message(alert)
        
        # Специальное форматирование для Discord
        elif 'discord' in config.get('url', '').lower():
            payload = self.format_discord_message(alert)
        
        try:
            response = requests.post(
                config['url'],
                json=payload,
                headers=config.get('headers', {}),
                timeout=10
            )
            
            if response.status_code not in [200, 204]:
                print(f"❌ Webhook error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Webhook send error: {e}")

    def format_slack_message(self, alert: Alert) -> Dict[str, Any]:
        """Форматирование сообщения для Slack"""
        color_map = {
            AlertLevel.INFO: "good",
            AlertLevel.WARNING: "warning", 
            AlertLevel.CRITICAL: "danger",
            AlertLevel.EMERGENCY: "danger"
        }
        
        attachment = {
            "color": color_map.get(alert.level, "warning"),
            "title": f"{alert.level.value.upper()}: {alert.title}",
            "text": alert.message,
            "fields": [
                {"title": "Source", "value": alert.source, "short": True},
                {"title": "Alert ID", "value": alert.id, "short": True},
                {"title": "Time", "value": datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S'), "short": True}
            ],
            "footer": "Bot Monitoring System",
            "ts": int(datetime.fromisoformat(alert.timestamp).timestamp())
        }
        
        if alert.details:
            for key, value in alert.details.items():
                attachment["fields"].append({
                    "title": key.title(),
                    "value": str(value),
                    "short": True
                })
        
        return {"attachments": [attachment]}

    def format_discord_message(self, alert: Alert) -> Dict[str, Any]:
        """Форматирование сообщения для Discord"""
        color_map = {
            AlertLevel.INFO: 0x3498db,      # Blue
            AlertLevel.WARNING: 0xf39c12,   # Orange
            AlertLevel.CRITICAL: 0xe74c3c,  # Red
            AlertLevel.EMERGENCY: 0x9b59b6  # Purple
        }
        
        embed = {
            "title": f"{alert.level.value.upper()}: {alert.title}",
            "description": alert.message,
            "color": color_map.get(alert.level, 0xf39c12),
            "timestamp": alert.timestamp,
            "fields": [
                {"name": "Source", "value": alert.source, "inline": True},
                {"name": "Alert ID", "value": alert.id, "inline": True}
            ],
            "footer": {"text": "Bot Monitoring System"}
        }
        
        if alert.details:
            for key, value in alert.details.items():
                embed["fields"].append({
                    "name": key.title(),
                    "value": str(value),
                    "inline": True
                })
        
        return {"embeds": [embed]}

    def should_send_to_channel(self, alert: Alert, channel: NotificationChannel) -> bool:
        """Проверка, нужно ли отправлять алерт в канал"""
        # Проверка минимального уровня
        level_values = {
            AlertLevel.INFO: 1,
            AlertLevel.WARNING: 2,
            AlertLevel.CRITICAL: 3,
            AlertLevel.EMERGENCY: 4
        }
        
        return level_values[alert.level] >= level_values[channel.min_level]

    def check_rate_limit(self, key: str, level: AlertLevel) -> bool:
        """Проверка rate limit для предотвращения спама"""
        current_time = time.time()
        
        # Лимиты по уровням (секунды)
        limits = {
            AlertLevel.INFO: 300,       # 5 минут
            AlertLevel.WARNING: 120,    # 2 минуты
            AlertLevel.CRITICAL: 60,    # 1 минута
            AlertLevel.EMERGENCY: 10    # 10 секунд
        }
        
        limit = limits.get(level, 60)
        
        if key in self.rate_limits:
            if current_time - self.rate_limits[key] < limit:
                return False
        
        self.rate_limits[key] = current_time
        return True

    def is_duplicate_alert(self, alert: Alert) -> bool:
        """Проверка на дубликат алерта"""
        # Проверяем последние алерты за 5 минут
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        for existing_alert in reversed(self.alert_history[-20:]):  # Последние 20
            if datetime.fromisoformat(existing_alert.timestamp) < cutoff_time:
                break
            
            if (existing_alert.title == alert.title and 
                existing_alert.source == alert.source and
                existing_alert.level == alert.level):
                return True
        
        return False

    def get_alert_color(self, level: AlertLevel) -> str:
        """Получение цвета для алерта"""
        colors = {
            AlertLevel.INFO: "#3498db",
            AlertLevel.WARNING: "#f39c12",
            AlertLevel.CRITICAL: "#e74c3c",
            AlertLevel.EMERGENCY: "#9b59b6"
        }
        return colors.get(level, "#95a5a6")

    def resolve_alert(self, alert_id: str):
        """Помечает алерт как решенный"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            print(f"✅ Alert {alert_id} resolved")

    def get_active_alerts(self) -> List[Alert]:
        """Получение списка активных алертов"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Статистика алертов"""
        total_alerts = len(self.alert_history)
        active_count = len(self.get_active_alerts())
        
        # Распределение по уровням
        level_counts = {}
        for alert in self.alert_history:
            level = alert.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Алерты за последний час
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert.timestamp) > hour_ago
        ]
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_count,
            'alerts_last_hour': len(recent_alerts),
            'level_distribution': level_counts,
            'channels_configured': len(self.notification_channels),
            'channels_enabled': len([c for c in self.notification_channels if c.enabled])
        }

    def test_notifications(self):
        """Тестирование системы уведомлений"""
        print("🧪 Testing notification system...")
        
        # Тестовые алерты
        test_alerts = [
            (AlertLevel.INFO, "Test Info Alert", "This is a test info message"),
            (AlertLevel.WARNING, "Test Warning Alert", "This is a test warning message"),
            (AlertLevel.CRITICAL, "Test Critical Alert", "This is a test critical message")
        ]
        
        for level, title, message in test_alerts:
            alert_id = self.send_alert(
                level=level,
                title=title,
                message=message,
                source="notification_test",
                details={"test": True, "timestamp": datetime.now().isoformat()}
            )
            print(f"✅ Test alert sent: {alert_id}")
            time.sleep(2)  # Небольшая задержка между тестами

    def shutdown(self):
        """Остановка системы уведомлений"""
        self.running = False
        print("🛑 Notification System: ОСТАНОВЛЕН")

# Глобальная система уведомлений
notification_system = NotificationSystem()

# Convenience функции для быстрой отправки алертов
def send_info_alert(title: str, message: str, source: str = "system", details: Dict[str, Any] = None):
    """Отправка информационного алерта"""
    return notification_system.send_alert(AlertLevel.INFO, title, message, source, details)

def send_warning_alert(title: str, message: str, source: str = "system", details: Dict[str, Any] = None):
    """Отправка предупреждающего алерта"""
    return notification_system.send_alert(AlertLevel.WARNING, title, message, source, details)

def send_critical_alert(title: str, message: str, source: str = "system", details: Dict[str, Any] = None):
    """Отправка критического алерта"""
    return notification_system.send_alert(AlertLevel.CRITICAL, title, message, source, details)

def send_emergency_alert(title: str, message: str, source: str = "system", details: Dict[str, Any] = None):
    """Отправка экстренного алерта"""
    return notification_system.send_alert(AlertLevel.EMERGENCY, title, message, source, details) 