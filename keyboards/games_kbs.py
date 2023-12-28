from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

games_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚽ Пенальти", callback_data="penalty"),
        ],
        [
            InlineKeyboardButton(
                text="☘ Об удачном ударе", callback_data="luckystrike"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="startplay")
        ]
    ]
)
