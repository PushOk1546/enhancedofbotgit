"""
Модуль утилит.
Содержит вспомогательные функции и классы для работы бота.
"""

import json
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from telebot import types
from config import (
    LOG_DIR, LOG_FILE, MAX_LOG_SIZE, LOG_BACKUP_COUNT,
    MODELS, FLIRT_STYLES, RELATIONSHIP_STAGES, SURVEY_STEPS, PPV_STYLES
)

def setup_logging() -> logging.Logger:
    """Настройка системы логирования"""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # Настройка основного логгера
    logger = logging.getLogger("bot_logger")
    logger.setLevel(logging.INFO)
    
    # Ротируемый файловый обработчик для JSON логов
    json_handler = RotatingFileHandler(
        log_dir / LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=LOG_BACKUP_COUNT
    )
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    json_handler.setFormatter(json_formatter)
    logger.addHandler(json_handler)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    """Создает основную клавиатуру бота"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton('💬 Написать сообщение'),
        types.KeyboardButton('💝 Флирт'),
        types.KeyboardButton('🎁 Платный контент'),
        types.KeyboardButton('🌟 Чаевые'),
        types.KeyboardButton('👥 Чаты с клиентами'),
        types.KeyboardButton('⚙️ Сменить модель'),
        types.KeyboardButton('ℹ️ Помощь')
    )
    return keyboard

def get_model_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру выбора модели"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key, model in MODELS.items():
        keyboard.add(types.InlineKeyboardButton(
            text=model['description'],
            callback_data=f"model_{key}"
        ))
    return keyboard

def get_flirt_style_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру выбора стиля флирта"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for style_name, style_info in FLIRT_STYLES.items():
        keyboard.add(types.InlineKeyboardButton(
            text=f"{style_info['emoji']} {style_info['description']}",
            callback_data=f"flirt_style_{style_info['id']}"
        ))
    return keyboard

def get_relationship_stage_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру выбора этапа отношений"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for stage_name, stage_info in RELATIONSHIP_STAGES.items():
        keyboard.add(types.InlineKeyboardButton(
            text=stage_info['description'],
            callback_data=f"flirt_stage_{stage_name}"
        ))
    return keyboard

def get_survey_keyboard(step: str) -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для текущего шага опроса"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for value, text in SURVEY_STEPS[step]['options']:
        keyboard.add(types.InlineKeyboardButton(
            text=text,
            callback_data=f"survey_{step}_{value}"
        ))
    return keyboard

def get_ppv_style_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру выбора стиля PPV контента"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for style_name, style_desc in PPV_STYLES.items():
        keyboard.add(types.InlineKeyboardButton(
            text=f"💎 {style_name.title()} - {style_desc}",
            callback_data=f"ppv_style_{style_name}"
        ))
    return keyboard

def get_quick_continue_keyboard(last_message: str = "") -> types.InlineKeyboardMarkup:
    """
    🆕 ФАЗЫ 2-3: Создает умную клавиатуру для естественного продолжения диалога
    Анализирует контекст и предлагает наиболее релевантные действия
    """
    keyboard = types.InlineKeyboardMarkup()
    
    # Анализируем последнее сообщение для контекстуальных кнопок
    last_message_lower = last_message.lower()
    
    # Умная логика выбора кнопок на основе контекста
    if any(word in last_message_lower for word in ['привет', 'hello', 'hi']):
        # Контекст: приветствие - предлагаем знакомство
        keyboard.row(
            types.InlineKeyboardButton("😊 Познакомиться ближе", callback_data="get_closer"),
            types.InlineKeyboardButton("💕 Легкий флирт", callback_data="light_flirt")
        )
        keyboard.row(
            types.InlineKeyboardButton("🎁 Показать контент", callback_data="show_content"),
            types.InlineKeyboardButton("💬 Просто пообщаться", callback_data="casual_chat")
        )
    elif any(word in last_message_lower for word in ['фото', 'видео', 'контент']):
        # Контекст: интерес к контенту - предлагаем PPV и флирт
        keyboard.row(
            types.InlineKeyboardButton("🔥 Горячий контент", callback_data="hot_content"),
            types.InlineKeyboardButton("💎 Эксклюзив для тебя", callback_data="exclusive_content")
        )
        keyboard.row(
            types.InlineKeyboardButton("💰 Чаевые за фото", callback_data="tips_for_content"),
            types.InlineKeyboardButton("😏 Интригующий ответ", callback_data="teasing_response")
        )
    elif any(word in last_message_lower for word in ['красивая', 'сексуальная', 'комплимент']):
        # Контекст: комплимент - усиливаем флирт
        keyboard.row(
            types.InlineKeyboardButton("😘 Поблагодарить кокетливо", callback_data="flirty_thanks"),
            types.InlineKeyboardButton("🔥 Усилить флирт", callback_data="escalate_flirt")
        )
        keyboard.row(
            types.InlineKeyboardButton("💕 Вернуть комплимент", callback_data="return_compliment"),
            types.InlineKeyboardButton("🎁 Предложить награду", callback_data="reward_compliment")
        )
    else:
        # Дефолтный контекст - универсальные действия продолжения
        keyboard.row(
            types.InlineKeyboardButton("💬 Продолжить беседу", callback_data="continue_conversation"),
            types.InlineKeyboardButton("💝 Добавить флирт", callback_data="add_flirt")
        )
        keyboard.row(
            types.InlineKeyboardButton("🎁 Предложить контент", callback_data="suggest_content"),
            types.InlineKeyboardButton("😏 Игривый ответ", callback_data="playful_response")
        )
    
    # Всегда доступные быстрые действия (третий ряд)
    keyboard.row(
        types.InlineKeyboardButton("💰 Чаевые", callback_data="quick_tips"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")
    )
    
    return keyboard

def get_smart_continuation_keyboard(context_type: str) -> types.InlineKeyboardMarkup:
    """
    🆕 Создает умную клавиатуру на основе типа контекста
    """
    keyboard = types.InlineKeyboardMarkup()
    
    if context_type == "flirt_mode":
        keyboard.row(
            types.InlineKeyboardButton("💕 Больше флирта", callback_data="more_flirt"),
            types.InlineKeyboardButton("🔥 Усилить страсть", callback_data="escalate_passion")
        )
        keyboard.row(
            types.InlineKeyboardButton("🎁 Особый контент", callback_data="special_content"),
            types.InlineKeyboardButton("💰 За флирт чаевые", callback_data="flirt_tips")
        )
    elif context_type == "content_interest":
        keyboard.row(
            types.InlineKeyboardButton("💎 VIP контент", callback_data="vip_content"),
            types.InlineKeyboardButton("🎁 PPV предложение", callback_data="ppv_offer")
        )
        keyboard.row(
            types.InlineKeyboardButton("😏 Заинтриговать", callback_data="tease_more"),
            types.InlineKeyboardButton("💰 Запросить чаевые", callback_data="request_payment")
        )
    elif context_type == "casual_chat":
        keyboard.row(
            types.InlineKeyboardButton("😊 Поддержать беседу", callback_data="continue_chat"),
            types.InlineKeyboardButton("💝 Перейти к флирту", callback_data="transition_flirt")
        )
        keyboard.row(
            types.InlineKeyboardButton("🎭 Рассказать о себе", callback_data="tell_about_self"),
            types.InlineKeyboardButton("❓ Задать вопрос", callback_data="ask_question")
        )
    
    # Навигация
    keyboard.row(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main"))
    
    return keyboard

def load_json_file(file_path: Path) -> dict:
    """Загружает данные из JSON файла"""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error loading {file_path}: {str(e)}", exc_info=True)
    return {}

def save_json_file(file_path: Path, data: dict) -> None:
    """Сохраняет данные в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving {file_path}: {str(e)}", exc_info=True)

def parse_time_string(time_str: str) -> int:
    """Парсит строку времени в минуты"""
    try:
        value = int(time_str[:-1])
        unit = time_str[-1].lower()
        
        if unit == 'm':
            return value
        elif unit == 'h':
            return value * 60
        elif unit == 'd':
            return value * 60 * 24
        else:
            raise ValueError("Invalid time unit")
    except (ValueError, IndexError):
        raise ValueError("Invalid time format") 