"""
Простой StateManager для MVP
Временное хранение пользовательских данных
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class StateManager:
    """Простой менеджер состояний для временного хранения данных"""
    
    def __init__(self, ttl_minutes: int = 30):
        self._states: Dict[str, Dict[str, Any]] = {}
        self._user_data: Dict[int, Dict[str, Any]] = {}  # {user_id: {key: value}}
        self._user_data_ttl: Dict[int, datetime] = {}  # TTL для данных пользователей
        self._ttl_minutes = ttl_minutes
        
    # === НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЬСКИМИ ДАННЫМИ ===
    
    async def set_user_data(self, user_id: int, key: str, value: Any) -> None:
        """Установить данные пользователя"""
        if user_id not in self._user_data:
            self._user_data[user_id] = {}
        
        self._user_data[user_id][key] = value
        # Обновляем TTL для пользователя
        self._user_data_ttl[user_id] = datetime.now() + timedelta(minutes=self._ttl_minutes)
        
    async def get_user_data(self, user_id: int, key: str) -> Optional[Any]:
        """Получить данные пользователя"""
        # Проверяем не истек ли срок хранения
        if user_id in self._user_data_ttl:
            if datetime.now() > self._user_data_ttl[user_id]:
                # Удаляем истекшие данные
                self._user_data.pop(user_id, None)
                self._user_data_ttl.pop(user_id, None)
                return None
        
        if user_id not in self._user_data:
            return None
            
        return self._user_data[user_id].get(key)
    
    async def delete_user_data(self, user_id: int, key: Optional[str] = None) -> None:
        """Удалить данные пользователя"""
        if user_id not in self._user_data:
            return
            
        if key is None:
            # Удаляем все данные пользователя
            self._user_data.pop(user_id, None)
            self._user_data_ttl.pop(user_id, None)
        else:
            # Удаляем конкретный ключ
            self._user_data[user_id].pop(key, None)
            # Если данных не осталось, удаляем пользователя полностью
            if not self._user_data[user_id]:
                self._user_data.pop(user_id, None)
                self._user_data_ttl.pop(user_id, None)
    
    async def get_all_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить все данные пользователя"""
        # Проверяем TTL
        if user_id in self._user_data_ttl:
            if datetime.now() > self._user_data_ttl[user_id]:
                self._user_data.pop(user_id, None)
                self._user_data_ttl.pop(user_id, None)
                return None
        
        return self._user_data.get(user_id, {}).copy()
    
    async def has_user_data(self, user_id: int, key: str) -> bool:
        """Проверить наличие данных пользователя"""
        value = await self.get_user_data(user_id, key)
        return value is not None
    
    # === СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ДЛЯ /reply КОМАНДЫ ===
    
    async def set_last_message_for_reply(self, user_id: int, message_text: str, message_hash: str) -> None:
        """Сохранить последнее сообщение для команды /reply"""
        await self.set_user_data(user_id, 'last_message_text_for_reply', message_text)
        await self.set_user_data(user_id, 'last_message_hash_for_reply', message_hash)
    
    async def get_last_message_for_reply(self, user_id: int) -> Optional[Dict[str, str]]:
        """Получить последнее сообщение для команды /reply"""
        message_text = await self.get_user_data(user_id, 'last_message_text_for_reply')
        message_hash = await self.get_user_data(user_id, 'last_message_hash_for_reply')
        
        if message_text and message_hash:
            return {
                'text': message_text,
                'hash': message_hash
            }
        return None
    
    async def clear_last_message_for_reply(self, user_id: int) -> None:
        """Очистить последнее сообщение для команды /reply"""
        await self.delete_user_data(user_id, 'last_message_text_for_reply')
        await self.delete_user_data(user_id, 'last_message_hash_for_reply')
    
    async def set_reply_variants(self, user_id: int, message_hash: str, variants: list) -> None:
        """Сохранить варианты ответов"""
        await self.set_user_data(user_id, f'reply_variants_{message_hash}', variants)
    
    async def get_reply_variants(self, user_id: int, message_hash: str) -> Optional[list]:
        """Получить варианты ответов"""
        return await self.get_user_data(user_id, f'reply_variants_{message_hash}')
    
    async def clear_reply_variants(self, user_id: int, message_hash: str) -> None:
        """Очистить варианты ответов"""
        await self.delete_user_data(user_id, f'reply_variants_{message_hash}')
    
    # === МЕТОДЫ ДЛЯ СТАТИСТИКИ ПОЛЬЗОВАТЕЛЕЙ ===
    
    async def increment_user_stat(self, user_id: int, stat_name: str) -> int:
        """Увеличить счетчик статистики пользователя"""
        current_value = await self.get_user_data(user_id, f'stat_{stat_name}') or 0
        new_value = current_value + 1
        await self.set_user_data(user_id, f'stat_{stat_name}', new_value)
        return new_value
    
    async def get_user_stat(self, user_id: int, stat_name: str) -> int:
        """Получить значение статистики пользователя"""
        return await self.get_user_data(user_id, f'stat_{stat_name}') or 0
    
    async def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """Получить все статистики пользователя"""
        all_data = await self.get_all_user_data(user_id) or {}
        stats = {}
        for key, value in all_data.items():
            if key.startswith('stat_'):
                stat_name = key[5:]  # Убираем префикс 'stat_'
                stats[stat_name] = value
        return stats
        
    # === СУЩЕСТВУЮЩИЕ МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ ===
        
    async def set_user_message(self, message_hash: str, user_id: int, message: str, additional_data: Dict = None) -> None:
        """Сохранить сообщение пользователя"""
        expires_at = datetime.now() + timedelta(minutes=self._ttl_minutes)
        
        self._states[message_hash] = {
            'user_id': user_id,
            'message': message,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'additional_data': additional_data or {}
        }
        
    async def get_user_message(self, message_hash: str) -> Optional[Dict[str, Any]]:
        """Получить сообщение пользователя"""
        if message_hash not in self._states:
            return None
            
        state = self._states[message_hash]
        
        # Проверяем не истек ли срок
        if datetime.now() > state['expires_at']:
            del self._states[message_hash]
            return None
            
        return state
        
    async def delete_user_message(self, message_hash: str) -> None:
        """Удалить сообщение пользователя"""
        self._states.pop(message_hash, None)
        
    async def cleanup_expired(self) -> None:
        """Очистка истекших состояний"""
        now = datetime.now()
        
        # Очистка старых состояний сообщений
        expired_message_keys = [
            key for key, state in self._states.items()
            if now > state['expires_at']
        ]
        
        for key in expired_message_keys:
            del self._states[key]
        
        # Очистка истекших пользовательских данных
        expired_user_ids = [
            user_id for user_id, ttl in self._user_data_ttl.items()
            if now > ttl
        ]
        
        for user_id in expired_user_ids:
            self._user_data.pop(user_id, None)
            self._user_data_ttl.pop(user_id, None)
            
    async def get_stats(self) -> Dict[str, int]:
        """Получить статистику состояний"""
        await self.cleanup_expired()
        
        total_user_data_keys = sum(len(data) for data in self._user_data.values())
        
        return {
            'total_message_states': len(self._states),
            'total_users_with_data': len(self._user_data),
            'total_user_data_keys': total_user_data_keys,
            'ttl_minutes': self._ttl_minutes
        }

# Глобальный экземпляр для использования в боте
state_manager = StateManager() 