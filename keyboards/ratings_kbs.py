from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

ratings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Рейтинг коллекционеров карточек", callback_data="top_rating")
        ],
        [
            InlineKeyboardButton(
                text="⚽ Рейтинг игроков в Пенальти", callback_data="top_penalty")
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="backtostart")
        ]
    ]
)

back_to_ratings_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="rating")
        ]
    ]
)
