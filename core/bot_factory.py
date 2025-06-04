#!/usr/bin/env python3
"""
Enterprise Bot Factory - Dependency Injection & Factory Pattern
Senior Developers Team - 10,000+ Projects Experience

Features:
- Dependency Injection Container
- Factory Pattern Implementation
- Interface Segregation
- Single Responsibility Principle
- Thread-Safe Operations
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Type, TypeVar, Generic
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

# Type definitions
T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management"""
    SINGLETON = "singleton"
    TRANSIENT = "transient" 
    SCOPED = "scoped"


class IBot(Protocol):
    """Bot interface for dependency injection"""
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def send_message(self, chat_id: int, text: str) -> None: ...


class IUserService(Protocol):
    """User service interface"""
    async def get_user(self, user_id: int) -> Optional[Dict]: ...
    async def create_user(self, user_data: Dict) -> bool: ...
    async def update_user(self, user_id: int, data: Dict) -> bool: ...


class IPaymentService(Protocol):
    """Payment service interface"""
    async def process_payment(self, user_id: int, amount: float, currency: str) -> bool: ...
    async def get_subscription_status(self, user_id: int) -> str: ...


class IMessageService(Protocol):
    """Message service interface"""
    async def generate_response(self, user_id: int, message: str) -> str: ...
    async def get_templates(self, category: str) -> List[str]: ...


@dataclass
class ServiceDescriptor:
    """Service descriptor for DI container"""
    service_type: Type
    implementation: Type
    lifetime: ServiceLifetime
    instance: Optional[object] = None


class DIContainer:
    """Dependency Injection Container - Enterprise Grade"""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, object] = {}
        self._lock = threading.RLock()
        self._scoped_services: Dict[str, Dict[Type, object]] = {}
        
    def register_singleton(self, service_type: Type[T], implementation: Type[T]) -> 'DIContainer':
        """Register singleton service"""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.SINGLETON
            )
        return self
    
    def register_transient(self, service_type: Type[T], implementation: Type[T]) -> 'DIContainer':
        """Register transient service"""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.TRANSIENT
            )
        return self
    
    def register_scoped(self, service_type: Type[T], implementation: Type[T]) -> 'DIContainer':
        """Register scoped service"""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.SCOPED
            )
        return self
    
    def resolve(self, service_type: Type[T], scope_id: Optional[str] = None) -> T:
        """Resolve service with proper lifetime management"""
        with self._lock:
            if service_type not in self._services:
                raise ValueError(f"Service {service_type} not registered")
            
            descriptor = self._services[service_type]
            
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_type not in self._singletons:
                    self._singletons[service_type] = self._create_instance(descriptor)
                return self._singletons[service_type]
            
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                if scope_id is None:
                    scope_id = "default"
                
                if scope_id not in self._scoped_services:
                    self._scoped_services[scope_id] = {}
                
                if service_type not in self._scoped_services[scope_id]:
                    self._scoped_services[scope_id][service_type] = self._create_instance(descriptor)
                
                return self._scoped_services[scope_id][service_type]
            
            else:  # TRANSIENT
                return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> object:
        """Create service instance with dependency injection"""
        # Get constructor parameters and resolve dependencies
        import inspect
        
        sig = inspect.signature(descriptor.implementation.__init__)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_type = param.annotation
            if param_type in self._services:
                params[param_name] = self.resolve(param_type)
        
        return descriptor.implementation(**params)
    
    def create_scope(self, scope_id: str) -> 'ServiceScope':
        """Create new service scope"""
        return ServiceScope(self, scope_id)
    
    def dispose_scope(self, scope_id: str) -> None:
        """Dispose service scope"""
        with self._lock:
            if scope_id in self._scoped_services:
                # Call dispose on all scoped services if they have it
                for service in self._scoped_services[scope_id].values():
                    if hasattr(service, 'dispose'):
                        service.dispose()
                
                del self._scoped_services[scope_id]


class ServiceScope:
    """Service scope for scoped lifetime management"""
    
    def __init__(self, container: DIContainer, scope_id: str):
        self.container = container
        self.scope_id = scope_id
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve service in this scope"""
        return self.container.resolve(service_type, self.scope_id)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.dispose_scope(self.scope_id)


class BotFactory:
    """Enterprise Bot Factory with Advanced DI"""
    
    def __init__(self):
        self.container = DIContainer()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._logger = logging.getLogger(__name__)
        self._setup_services()
    
    def _setup_services(self) -> None:
        """Setup all services with proper DI registration"""
        # Import implementations here to avoid circular imports
        from .services.user_service import UserService
        from .services.payment_service import PaymentService
        from .services.message_service import MessageService
        from .enterprise_bot_v2 import EnterpriseBot
        
        # Register services
        self.container.register_singleton(IUserService, UserService)
        self.container.register_singleton(IPaymentService, PaymentService)
        self.container.register_singleton(IMessageService, MessageService)
        self.container.register_singleton(IBot, EnterpriseBot)
    
    def create_bot(self) -> IBot:
        """Create bot instance with all dependencies injected"""
        try:
            bot = self.container.resolve(IBot)
            self._logger.info("Enterprise bot created successfully")
            return bot
        except Exception as e:
            self._logger.error(f"Failed to create bot: {e}")
            raise
    
    async def create_bot_async(self) -> IBot:
        """Create bot instance asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.create_bot)
    
    def create_scope(self, scope_id: str) -> ServiceScope:
        """Create new service scope"""
        return self.container.create_scope(scope_id)
    
    def shutdown(self) -> None:
        """Shutdown factory and cleanup resources"""
        self._executor.shutdown(wait=True)
        
        # Dispose all singletons
        for service in self.container._singletons.values():
            if hasattr(service, 'dispose'):
                service.dispose()


# Global factory instance (Singleton)
_factory_instance: Optional[BotFactory] = None
_factory_lock = threading.Lock()


def get_bot_factory() -> BotFactory:
    """Get global bot factory instance (Thread-safe Singleton)"""
    global _factory_instance
    
    if _factory_instance is None:
        with _factory_lock:
            if _factory_instance is None:
                _factory_instance = BotFactory()
    
    return _factory_instance


# Convenience functions
def create_enterprise_bot() -> IBot:
    """Create enterprise bot with DI"""
    factory = get_bot_factory()
    return factory.create_bot()


async def create_enterprise_bot_async() -> IBot:
    """Create enterprise bot asynchronously"""
    factory = get_bot_factory()
    return await factory.create_bot_async() 