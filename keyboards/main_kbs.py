from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from utils.const import channel_link

start_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="ℹ️ Информация", callback_data="info")
        ],
        [
            InlineKeyboardButton(
                text="🎮 Начать игру", callback_data="startplay")
        ]
    ]
)

info_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 О картах", callback_data="about_cards")
        ],
        [
            InlineKeyboardButton(
                text="⚽ О пенальти", callback_data="about_penalty")
        ],
        [
            InlineKeyboardButton(
                text="☘ Об удачном ударе", callback_data="about_luckystrike")
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="backtostart")
        ]
    ]
)

back_to_info_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="info")
        ]
    ]
)


main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Получить карту", callback_data="getcard"),
            InlineKeyboardButton(
                text="🧳 Моя коллекция", callback_data="mycards")
        ],
        [
            InlineKeyboardButton(
                text="🎭 Обмен картами", callback_data="trade"),
            InlineKeyboardButton(
                text="🏆 Общий рейтинг", callback_data="rating")
        ],
        [
            InlineKeyboardButton(
                text="🎲 Мини-игры", callback_data="games")
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="backtostart")
        ]
    ]
)

sub_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Подписаться ✓", url=channel_link)
        ],
        [
            InlineKeyboardButton(
                text="🎮 Начать игру", callback_data="startplay")
        ]
    ]
)

to_main_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🧑💻 В личный кабинет", callback_data="startplay")
        ]
    ]
)

back_to_main_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="startplay")
        ]
    ]
)


cancel_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚫 Отменить", callback_data="cancel_cb")
        ]
    ]
)
