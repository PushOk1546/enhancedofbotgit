"""
Утилиты для управления множественными чатами с клиентами.
Создание клавиатур, форматирование и вспомогательные функции.
"""

from telebot import types
from typing import List, Dict, Any
from datetime import datetime, timedelta
from chat_models import ChatManager, ClientChat

def get_chat_management_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для управления чатами"""
    keyboard = types.InlineKeyboardMarkup()
    
    # Первый ряд - основные действия
    keyboard.row(
        types.InlineKeyboardButton("💬 Список чатов", callback_data="chat_list"),
        types.InlineKeyboardButton("➕ Новый чат", callback_data="chat_new")
    )
    
    # Второй ряд - управление текущим чатом
    keyboard.row(
        types.InlineKeyboardButton("📝 Переименовать", callback_data="chat_rename"),
        types.InlineKeyboardButton("🗑 Удалить чат", callback_data="chat_delete")
    )
    
    # Третий ряд - анализ и память
    keyboard.row(
        types.InlineKeyboardButton("🧠 Память клиента", callback_data="chat_memory"),
        types.InlineKeyboardButton("📊 Аналитика", callback_data="chat_analytics")
    )
    
    # Четвертый ряд - назад
    keyboard.row(
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    
    return keyboard

def get_chat_list_keyboard(chat_manager: ChatManager, page: int = 0, items_per_page: int = 5) -> types.InlineKeyboardMarkup:
    """Создает клавиатуру со списком чатов"""
    keyboard = types.InlineKeyboardMarkup()
    
    chat_list = chat_manager.get_chat_list()
    total_chats = len(chat_list)
    
    # Пагинация
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, total_chats)
    page_chats = chat_list[start_idx:end_idx]
    
    # Добавляем кнопки для каждого чата
    for chat_info in page_chats:
        # Формируем текст кнопки
        status_emoji = "🟢" if chat_info['is_active'] else "⚪"
        stage_emoji = get_stage_emoji(chat_info['conversation_stage'])
        
        button_text = f"{status_emoji} {stage_emoji} {chat_info['client_name'][:20]}"
        callback_data = f"chat_switch_{chat_info['chat_id']}"
        
        keyboard.row(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Навигация по страницам
    if total_chats > items_per_page:
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"chat_list_page_{page-1}"))
        
        nav_buttons.append(types.InlineKeyboardButton(
            f"📄 {page+1}/{(total_chats-1)//items_per_page + 1}", 
            callback_data="chat_list_info"
        ))
        
        if end_idx < total_chats:
            nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"chat_list_page_{page+1}"))
        
        keyboard.row(*nav_buttons)
    
    # Кнопки управления
    keyboard.row(
        types.InlineKeyboardButton("➕ Новый чат", callback_data="chat_new"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="chat_management")
    )
    
    return keyboard

def get_chat_context_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для работы в контексте активного чата"""
    keyboard = types.InlineKeyboardMarkup()
    
    # Первый ряд - генерация контента
    keyboard.row(
        types.InlineKeyboardButton("💬 Ответить", callback_data="chat_reply"),
        types.InlineKeyboardButton("💝 Флирт", callback_data="chat_flirt")
    )
    
    # Второй ряд - коммерческие функции
    keyboard.row(
        types.InlineKeyboardButton("🎁 PPV", callback_data="chat_ppv"),
        types.InlineKeyboardButton("💰 Чаевые", callback_data="chat_tips")
    )
    
    # Третий ряд - управление чатом
    keyboard.row(
        types.InlineKeyboardButton("📝 Заметка", callback_data="chat_note"),
        types.InlineKeyboardButton("🏷 Теги", callback_data="chat_tags")
    )
    
    # Четвертый ряд - переключение и управление
    keyboard.row(
        types.InlineKeyboardButton("🔄 Сменить чат", callback_data="chat_list"),
        types.InlineKeyboardButton("⚙️ Управление", callback_data="chat_management")
    )
    
    return keyboard

def get_stage_emoji(stage: str) -> str:
    """Возвращает эмодзи для этапа разговора"""
    stage_emojis = {
        "initial": "🌱",
        "warming_up": "🔥",
        "engaged": "💕",
        "intimate": "😍"
    }
    return stage_emojis.get(stage, "💬")

def format_chat_info(chat: ClientChat) -> str:
    """Форматирует информацию о чате для отображения"""
    last_message = chat.messages[-1] if chat.messages else None
    last_msg_preview = last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else (last_message.content if last_message else "Новый чат")
    
    # Время последней активности
    time_diff = datetime.now() - chat.last_activity
    if time_diff < timedelta(hours=1):
        time_str = f"{int(time_diff.total_seconds() // 60)} мин. назад"
    elif time_diff < timedelta(days=1):
        time_str = f"{int(time_diff.total_seconds() // 3600)} ч. назад"
    else:
        time_str = f"{int(time_diff.days)} дн. назад"
    
    stage_emoji = get_stage_emoji(chat.conversation_stage)
    
    info = f"""💬 **{chat.client_profile.name}**
{stage_emoji} Этап: {chat.conversation_stage}
💌 Сообщений: {len(chat.messages)}
🕒 Последняя активность: {time_str}

📝 **Последнее сообщение:**
_{last_msg_preview}_

"""
    
    # Добавляем информацию о памяти клиента, если есть
    if chat.client_memory.get("preferences"):
        prefs = ", ".join(f"{k}: {v}" for k, v in list(chat.client_memory["preferences"].items())[:3])
        info += f"🧠 **Предпочтения:** {prefs}\n"
    
    if chat.client_memory.get("interests"):
        interests = ", ".join(chat.client_memory["interests"][:3])
        info += f"❤️ **Интересы:** {interests}\n"
    
    return info

def format_chat_memory(chat: ClientChat) -> str:
    """Форматирует память о клиенте"""
    memory_text = f"🧠 **Память о клиенте: {chat.client_profile.name}**\n\n"
    
    # Основная информация
    memory_text += f"🆔 ID: `{chat.client_profile.client_id[:8]}...`\n"
    memory_text += f"📅 Знакомы с: {chat.created_at.strftime('%Y-%m-%d')}\n"
    memory_text += f"🎭 Этап отношений: {chat.conversation_stage}\n"
    memory_text += f"😊 Настроение: {chat.client_mood}\n\n"
    
    # Предпочтения
    if chat.client_memory.get("preferences"):
        memory_text += "💝 **Предпочтения:**\n"
        for key, value in chat.client_memory["preferences"].items():
            memory_text += f"• {key}: {value}\n"
        memory_text += "\n"
    
    # Интересы
    if chat.client_memory.get("interests"):
        interests = ", ".join(chat.client_memory["interests"])
        memory_text += f"❤️ **Интересы:** {interests}\n\n"
    
    # История покупок
    if chat.client_memory.get("purchase_history"):
        memory_text += "💰 **История покупок:**\n"
        for purchase in chat.client_memory["purchase_history"][-3:]:  # Последние 3
            memory_text += f"• {purchase.get('type', 'покупка')}: {purchase.get('content', '')[:30]}...\n"
        memory_text += "\n"
    
    # Паттерны взаимодействия
    memory_text += "📊 **Паттерны общения:**\n"
    pattern = chat.interaction_pattern
    memory_text += f"• Скорость ответа: {pattern.get('response_time', 'unknown')}\n"
    memory_text += f"• Длина сообщений: {pattern.get('message_length', 'unknown')}\n"
    memory_text += f"• Использование эмодзи: {pattern.get('emoji_usage', 'unknown')}\n"
    memory_text += f"• Восприимчивость к флирту: {pattern.get('flirt_receptiveness', 'unknown')}\n\n"
    
    # Заметки
    if chat.client_memory.get("communication_notes"):
        memory_text += "📝 **Заметки:**\n"
        for note in chat.client_memory["communication_notes"][-3:]:  # Последние 3
            memory_text += f"• {note}\n"
    
    return memory_text

def format_chat_analytics(chat_manager: ChatManager) -> str:
    """Форматирует аналитику по всем чатам"""
    analytics_text = "📊 **Аналитика чатов**\n\n"
    
    chats = list(chat_manager.chats.values())
    total_chats = len(chats)
    
    if total_chats == 0:
        return "📊 **Аналитика чатов**\n\nНет активных чатов."
    
    # Общая статистика
    total_messages = sum(len(chat.messages) for chat in chats)
    active_chats = len([chat for chat in chats if chat.is_active])
    
    analytics_text += f"📈 **Общая статистика:**\n"
    analytics_text += f"• Всего чатов: {total_chats}\n"
    analytics_text += f"• Активные чаты: {active_chats}\n"
    analytics_text += f"• Всего сообщений: {total_messages}\n"
    analytics_text += f"• Среднее сообщений на чат: {total_messages // total_chats if total_chats > 0 else 0}\n\n"
    
    # Статистика по этапам
    stage_counts = {}
    for chat in chats:
        stage = chat.conversation_stage
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    analytics_text += f"🎭 **По этапам отношений:**\n"
    for stage, count in stage_counts.items():
        emoji = get_stage_emoji(stage)
        analytics_text += f"• {emoji} {stage}: {count} чатов\n"
    analytics_text += "\n"
    
    # Топ-3 самых активных чата
    most_active = sorted(chats, key=lambda x: len(x.messages), reverse=True)[:3]
    analytics_text += f"🔥 **Самые активные чаты:**\n"
    for i, chat in enumerate(most_active, 1):
        analytics_text += f"{i}. {chat.client_profile.name}: {len(chat.messages)} сообщений\n"
    
    return analytics_text

def create_chat_context_prompt(chat: ClientChat, user_message: str = "") -> str:
    """Создает контекстный промпт для ИИ с учетом истории чата"""
    context = f"""Ты общаешься с клиентом {chat.client_profile.name}.

Контекст отношений:
- Этап: {chat.conversation_stage}
- Настроение клиента: {chat.client_mood}
- Всего сообщений в истории: {len(chat.messages)}

"""
    
    # Добавляем память о клиенте
    if chat.client_memory.get("preferences"):
        context += "Предпочтения клиента:\n"
        for key, value in chat.client_memory["preferences"].items():
            context += f"- {key}: {value}\n"
        context += "\n"
    
    if chat.client_memory.get("interests"):
        interests = ", ".join(chat.client_memory["interests"])
        context += f"Интересы: {interests}\n\n"
    
    # Последние сообщения для контекста
    recent_messages = chat.get_recent_messages(5)
    if recent_messages:
        context += "Последние сообщения:\n"
        for msg in recent_messages:
            context += f"{msg.role}: {msg.content}\n"
        context += "\n"
    
    # Паттерны общения
    pattern = chat.interaction_pattern
    context += f"Стиль общения клиента: {pattern.get('message_length', 'unknown')} сообщения, {pattern.get('emoji_usage', 'unknown')} эмодзи\n"
    context += f"Восприимчивость к флирту: {pattern.get('flirt_receptiveness', 'unknown')}\n\n"
    
    if user_message:
        context += f"Новое сообщение от клиента: {user_message}\n\n"
    
    context += """Создай ответ, учитывая всю эту информацию. Будь естественной, поддерживай установленную динамику отношений и помни предыдущий контекст общения."""
    
    return context 