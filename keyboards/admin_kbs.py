from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Карточки", callback_data="admincards"),
        ],
        [
            InlineKeyboardButton(
                text="Промокоды", callback_data="adminpromos"),
        ],
        [
            InlineKeyboardButton(
                text="Пользователи", callback_data="adminusers")
        ]
    ]
)

back_to_admin_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

admin_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Добавить", callback_data="addcard"),
        ],
        [
            InlineKeyboardButton(
                text="Редактировать", callback_data="editcards"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

admin_promos_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Добавить", callback_data="addpromo"),
            InlineKeyboardButton(
                text="Удалить", callback_data="delpromos"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)
