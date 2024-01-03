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
                text="☘️ Удачный удар", callback_data="luckystrike"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="startplay")
        ]
    ]
)


lucky_shot_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚽ Сделать удар", callback_data="hitls"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="games")
        ]
    ]
)

no_free_ls_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💵 Купить 3 удара", callback_data="buyls"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="games")
        ]
    ]
)


def penalty_offer_kb(pen_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Начать игру", callback_data=f"penstart_{pen_id}"),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"pencancel_{pen_id}")
            ]
        ]
    )
    return keyboard


after_penalty_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚽ Рейтинг игроков в Пенальти", callback_data="top_penalty"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="games")
        ]
    ]
)
