"""
Конфигурационный модуль
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    url: str
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

@dataclass
class RedisConfig:
    """Конфигурация Redis"""
    url: str
    pool_size: int = 10
    timeout: int = 5

@dataclass
class MonitoringConfig:
    """Конфигурация мониторинга"""
    enabled: bool = True
    interval: int = 60
    metrics_port: int = 9090

@dataclass
class CacheConfig:
    """Конфигурация кэширования"""
    memory_size: int = 1000
    redis_enabled: bool = True
    file_cache_path: str = "cache"
    default_ttl: int = 3600

@dataclass
class QueueConfig:
    """Конфигурация очередей"""
    max_workers: int = 10
    max_queue_size: int = 1000
    retry_delay: float = 1.0
    max_retries: int = 3

@dataclass
class LoggingConfig:
    """Конфигурация логирования"""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    rotation: str = "1 day"
    retention: str = "7 days"
    path: str = "logs"

@dataclass
class Config:
    """Основная конфигурация"""
    env: str
    debug: bool
    database: DatabaseConfig
    redis: Optional[RedisConfig]
    monitoring: MonitoringConfig
    cache: CacheConfig
    queue: QueueConfig
    logging: LoggingConfig
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Создание конфигурации из переменных окружения"""
        env = os.getenv("ENV", "development")
        debug = env == "development"
        
        # База данных
        database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///bot.db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            echo=debug
        )
        
        # Redis
        redis_url = os.getenv("REDIS_URL")
        redis = RedisConfig(
            url=redis_url,
            pool_size=int(os.getenv("REDIS_POOL_SIZE", "10")),
            timeout=int(os.getenv("REDIS_TIMEOUT", "5"))
        ) if redis_url else None
        
        # Мониторинг
        monitoring = MonitoringConfig(
            enabled=bool(int(os.getenv("MONITORING_ENABLED", "1"))),
            interval=int(os.getenv("MONITORING_INTERVAL", "60")),
            metrics_port=int(os.getenv("METRICS_PORT", "9090"))
        )
        
        # Кэширование
        cache = CacheConfig(
            memory_size=int(os.getenv("CACHE_MEMORY_SIZE", "1000")),
            redis_enabled=bool(int(os.getenv("CACHE_REDIS_ENABLED", "1"))),
            file_cache_path=os.getenv("CACHE_FILE_PATH", "cache"),
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "3600"))
        )
        
        # Очереди
        queue = QueueConfig(
            max_workers=int(os.getenv("QUEUE_MAX_WORKERS", "10")),
            max_queue_size=int(os.getenv("QUEUE_MAX_SIZE", "1000")),
            retry_delay=float(os.getenv("QUEUE_RETRY_DELAY", "1.0")),
            max_retries=int(os.getenv("QUEUE_MAX_RETRIES", "3"))
        )
        
        # Логирование
        logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"),
            rotation=os.getenv("LOG_ROTATION", "1 day"),
            retention=os.getenv("LOG_RETENTION", "7 days"),
            path=os.getenv("LOG_PATH", "logs")
        )
        
        return cls(
            env=env,
            debug=debug,
            database=database,
            redis=redis,
            monitoring=monitoring,
            cache=cache,
            queue=queue,
            logging=logging
        )

# Создание конфигурации
config = Config.from_env()

# Создание необходимых директорий
Path(config.logging.path).mkdir(parents=True, exist_ok=True)
Path(config.cache.file_cache_path).mkdir(parents=True, exist_ok=True) 