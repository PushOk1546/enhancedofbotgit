#!/usr/bin/env python3
"""
🔥 ENTERPRISE MONITORING SYSTEM 🔥
Продвинутая система мониторинга для Telegram Stars/TON бота
Real-time метрики, health check, performance tracking, revenue analytics
"""

import os
import time
import json
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import sqlite3

@dataclass
class SystemMetrics:
    """Системные метрики"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    active_users: int
    messages_per_minute: int
    cache_hit_rate: float
    response_time_avg: float
    error_count: int
    revenue_today: float

@dataclass
class UserActivity:
    """Активность пользователя"""
    user_id: int
    last_activity: str
    messages_sent: int
    tier: str
    revenue_contributed: float
    errors_encountered: int

class MonitoringSystem:
    def __init__(self):
        self.db_path = "monitoring.db"
        self.metrics_history = deque(maxlen=1440)  # 24 часа по минутам
        self.user_sessions = {}
        self.message_counter = defaultdict(int)
        self.error_log = deque(maxlen=1000)
        self.response_times = deque(maxlen=100)
        self.revenue_tracker = defaultdict(float)
        
        # Инициализация базы данных
        self.init_database()
        
        # Запуск мониторинга в фоне
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self.continuous_monitoring)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        print("🔥 Monitoring System: АКТИВИРОВАН")

    def init_database(self):
        """Инициализация базы данных мониторинга"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица системных метрик
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_percent REAL,
                memory_percent REAL,
                memory_mb REAL,
                active_users INTEGER,
                messages_per_minute INTEGER,
                cache_hit_rate REAL,
                response_time_avg REAL,
                error_count INTEGER,
                revenue_today REAL
            )
        ''')
        
        # Таблица активности пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                user_id INTEGER,
                timestamp TEXT,
                action TEXT,
                tier TEXT,
                revenue_amount REAL,
                response_time REAL,
                PRIMARY KEY (user_id, timestamp)
            )
        ''')
        
        # Таблица ошибок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                error_type TEXT,
                error_message TEXT,
                user_id INTEGER,
                stack_trace TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def continuous_monitoring(self):
        """Непрерывный мониторинг системы"""
        while self.monitoring_active:
            try:
                metrics = self.collect_system_metrics()
                self.save_metrics(metrics)
                self.metrics_history.append(metrics)
                
                # Проверка алертов
                self.check_alerts(metrics)
                
                time.sleep(60)  # Каждую минуту
            except Exception as e:
                self.log_error("monitoring_error", str(e), None)
                time.sleep(30)

    def collect_system_metrics(self) -> SystemMetrics:
        """Сбор системных метрик"""
        # Системные ресурсы
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_mb = memory.used / 1024 / 1024
        
        # Пользовательские метрики
        current_time = datetime.now()
        active_users = self.count_active_users()
        messages_per_minute = self.calculate_messages_per_minute()
        
        # Производительность
        cache_hit_rate = self.get_cache_hit_rate()
        response_time_avg = self.calculate_avg_response_time()
        error_count = len([e for e in self.error_log if 
                          datetime.fromisoformat(e['timestamp']) > current_time - timedelta(minutes=1)])
        
        # Доходы
        revenue_today = self.calculate_today_revenue()
        
        return SystemMetrics(
            timestamp=current_time.isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            active_users=active_users,
            messages_per_minute=messages_per_minute,
            cache_hit_rate=cache_hit_rate,
            response_time_avg=response_time_avg,
            error_count=error_count,
            revenue_today=revenue_today
        )

    def track_user_action(self, user_id: int, action: str, tier: str = "free", 
                         revenue_amount: float = 0.0, response_time: float = 0.0):
        """Отслеживание действий пользователя"""
        timestamp = datetime.now().isoformat()
        
        # Обновляем сессию пользователя
        self.user_sessions[user_id] = {
            'last_activity': timestamp,
            'tier': tier,
            'session_messages': self.user_sessions.get(user_id, {}).get('session_messages', 0) + 1
        }
        
        # Увеличиваем счетчик сообщений
        self.message_counter[datetime.now().strftime('%Y-%m-%d %H:%M')] += 1
        
        # Трекинг доходов
        if revenue_amount > 0:
            self.revenue_tracker[datetime.now().strftime('%Y-%m-%d')] += revenue_amount
        
        # Сохраняем время отклика
        if response_time > 0:
            self.response_times.append(response_time)
        
        # Сохраняем в базу данных
        self.save_user_activity(user_id, timestamp, action, tier, revenue_amount, response_time)

    def log_error(self, error_type: str, error_message: str, user_id: Optional[int], 
                  stack_trace: str = ""):
        """Логирование ошибок"""
        timestamp = datetime.now().isoformat()
        
        error_entry = {
            'timestamp': timestamp,
            'error_type': error_type,
            'error_message': error_message,
            'user_id': user_id,
            'stack_trace': stack_trace
        }
        
        self.error_log.append(error_entry)
        
        # Сохраняем в базу данных
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO error_log (timestamp, error_type, error_message, user_id, stack_trace)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, error_type, error_message, user_id, stack_trace))
        conn.commit()
        conn.close()
        
        print(f"❌ ERROR LOGGED: {error_type} - {error_message}")

    def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья системы"""
        if not self.metrics_history:
            return {"status": "initializing", "details": "Collecting initial metrics..."}
        
        latest_metrics = self.metrics_history[-1]
        
        # Определяем статус здоровья
        health_score = 100
        issues = []
        
        # Проверка CPU
        if latest_metrics.cpu_percent > 80:
            health_score -= 20
            issues.append(f"High CPU usage: {latest_metrics.cpu_percent:.1f}%")
        
        # Проверка памяти
        if latest_metrics.memory_percent > 80:
            health_score -= 20
            issues.append(f"High memory usage: {latest_metrics.memory_percent:.1f}%")
        
        # Проверка ошибок
        if latest_metrics.error_count > 10:
            health_score -= 15
            issues.append(f"High error rate: {latest_metrics.error_count} errors/min")
        
        # Проверка времени отклика
        if latest_metrics.response_time_avg > 2.0:
            health_score -= 10
            issues.append(f"Slow response time: {latest_metrics.response_time_avg:.2f}s")
        
        # Проверка cache hit rate
        if latest_metrics.cache_hit_rate < 0.5:
            health_score -= 10
            issues.append(f"Low cache hit rate: {latest_metrics.cache_hit_rate:.1%}")
        
        # Определяем общий статус
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 70:
            status = "good"
        elif health_score >= 50:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": health_score,
            "issues": issues,
            "metrics": asdict(latest_metrics),
            "uptime": self.get_uptime(),
            "active_users_24h": len(self.user_sessions)
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Детальный отчет о производительности"""
        if len(self.metrics_history) < 5:
            return {"status": "insufficient_data", "message": "Need more data for analysis"}
        
        recent_metrics = list(self.metrics_history)[-60:]  # Последний час
        
        # Расчет средних значений
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_time_avg for m in recent_metrics) / len(recent_metrics)
        avg_cache_hit_rate = sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics)
        
        # Тренды
        cpu_trend = self.calculate_trend([m.cpu_percent for m in recent_metrics])
        memory_trend = self.calculate_trend([m.memory_percent for m in recent_metrics])
        
        return {
            "timeframe": "last_hour",
            "averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_percent": round(avg_memory, 2),
                "response_time": round(avg_response_time, 3),
                "cache_hit_rate": round(avg_cache_hit_rate, 3)
            },
            "trends": {
                "cpu": cpu_trend,
                "memory": memory_trend
            },
            "total_messages": sum(m.messages_per_minute for m in recent_metrics),
            "total_errors": sum(m.error_count for m in recent_metrics),
            "peak_users": max(m.active_users for m in recent_metrics),
            "revenue_trend": self.get_revenue_trend()
        }

    def get_revenue_analytics(self) -> Dict[str, Any]:
        """Аналитика доходов"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Доходы по дням
        daily_revenue = dict(self.revenue_tracker)
        
        # Сравнения
        today_revenue = daily_revenue.get(today, 0.0)
        yesterday_revenue = daily_revenue.get(yesterday, 0.0)
        
        # Тренд
        revenue_growth = 0
        if yesterday_revenue > 0:
            revenue_growth = ((today_revenue - yesterday_revenue) / yesterday_revenue) * 100
        
        # Недельная статистика
        week_revenue = sum(daily_revenue.get(
            (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), 0
        ) for i in range(7))
        
        return {
            "today": today_revenue,
            "yesterday": yesterday_revenue,
            "growth_percent": round(revenue_growth, 2),
            "week_total": week_revenue,
            "daily_average": round(week_revenue / 7, 2),
            "top_revenue_days": sorted(daily_revenue.items(), 
                                     key=lambda x: x[1], reverse=True)[:5]
        }

    def get_user_analytics(self) -> Dict[str, Any]:
        """Аналитика пользователей"""
        active_users = len(self.user_sessions)
        
        # Распределение по тарифам
        tier_distribution = defaultdict(int)
        for session in self.user_sessions.values():
            tier_distribution[session['tier']] += 1
        
        # Активность по времени
        current_hour = datetime.now().hour
        hourly_activity = defaultdict(int)
        
        for timestamp_str in self.message_counter.keys():
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                hourly_activity[timestamp.hour] += self.message_counter[timestamp_str]
            except:
                continue
        
        return {
            "active_users": active_users,
            "tier_distribution": dict(tier_distribution),
            "hourly_activity": dict(hourly_activity),
            "peak_hour": max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None,
            "messages_total": sum(self.message_counter.values()),
            "avg_session_messages": sum(s['session_messages'] for s in self.user_sessions.values()) / max(1, active_users)
        }

    def generate_monitoring_report(self) -> str:
        """Генерация полного отчета мониторинга"""
        health = self.get_health_status()
        performance = self.get_performance_report()
        revenue = self.get_revenue_analytics()
        users = self.get_user_analytics()
        
        report = f"""
🔥 **МОНИТОРИНГ СИСТЕМЫ** 🔥
📅 **Время:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🏥 **ЗДОРОВЬЕ СИСТЕМЫ:**
• Статус: {health['status'].upper()} ({health['health_score']}/100)
• Проблемы: {len(health['issues'])}
• Uptime: {health['uptime']}
• Активных пользователей: {health['active_users_24h']}

⚡ **ПРОИЗВОДИТЕЛЬНОСТЬ:**
• CPU: {performance.get('averages', {}).get('cpu_percent', 0):.1f}%
• Память: {performance.get('averages', {}).get('memory_percent', 0):.1f}%
• Время отклика: {performance.get('averages', {}).get('response_time', 0):.3f}s
• Cache hit rate: {performance.get('averages', {}).get('cache_hit_rate', 0):.1%}

💰 **ДОХОДЫ:**
• Сегодня: ${revenue['today']:.2f}
• Рост: {revenue['growth_percent']:+.1f}%
• За неделю: ${revenue['week_total']:.2f}
• Средний день: ${revenue['daily_average']:.2f}

👥 **ПОЛЬЗОВАТЕЛИ:**
• Активные: {users['active_users']}
• Сообщений: {users['messages_total']:,}
• Пик активности: {users['peak_hour']}:00

🔴 **ПРОБЛЕМЫ:**
{chr(10).join(f"• {issue}" for issue in health['issues']) if health['issues'] else "• Проблем не обнаружено"}
        """
        
        return report

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def count_active_users(self) -> int:
        """Подсчет активных пользователей за последние 24 часа"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        active_count = 0
        
        for session in self.user_sessions.values():
            try:
                last_activity = datetime.fromisoformat(session['last_activity'])
                if last_activity > cutoff_time:
                    active_count += 1
            except:
                continue
        
        return active_count

    def calculate_messages_per_minute(self) -> int:
        """Расчет сообщений в минуту"""
        current_minute = datetime.now().strftime('%Y-%m-%d %H:%M')
        return self.message_counter.get(current_minute, 0)

    def get_cache_hit_rate(self) -> float:
        """Получение cache hit rate"""
        try:
            from response_cache import response_cache
            stats = response_cache.get_stats()
            total = stats.get('total', 1)
            hits = stats.get('hits', 0)
            return hits / total if total > 0 else 0.0
        except:
            return 0.0

    def calculate_avg_response_time(self) -> float:
        """Расчет среднего времени отклика"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def calculate_today_revenue(self) -> float:
        """Расчет дневного дохода"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.revenue_tracker.get(today, 0.0)

    def calculate_trend(self, values: List[float]) -> str:
        """Определение тренда по значениям"""
        if len(values) < 2:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        change_percent = ((second_half - first_half) / first_half) * 100 if first_half > 0 else 0
        
        if change_percent > 5:
            return "increasing"
        elif change_percent < -5:
            return "decreasing"
        else:
            return "stable"

    def get_uptime(self) -> str:
        """Получение uptime системы"""
        # Простая реализация - время работы мониторинга
        return f"{len(self.metrics_history)} minutes"

    def get_revenue_trend(self) -> str:
        """Тренд доходов"""
        if len(self.revenue_tracker) < 2:
            return "insufficient_data"
        
        recent_days = sorted(self.revenue_tracker.items())[-7:]  # Последние 7 дней
        revenues = [day[1] for day in recent_days]
        
        return self.calculate_trend(revenues)

    def check_alerts(self, metrics: SystemMetrics):
        """Проверка алертов"""
        alerts = []
        
        # Критические алерты
        if metrics.cpu_percent > 90:
            alerts.append(f"🚨 CRITICAL: CPU usage {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > 90:
            alerts.append(f"🚨 CRITICAL: Memory usage {metrics.memory_percent:.1f}%")
        
        if metrics.error_count > 50:
            alerts.append(f"🚨 CRITICAL: Error rate {metrics.error_count} errors/min")
        
        # Предупреждения
        if metrics.response_time_avg > 3.0:
            alerts.append(f"⚠️ WARNING: Slow response time {metrics.response_time_avg:.2f}s")
        
        if metrics.cache_hit_rate < 0.3:
            alerts.append(f"⚠️ WARNING: Low cache hit rate {metrics.cache_hit_rate:.1%}")
        
        # Логируем алерты
        for alert in alerts:
            print(alert)
            self.log_error("alert", alert, None)

    def save_metrics(self, metrics: SystemMetrics):
        """Сохранение метрик в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO system_metrics 
            (timestamp, cpu_percent, memory_percent, memory_mb, active_users, 
             messages_per_minute, cache_hit_rate, response_time_avg, error_count, revenue_today)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp, metrics.cpu_percent, metrics.memory_percent, 
            metrics.memory_mb, metrics.active_users, metrics.messages_per_minute,
            metrics.cache_hit_rate, metrics.response_time_avg, 
            metrics.error_count, metrics.revenue_today
        ))
        conn.commit()
        conn.close()

    def save_user_activity(self, user_id: int, timestamp: str, action: str, 
                          tier: str, revenue_amount: float, response_time: float):
        """Сохранение активности пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_activity 
            (user_id, timestamp, action, tier, revenue_amount, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, timestamp, action, tier, revenue_amount, response_time))
        conn.commit()
        conn.close()

    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        print("🛑 Monitoring System: ОСТАНОВЛЕН")

# Глобальный экземпляр мониторинга
monitoring_system = MonitoringSystem() 