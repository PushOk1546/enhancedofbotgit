"""
Модуль моделей для управления множественными чатами с клиентами.
Обеспечивает сохранение контекста и памяти для каждого отдельного чата.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

class ClientProfile:
    """Профиль клиента с базовой информацией"""
    
    def __init__(self, client_id: str = None, name: str = "", description: str = ""):
        self.client_id: str = client_id or str(uuid.uuid4())
        self.name: str = name or f"Клиент_{self.client_id[:8]}"
        self.description: str = description
        self.created_at: datetime = datetime.now()
        self.last_interaction: datetime = datetime.now()
        self.tags: List[str] = []  # Теги для категоризации клиентов
        self.metadata: Dict[str, Any] = {}  # Дополнительная информация
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь"""
        return {
            'client_id': self.client_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'last_interaction': self.last_interaction.isoformat(),
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ClientProfile':
        """Создание объекта из словаря"""
        profile = cls(
            client_id=data['client_id'],
            name=data['name'],
            description=data.get('description', '')
        )
        profile.created_at = datetime.fromisoformat(data['created_at'])
        profile.last_interaction = datetime.fromisoformat(data['last_interaction'])
        profile.tags = data.get('tags', [])
        profile.metadata = data.get('metadata', {})
        return profile

class ChatMessage:
    """Сообщение в чате с расширенными метаданными"""
    
    def __init__(self, role: str, content: str, message_type: str = "text"):
        self.message_id: str = str(uuid.uuid4())
        self.role: str = role  # 'user', 'assistant', 'system'
        self.content: str = content
        self.message_type: str = message_type  # 'text', 'flirt', 'ppv', 'tip_request'
        self.timestamp: datetime = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self.context_tags: List[str] = []  # Теги для контекста
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь"""
        return {
            'message_id': self.message_id,
            'role': self.role,
            'content': self.content,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'context_tags': self.context_tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        """Создание объекта из словаря"""
        message = cls(
            role=data['role'],
            content=data['content'],
            message_type=data.get('message_type', 'text')
        )
        message.message_id = data.get('message_id', message.message_id)
        message.timestamp = datetime.fromisoformat(data['timestamp'])
        message.metadata = data.get('metadata', {})
        message.context_tags = data.get('context_tags', [])
        return message

class ClientChat:
    """Чат с конкретным клиентом"""
    
    def __init__(self, client_profile: ClientProfile):
        self.chat_id: str = str(uuid.uuid4())
        self.client_profile: ClientProfile = client_profile
        self.messages: List[ChatMessage] = []
        self.is_active: bool = True
        self.created_at: datetime = datetime.now()
        self.last_activity: datetime = datetime.now()
        
        # Контекстная информация
        self.conversation_stage: str = "initial"  # initial, warming_up, engaged, intimate
        self.client_mood: str = "neutral"  # happy, sad, excited, frustrated, etc.
        self.interaction_pattern: Dict[str, Any] = {
            "response_time": "medium",  # fast, medium, slow
            "message_length": "medium",  # short, medium, long
            "emoji_usage": "moderate",  # none, light, moderate, heavy
            "flirt_receptiveness": "unknown"  # unknown, low, medium, high
        }
        
        # Память о клиенте
        self.client_memory: Dict[str, Any] = {
            "preferences": {},  # Предпочтения клиента
            "interests": [],    # Интересы
            "important_dates": {},  # Важные даты
            "purchase_history": [],  # История покупок
            "communication_notes": []  # Заметки об общении
        }
    
    def add_message(self, message: ChatMessage):
        """Добавление сообщения в чат"""
        self.messages.append(message)
        self.last_activity = datetime.now()
        self.client_profile.last_interaction = datetime.now()
        
        # Автоматическое обновление контекста
        self._update_conversation_context(message)
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Получение последних сообщений"""
        return self.messages[-limit:] if self.messages else []
    
    def get_context_summary(self) -> str:
        """Создание краткого контекста для ИИ"""
        recent_messages = self.get_recent_messages(5)
        
        context_parts = [
            f"Клиент: {self.client_profile.name}",
            f"Этап диалога: {self.conversation_stage}",
            f"Настроение: {self.client_mood}",
        ]
        
        if self.client_memory.get("preferences"):
            prefs = ", ".join(f"{k}: {v}" for k, v in self.client_memory["preferences"].items())
            context_parts.append(f"Предпочтения: {prefs}")
        
        if recent_messages:
            context_parts.append("Последние сообщения:")
            for msg in recent_messages[-3:]:
                context_parts.append(f"- {msg.role}: {msg.content[:100]}...")
        
        return "\n".join(context_parts)
    
    def _update_conversation_context(self, message: ChatMessage):
        """Автоматическое обновление контекста разговора"""
        # Простая эвристика для определения этапа разговора
        if len(self.messages) <= 3:
            self.conversation_stage = "initial"
        elif len(self.messages) <= 10:
            self.conversation_stage = "warming_up"
        elif len(self.messages) <= 20:
            self.conversation_stage = "engaged"
        else:
            self.conversation_stage = "intimate"
        
        # Анализ типа сообщения для обновления памяти
        if message.message_type == "ppv" and message.role == "assistant":
            self.client_memory["purchase_history"].append({
                "type": "ppv_offer",
                "timestamp": message.timestamp.isoformat(),
                "content": message.content[:50]
            })
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь"""
        return {
            'chat_id': self.chat_id,
            'client_profile': self.client_profile.to_dict(),
            'messages': [msg.to_dict() for msg in self.messages],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'conversation_stage': self.conversation_stage,
            'client_mood': self.client_mood,
            'interaction_pattern': self.interaction_pattern,
            'client_memory': self.client_memory
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ClientChat':
        """Создание объекта из словаря"""
        client_profile = ClientProfile.from_dict(data['client_profile'])
        chat = cls(client_profile)
        
        chat.chat_id = data['chat_id']
        chat.messages = [ChatMessage.from_dict(msg) for msg in data['messages']]
        chat.is_active = data.get('is_active', True)
        chat.created_at = datetime.fromisoformat(data['created_at'])
        chat.last_activity = datetime.fromisoformat(data['last_activity'])
        chat.conversation_stage = data.get('conversation_stage', 'initial')
        chat.client_mood = data.get('client_mood', 'neutral')
        chat.interaction_pattern = data.get('interaction_pattern', {})
        chat.client_memory = data.get('client_memory', {})
        
        return chat

class ChatManager:
    """Менеджер для управления множественными чатами"""
    
    def __init__(self, user_id: int):
        self.user_id: int = user_id
        self.chats: Dict[str, ClientChat] = {}  # chat_id -> ClientChat
        self.active_chat_id: Optional[str] = None
        self.created_at: datetime = datetime.now()
    
    def create_chat(self, client_name: str = "", client_description: str = "") -> ClientChat:
        """Создание нового чата с клиентом"""
        client_profile = ClientProfile(name=client_name, description=client_description)
        chat = ClientChat(client_profile)
        
        self.chats[chat.chat_id] = chat
        
        # Если это первый чат, делаем его активным
        if self.active_chat_id is None:
            self.active_chat_id = chat.chat_id
        
        return chat
    
    def get_active_chat(self) -> Optional[ClientChat]:
        """Получение активного чата"""
        if self.active_chat_id and self.active_chat_id in self.chats:
            return self.chats[self.active_chat_id]
        return None
    
    def switch_chat(self, chat_id: str) -> bool:
        """Переключение на другой чат"""
        if chat_id in self.chats:
            self.active_chat_id = chat_id
            return True
        return False
    
    def get_chat_list(self) -> List[Dict[str, Any]]:
        """Получение списка чатов для отображения"""
        chat_list = []
        for chat in self.chats.values():
            last_message = chat.messages[-1] if chat.messages else None
            chat_list.append({
                'chat_id': chat.chat_id,
                'client_name': chat.client_profile.name,
                'is_active': chat.chat_id == self.active_chat_id,
                'message_count': len(chat.messages),
                'last_activity': chat.last_activity,
                'last_message': last_message.content[:50] if last_message else "Новый чат",
                'conversation_stage': chat.conversation_stage
            })
        
        # Сортируем по последней активности
        chat_list.sort(key=lambda x: x['last_activity'], reverse=True)
        return chat_list
    
    def delete_chat(self, chat_id: str) -> bool:
        """Удаление чата"""
        if chat_id in self.chats:
            del self.chats[chat_id]
            
            # Если удален активный чат, переключаемся на другой
            if self.active_chat_id == chat_id:
                remaining_chats = list(self.chats.keys())
                self.active_chat_id = remaining_chats[0] if remaining_chats else None
            
            return True
        return False
    
    def add_message_to_active_chat(self, role: str, content: str, message_type: str = "text") -> bool:
        """Добавление сообщения в активный чат"""
        active_chat = self.get_active_chat()
        if active_chat:
            message = ChatMessage(role, content, message_type)
            active_chat.add_message(message)
            return True
        return False
    
    def get_context_for_ai(self) -> str:
        """Получение контекста для ИИ из активного чата"""
        active_chat = self.get_active_chat()
        if active_chat:
            return active_chat.get_context_summary()
        return "Нет активного чата"
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь"""
        return {
            'user_id': self.user_id,
            'chats': {chat_id: chat.to_dict() for chat_id, chat in self.chats.items()},
            'active_chat_id': self.active_chat_id,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatManager':
        """Создание объекта из словаря"""
        manager = cls(data['user_id'])
        manager.chats = {
            chat_id: ClientChat.from_dict(chat_data) 
            for chat_id, chat_data in data['chats'].items()
        }
        manager.active_chat_id = data.get('active_chat_id')
        manager.created_at = datetime.fromisoformat(data['created_at'])
        return manager 