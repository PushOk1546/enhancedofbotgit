"""
API модуль для взаимодействия с Groq.
КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ от команды сеньор разработчиков:
- Circuit Breaker паттерн для устойчивости к сбоям
- Exponential backoff для retry механизма
- Comprehensive error handling и логирование
- Защита от API rate limits
"""

import asyncio
import logging
import time
import random
from enum import Enum
from typing import Optional, Dict, Any
from groq import AsyncGroq
from config import GROQ_KEY

logger = logging.getLogger("bot_logger")

class CircuitState(Enum):
    """Состояния Circuit Breaker"""
    CLOSED = "closed"      # Нормальная работа
    OPEN = "open"          # API недоступен, блокируем запросы
    HALF_OPEN = "half_open"  # Тестирование восстановления

class CircuitBreaker:
    """
    Circuit Breaker для защиты от сбоев API.
    КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Предотвращает каскадные сбои.
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5, 
        recovery_timeout: int = 60,
        success_threshold: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
        logger.info(f"Circuit Breaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}")
    
    async def call(self, func, *args, **kwargs):
        """
        Выполняет вызов через circuit breaker.
        Блокирует вызовы если API недоступен.
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit Breaker: Attempting recovery (HALF_OPEN)")
            else:
                raise APICircuitBreakerError("Circuit breaker is OPEN - API unavailable")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Проверяет, можно ли попытаться восстановить соединение"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time > self.recovery_timeout
    
    def _on_success(self):
        """Обрабатывает успешный вызов"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit Breaker: Recovery successful (CLOSED)")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """Обрабатывает неуспешный вызов"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("Circuit Breaker: Recovery failed, back to OPEN")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit Breaker: Too many failures ({self.failure_count}), switching to OPEN")
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус circuit breaker"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time,
            "time_until_retry": max(0, (self.last_failure_time or 0) + self.recovery_timeout - time.time()) if self.last_failure_time else 0
        }

class APIError(Exception):
    """Базовый класс для ошибок API"""
    pass

class APICircuitBreakerError(APIError):
    """Ошибка circuit breaker - API недоступен"""
    pass

class APIRateLimitError(APIError):
    """Ошибка превышения лимита запросов"""
    pass

class APITimeoutError(APIError):
    """Ошибка таймаута API"""
    pass

class EnhancedRetryManager:
    """
    Улучшенный менеджер повторных попыток.
    КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Exponential backoff + jitter.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Вычисляет задержку для повторной попытки"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Добавляем случайность для избежания thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """Выполняет функцию с exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"All retry attempts exhausted. Last error: {e}")
                    break
                
                delay = self.calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        
        raise last_exception

# Глобальные экземпляры
circuit_breaker = CircuitBreaker()
retry_manager = EnhancedRetryManager()

# Инициализация клиента Groq
groq_client = None

def init_groq_client():
    """Инициализирует клиент Groq"""
    global groq_client
    if not GROQ_KEY:
        logger.error("🚨 CRITICAL: GROQ_KEY not found in environment variables")
        raise APIError("GROQ_KEY not configured")
    
    groq_client = AsyncGroq(api_key=GROQ_KEY)
    logger.info("✅ Groq client initialized successfully")

async def _raw_groq_request(prompt: str, model: str, **kwargs) -> str:
    """
    Выполняет сырой запрос к Groq API.
    Используется circuit breaker'ом.
    """
    if groq_client is None:
        init_groq_client()
    
    try:
        # Валидация параметров
        if not prompt or not prompt.strip():
            raise APIError("Empty prompt provided")
        
        if len(prompt) > 32000:  # Groq limit
            logger.warning(f"Prompt too long ({len(prompt)} chars), truncating")
            prompt = prompt[:32000]
        
        # Параметры по умолчанию
        request_params = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": False
        }
        
        logger.debug(f"Making Groq request: model={model}, prompt_length={len(prompt)}")
        
        # Выполняем запрос с таймаутом
        start_time = time.time()
        
        try:
            response = await asyncio.wait_for(
                groq_client.chat.completions.create(**request_params),
                timeout=30.0  # 30 секунд таймаут
            )
        except asyncio.TimeoutError:
            raise APITimeoutError("Groq API request timeout")
        
        elapsed_time = time.time() - start_time
        
        # Проверяем ответ
        if not response or not response.choices:
            raise APIError("Empty response from Groq API")
        
        content = response.choices[0].message.content
        if not content:
            raise APIError("Empty content in Groq response")
        
        # Логируем статистику
        logger.debug(f"Groq request successful: {elapsed_time:.2f}s, response_length={len(content)}")
        
        return content.strip()
        
    except Exception as e:
        # Классифицируем ошибки
        error_message = str(e).lower()
        
        if "rate limit" in error_message or "too many requests" in error_message:
            raise APIRateLimitError(f"Rate limit exceeded: {e}")
        elif "timeout" in error_message:
            raise APITimeoutError(f"Request timeout: {e}")
        elif "network" in error_message or "connection" in error_message:
            raise APIError(f"Network error: {e}")
        else:
            raise APIError(f"Groq API error: {e}")

async def generate_groq_response(
    prompt: str, 
    model: str, 
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    Генерирует ответ от Groq с защитой от сбоев.
    КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ:
    - Circuit breaker защита
    - Exponential backoff retry
    - Comprehensive error handling
    """
    try:
        # Валидация входных данных
        if not prompt or not model:
            raise APIError("Prompt and model are required")
        
        # Формируем параметры запроса
        request_kwargs = kwargs.copy()
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        request_kwargs["temperature"] = temperature
        
        # Выполняем запрос через circuit breaker и retry manager
        result = await circuit_breaker.call(
            retry_manager.retry_with_backoff,
            _raw_groq_request,
            prompt,
            model,
            **request_kwargs
        )
        
        logger.info(f"✅ Generated response: model={model}, length={len(result)}")
        return result
        
    except APICircuitBreakerError as e:
        logger.error(f"🚨 API Circuit Breaker: {e}")
        # Возвращаем fallback ответ
        return "🤖 Сервис временно недоступен. Попробуйте позже."
        
    except APIRateLimitError as e:
        logger.warning(f"⚠️ API Rate Limit: {e}")
        return "⏱️ Слишком много запросов. Подождите немного."
        
    except APITimeoutError as e:
        logger.warning(f"⏰ API Timeout: {e}")
        return "⏰ Запрос выполняется слишком долго. Попробуйте упростить запрос."
        
    except APIError as e:
        logger.error(f"🚨 API Error: {e}")
        return "❌ Ошибка сервиса. Мы работаем над исправлением."
        
    except Exception as e:
        logger.error(f"🚨 CRITICAL: Unexpected error in generate_groq_response: {e}", exc_info=True)
        return "❌ Произошла неожиданная ошибка. Обратитесь к администратору."

async def health_check() -> Dict[str, Any]:
    """
    Проверка здоровья API.
    Возвращает статус всех компонентов.
    """
    status = {
        "timestamp": time.time(),
        "groq_client": "unknown",
        "circuit_breaker": circuit_breaker.get_status(),
        "overall": "unknown"
    }
    
    try:
        # Проверяем доступность Groq API
        test_response = await generate_groq_response(
            "Test message", 
            "gemma2-2b-it",
            max_tokens=10
        )
        
        if test_response and not test_response.startswith("🤖") and not test_response.startswith("❌"):
            status["groq_client"] = "healthy"
        else:
            status["groq_client"] = "degraded"
            
    except Exception as e:
        status["groq_client"] = "unhealthy"
        status["groq_error"] = str(e)
    
    # Определяем общий статус
    if status["groq_client"] == "healthy" and status["circuit_breaker"]["state"] == "closed":
        status["overall"] = "healthy"
    elif status["groq_client"] == "degraded":
        status["overall"] = "degraded"
    else:
        status["overall"] = "unhealthy"
    
    return status

# Инициализация при импорте модуля
try:
    init_groq_client()
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {e}")
    # Не останавливаем приложение, circuit breaker обработает ошибки