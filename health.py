"""
Система health checks для мониторинга здоровья OnlyFans Assistant Bot.
КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ от команды сеньор разработчиков:
- Comprehensive health monitoring
- Real-time system metrics
- Circuit breaker status monitoring
- Database integrity checks
"""

import asyncio
import time
import psutil
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger("health_checker")

@dataclass
class HealthStatus:
    """Статус компонента системы"""
    name: str
    status: str  # healthy, degraded, unhealthy
    details: Dict[str, Any]
    last_check: float
    response_time: Optional[float] = None
    error: Optional[str] = None

@dataclass
class SystemMetrics:
    """Системные метрики"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    uptime_seconds: float
    active_connections: int
    timestamp: float

class HealthChecker:
    """
    Главный класс для проверки здоровья системы.
    КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Комплексный мониторинг всех компонентов.
    """
    
    def __init__(self):
        self.checks_registry: Dict[str, callable] = {}
        self.last_full_check: Optional[Dict[str, Any]] = None
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 100
        self.startup_time = time.time()
        
        # Регистрируем базовые проверки
        self._register_default_checks()
        
        logger.info("Health Checker initialized with comprehensive monitoring")
    
    def _register_default_checks(self):
        """Регистрирует стандартные проверки здоровья"""
        self.register_check("system", self.check_system_resources)
        self.register_check("telegram", self.check_telegram_api)
        self.register_check("groq", self.check_groq_api)
        self.register_check("filesystem", self.check_filesystem)
        self.register_check("database", self.check_database_integrity)
        self.register_check("security", self.check_security_status)
        self.register_check("memory_leaks", self.check_memory_leaks)
    
    def register_check(self, name: str, check_func: callable):
        """Регистрирует новую проверку здоровья"""
        self.checks_registry[name] = check_func
        logger.debug(f"Registered health check: {name}")
    
    async def check_system_resources(self) -> HealthStatus:
        """Проверяет системные ресурсы"""
        try:
            start_time = time.time()
            
            # Получаем системные метрики
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = time.time() - start_time
            
            # Определяем статус на основе использования ресурсов
            if cpu_percent > 90 or memory.percent > 95 or disk.percent > 95:
                status = "unhealthy"
            elif cpu_percent > 70 or memory.percent > 80 or disk.percent > 85:
                status = "degraded"
            else:
                status = "healthy"
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / 1024 / 1024,
                "memory_available_mb": memory.available / 1024 / 1024,
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "uptime_hours": (time.time() - self.startup_time) / 3600
            }
            
            # Сохраняем метрики в историю
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_percent=disk.percent,
                uptime_seconds=time.time() - self.startup_time,
                active_connections=len(psutil.net_connections()),
                timestamp=time.time()
            )
            self._add_metrics_to_history(metrics)
            
            return HealthStatus(
                name="system",
                status=status,
                details=details,
                last_check=time.time(),
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return HealthStatus(
                name="system",
                status="unhealthy",
                details={},
                last_check=time.time(),
                error=str(e)
            )
    
    async def check_telegram_api(self) -> HealthStatus:
        """Проверяет доступность Telegram API"""
        try:
            start_time = time.time()
            
            # Импортируем бота для проверки
            try:
                from bot import bot
                
                # Простая проверка через getMe
                me = await bot.get_me()
                response_time = time.time() - start_time
                
                if me and me.username:
                    status = "healthy"
                    details = {
                        "bot_username": me.username,
                        "bot_id": me.id,
                        "can_read_all_group_messages": me.can_read_all_group_messages,
                        "api_response_time": response_time
                    }
                else:
                    status = "degraded"
                    details = {"issue": "Invalid bot response"}
                
            except ImportError:
                # Бот еще не инициализирован
                status = "degraded"
                details = {"issue": "Bot not initialized"}
                response_time = time.time() - start_time
            
            return HealthStatus(
                name="telegram",
                status=status,
                details=details,
                last_check=time.time(),
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Telegram API check failed: {e}")
            return HealthStatus(
                name="telegram",
                status="unhealthy",
                details={},
                last_check=time.time(),
                error=str(e)
            )
    
    async def check_groq_api(self) -> HealthStatus:
        """Проверяет состояние Groq API"""
        try:
            from api import health_check as api_health_check, circuit_breaker
            
            start_time = time.time()
            api_status = await api_health_check()
            response_time = time.time() - start_time
            
            # Анализируем статус API
            if api_status["overall"] == "healthy":
                status = "healthy"
            elif api_status["overall"] == "degraded":
                status = "degraded"
            else:
                status = "unhealthy"
            
            details = {
                "groq_client_status": api_status["groq_client"],
                "circuit_breaker": api_status["circuit_breaker"],
                "api_response_time": response_time
            }
            
            return HealthStatus(
                name="groq",
                status=status,
                details=details,
                last_check=time.time(),
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Groq API check failed: {e}")
            return HealthStatus(
                name="groq",
                status="unhealthy",
                details={},
                last_check=time.time(),
                error=str(e)
            )
    
    async def check_filesystem(self) -> HealthStatus:
        """Проверяет состояние файловой системы"""
        try:
            start_time = time.time()
            
            # Проверяем ключевые файлы и директории
            checks = {
                "data_directory": os.path.exists("data"),
                "users_file": os.path.exists("data/users.json"),
                "prompts_directory": os.path.exists("prompts"),
                "logs_writable": os.access(".", os.W_OK)
            }
            
            # Проверяем размеры файлов
            file_sizes = {}
            if checks["users_file"]:
                file_sizes["users_json_kb"] = os.path.getsize("data/users.json") / 1024
            
            response_time = time.time() - start_time
            
            # Определяем статус
            if all(checks.values()):
                status = "healthy"
            elif checks["data_directory"] and checks["logs_writable"]:
                status = "degraded"
            else:
                status = "unhealthy"
            
            details = {
                "checks": checks,
                "file_sizes": file_sizes,
                "filesystem_response_time": response_time
            }
            
            return HealthStatus(
                name="filesystem",
                status=status,
                details=details,
                last_check=time.time(),
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Filesystem check failed: {e}")
            return HealthStatus(
                name="filesystem",
                status="unhealthy",
                details={},
                last_check=time.time(),
                error=str(e)
            )
    
    async def check_database_integrity(self) -> HealthStatus:
        """Проверяет целостность данных пользователей"""
        try:
            start_time = time.time()
            
            from state_manager import StateManager
            
            # Создаем временный state manager для проверки
            test_sm = StateManager()
            
            # Проверяем загрузку данных
            await test_sm.load_data()
            
            # Проверяем статистику пользователей
            user_count = test_sm.get_user_count()
            active_users = len(test_sm.get_active_users(24))
            
            # Проверяем целостность данных
            integrity_issues = []
            
            for user_id, user_state in test_sm.users.items():
                if not isinstance(user_id, int):
                    integrity_issues.append(f"Invalid user_id type: {type(user_id)}")
                
                if len(user_state.history) > 1000:
                    integrity_issues.append(f"User {user_id} has excessive history: {len(user_state.history)}")
            
            response_time = time.time() - start_time
            
            # Определяем статус
            if not integrity_issues and user_count >= 0:
                status = "healthy"
            elif integrity_issues and len(integrity_issues) < 5:
                status = "degraded"
            else:
                status = "unhealthy"
            
            details = {
                "total_users": user_count,
                "active_users_24h": active_users,
                "integrity_issues": integrity_issues,
                "data_load_time": response_time
            }
            
            return HealthStatus(
                name="database",
                status=status,
                details=details,
                last_check=time.time(),
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return HealthStatus(
                name="database",
                status="unhealthy",
                details={},
                last_check=time.time(),
                error=str(e)
            )
    
    async def check_security_status(self) -> HealthStatus:
        """Проверяет статус безопасности"""
        try:
            start_time = time.time()
            
            from security import security_stats, rate_limiter
            from config.config import ADMIN_IDS
            
            # Получаем статистику безопасности
            stats = security_stats.get_stats()
            
            # Проверяем конфигурацию безопасности
            security_config = {
                "admin_ids_configured": len(ADMIN_IDS) > 0,
                "rate_limiter_active": rate_limiter is not None,
                "blocked_attempts": stats["blocked_attempts"],
                "rate_limited_requests": stats["rate_limited"],
                "input_sanitized": stats["input_sanitized"]
            }
            
            response_time = time.time() - start_time
            
            # Определяем статус
            if security_config["admin_ids_configured"] and security_config["rate_limiter_active"]:
                status = "healthy"
            elif security_config["rate_limiter_active"]:
                status = "degraded"
            else:
                status = "unhealthy"
            
            details = {
                "security_config": security_config,
                "security_stats": stats,
                "security_check_time": response_time
            }
            
            return HealthStatus(
                name="security",
                status=status,
                details=details,
                last_check=time.time(),
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Security status check failed: {e}")
            return HealthStatus(
                name="security",
                status="unhealthy",
                details={},
                last_check=time.time(),
                error=str(e)
            )
    
    async def check_memory_leaks(self) -> HealthStatus:
        """Проверяет потенциальные утечки памяти"""
        try:
            start_time = time.time()
            
            # Анализируем историю метрик для выявления трендов
            if len(self.metrics_history) < 10:
                status = "healthy"
                details = {"note": "Insufficient data for memory leak detection"}
            else:
                # Проверяем тренд использования памяти
                recent_metrics = self.metrics_history[-10:]
                memory_trend = [m.memory_percent for m in recent_metrics]
                
                # Простая проверка на постоянный рост памяти
                increasing_count = 0
                for i in range(1, len(memory_trend)):
                    if memory_trend[i] > memory_trend[i-1]:
                        increasing_count += 1
                
                memory_leak_risk = increasing_count / (len(memory_trend) - 1)
                
                if memory_leak_risk > 0.8:  # 80% измерений показывают рост
                    status = "degraded"
                elif memory_leak_risk > 0.9:  # 90% измерений показывают рост
                    status = "unhealthy"
                else:
                    status = "healthy"
                
                details = {
                    "memory_trend": memory_trend,
                    "leak_risk_percent": memory_leak_risk * 100,
                    "current_memory_mb": recent_metrics[-1].memory_used_mb
                }
            
            response_time = time.time() - start_time
            
            return HealthStatus(
                name="memory_leaks",
                status=status,
                details=details,
                last_check=time.time(),
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Memory leak check failed: {e}")
            return HealthStatus(
                name="memory_leaks",
                status="unhealthy",
                details={},
                last_check=time.time(),
                error=str(e)
            )
    
    def _add_metrics_to_history(self, metrics: SystemMetrics):
        """Добавляет метрики в историю"""
        self.metrics_history.append(metrics)
        
        # Ограничиваем размер истории
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Запускает все зарегистрированные проверки.
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Параллельное выполнение для производительности.
        """
        logger.info("Starting comprehensive health check...")
        start_time = time.time()
        
        # Запускаем все проверки параллельно
        tasks = []
        for name, check_func in self.checks_registry.items():
            task = asyncio.create_task(check_func())
            tasks.append((name, task))
        
        # Ожидаем завершения всех проверок
        results = {}
        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = HealthStatus(
                    name=name,
                    status="unhealthy",
                    details={},
                    last_check=time.time(),
                    error=str(e)
                )
        
        # Определяем общий статус системы
        overall_status = self._calculate_overall_status(results)
        
        # Формируем итоговый отчет
        health_report = {
            "timestamp": time.time(),
            "overall_status": overall_status,
            "check_duration": time.time() - start_time,
            "components": {name: asdict(status) for name, status in results.items()},
            "summary": self._generate_summary(results)
        }
        
        self.last_full_check = health_report
        logger.info(f"Health check completed: {overall_status} ({health_report['check_duration']:.2f}s)")
        
        return health_report
    
    def _calculate_overall_status(self, results: Dict[str, HealthStatus]) -> str:
        """Вычисляет общий статус на основе результатов всех проверок"""
        statuses = [status.status for status in results.values()]
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"
    
    def _generate_summary(self, results: Dict[str, HealthStatus]) -> Dict[str, Any]:
        """Генерирует краткую сводку по результатам проверок"""
        healthy_count = sum(1 for s in results.values() if s.status == "healthy")
        degraded_count = sum(1 for s in results.values() if s.status == "degraded")
        unhealthy_count = sum(1 for s in results.values() if s.status == "unhealthy")
        
        avg_response_time = sum(
            s.response_time for s in results.values() 
            if s.response_time is not None
        ) / len([s for s in results.values() if s.response_time is not None])
        
        return {
            "total_checks": len(results),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "average_response_time": avg_response_time,
            "issues": [
                f"{name}: {status.error or 'degraded'}" 
                for name, status in results.items() 
                if status.status != "healthy"
            ]
        }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Возвращает текущую статистику системы"""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        current_metrics = self.metrics_history[-1]
        
        return {
            "current": asdict(current_metrics),
            "history_size": len(self.metrics_history),
            "uptime_hours": (time.time() - self.startup_time) / 3600,
            "last_health_check": self.last_full_check["timestamp"] if self.last_full_check else None
        }

# Глобальный экземпляр health checker
health_checker = HealthChecker()

async def quick_health_check() -> Dict[str, str]:
    """Быстрая проверка основных компонентов"""
    try:
        # Только критические проверки
        system_check = await health_checker.check_system_resources()
        
        return {
            "status": system_check.status,
            "timestamp": time.time(),
            "uptime": (time.time() - health_checker.startup_time) / 3600
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        } 