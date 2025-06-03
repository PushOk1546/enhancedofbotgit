"""
Модуль безопасности и авторизации для OnlyFans Assistant Bot
Реализует критические исправления безопасности согласно аудиту сеньор разработчиков
"""

import time
import logging
from functools import wraps
from typing import Dict, List, Optional
from config import ADMIN_IDS

logger = logging.getLogger("security")

def admin_required(func):
    """
    Декоратор для проверки admin прав.
    КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Проверяет ADMIN_IDS перед выполнением функции.
    """
    @wraps(func)
    async def wrapper(bot, message, *args, **kwargs):
        user_id = message.from_user.id
        
        if user_id not in ADMIN_IDS:
            logger.warning(f"🚨 SECURITY: Unauthorized access attempt by user {user_id}")
            from handlers import safe_reply_to
            await safe_reply_to(bot, message, "❌ Доступ запрещен. Требуются права администратора.")
            return
        
        logger.info(f"✅ SECURITY: Admin access granted for user {user_id}")
        return await func(bot, message, *args, **kwargs)
    return wrapper

def validate_user_input(user_input: str, max_length: int = 1000) -> str:
    """
    Валидация и санитизация пользовательского ввода.
    КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Защита от prompt injection атак.
    """
    if not isinstance(user_input, str):
        raise ValueError("Input must be string")
    
    if len(user_input) > max_length:
        raise ValueError(f"Input too long: {len(user_input)} > {max_length}")
    
    # Экранирование потенциально опасных символов для prompt injection
    dangerous_patterns = [
        ('${', '\\${'),          # Template injection
        ('{', '\\{'),            # Template placeholders
        ('}', '\\}'),            # Template placeholders  
        ('`', '\\`'),            # Code execution
        ('<script>', '&lt;script&gt;'),  # XSS
        ('</script>', '&lt;/script&gt;'), # XSS
        ('javascript:', 'javascript_'),   # JS injection
        ('data:', 'data_'),      # Data URLs
        ('vbscript:', 'vbscript_'), # VBScript
    ]
    
    cleaned_input = user_input
    for dangerous, safe in dangerous_patterns:
        cleaned_input = cleaned_input.replace(dangerous, safe)
    
    # Дополнительная защита: удаляем null bytes
    cleaned_input = cleaned_input.replace('\x00', '')
    
    if cleaned_input != user_input:
        logger.warning(f"🛡️ SECURITY: Sanitized dangerous input from user")
    
    return cleaned_input

class RateLimiter:
    """
    Rate limiter для защиты от DoS атак.
    КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Предотвращает исчерпание API квот.
    """
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.requests: Dict[int, List[float]] = {}
        self.max_requests = max_requests
        self.time_window = time_window
        self.admin_max_requests = max_requests * 5  # Админы получают больше лимита
    
    def is_allowed(self, user_id: int) -> bool:
        """Проверяет, разрешен ли запрос от пользователя"""
        current_time = time.time()
        
        # Очищаем старые запросы
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if current_time - req_time < self.time_window
            ]
        else:
            self.requests[user_id] = []
        
        # Определяем лимит: админы получают больше запросов
        max_limit = self.admin_max_requests if user_id in ADMIN_IDS else self.max_requests
        
        # Проверяем лимит
        if len(self.requests[user_id]) >= max_limit:
            logger.warning(f"🚫 RATE LIMIT: User {user_id} exceeded limit ({len(self.requests[user_id])}/{max_limit})")
            return False
        
        # Добавляем текущий запрос
        self.requests[user_id].append(current_time)
        return True
    
    def get_remaining_requests(self, user_id: int) -> int:
        """Возвращает количество оставшихся запросов"""
        if user_id not in self.requests:
            return self.max_requests
        
        max_limit = self.admin_max_requests if user_id in ADMIN_IDS else self.max_requests
        return max(0, max_limit - len(self.requests[user_id]))
    
    def get_reset_time(self, user_id: int) -> Optional[float]:
        """Возвращает время до сброса лимита"""
        if user_id not in self.requests or not self.requests[user_id]:
            return None
        
        oldest_request = min(self.requests[user_id])
        reset_time = oldest_request + self.time_window
        return max(0, reset_time - time.time())

# Глобальные экземпляры
rate_limiter = RateLimiter()
ai_rate_limiter = RateLimiter(max_requests=5, time_window=60)  # Строже для AI запросов

def rate_limit_check(limiter: RateLimiter = None):
    """
    Декоратор для проверки rate limit
    """
    if limiter is None:
        limiter = rate_limiter
    
    def decorator(func):
        @wraps(func)
        async def wrapper(bot, message, *args, **kwargs):
            user_id = message.from_user.id
            
            if not limiter.is_allowed(user_id):
                remaining_time = limiter.get_reset_time(user_id)
                from handlers import safe_reply_to
                
                if remaining_time:
                    await safe_reply_to(
                        bot, message, 
                        f"❌ Слишком много запросов. Подождите {int(remaining_time)} секунд."
                    )
                else:
                    await safe_reply_to(bot, message, "❌ Слишком много запросов. Попробуйте позже.")
                return
            
            return await func(bot, message, *args, **kwargs)
        return wrapper
    return decorator

def secure_format_prompt(template: str, **kwargs) -> str:
    """
    Безопасное форматирование промптов с валидацией.
    КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Защита от prompt injection.
    """
    # Валидируем все аргументы
    cleaned_kwargs = {}
    for key, value in kwargs.items():
        if isinstance(value, str):
            cleaned_kwargs[key] = validate_user_input(value, max_length=2000)
        else:
            cleaned_kwargs[key] = str(value)[:2000]  # Ограничиваем длину
    
    try:
        formatted = template.format(**cleaned_kwargs)
        return formatted
    except KeyError as e:
        logger.error(f"🚨 SECURITY: Template formatting error: {e}")
        # Возвращаем безопасную версию без форматирования
        return template.replace('{', '{{').replace('}', '}}')

def log_security_event(event_type: str, user_id: int, details: str = ""):
    """Логирование событий безопасности"""
    logger.warning(f"🔒 SECURITY EVENT: {event_type} | User: {user_id} | {details}")

# Статистика безопасности
class SecurityStats:
    def __init__(self):
        self.blocked_attempts = 0
        self.rate_limited = 0
        self.input_sanitized = 0
        self.admin_accesses = 0
    
    def increment_blocked(self):
        self.blocked_attempts += 1
    
    def increment_rate_limited(self):
        self.rate_limited += 1
    
    def increment_sanitized(self):
        self.input_sanitized += 1
    
    def increment_admin_access(self):
        self.admin_accesses += 1
    
    def get_stats(self) -> dict:
        return {
            "blocked_attempts": self.blocked_attempts,
            "rate_limited": self.rate_limited,
            "input_sanitized": self.input_sanitized,
            "admin_accesses": self.admin_accesses
        }

security_stats = SecurityStats() 