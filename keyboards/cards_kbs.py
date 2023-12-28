from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from keyboards.cb_data import PageCB

card_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎁 Получить бесплатную карточку", callback_data="getfreecard"),
        ],
        [
            InlineKeyboardButton(
                text="🛍 Магазин карточек", callback_data="cardsstore"),
        ],
        [
            InlineKeyboardButton(
                text="🧑‍💻 Ввести промокод", callback_data="promo"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="startplay")
        ]
    ]
)


no_free_card_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🛍 Магазин карточек", callback_data="cardsstore"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="startplay")
        ]
    ]
)


accept_new_card_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Принять", callback_data="startplay")
        ]
    ]
)


buy_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💵 Купить 3 рандомных карточки", callback_data="cardbuy_3"),
        ],
        [
            InlineKeyboardButton(
                text="💵 Купить 5 рандомных карточки", callback_data="cardbuy_5"),
        ],
        [
            InlineKeyboardButton(
                text="💵 Купить 10 рандомных карточки", callback_data="cardbuy_10"),
        ],
        [
            InlineKeyboardButton(
                text="💵 Купить 50 рандомных карточки", callback_data="cardbuy_50"),
        ],
        [
            InlineKeyboardButton(
                text="💵 Купить Легендарный набор", callback_data="cardbuy_50"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="startplay")
        ]
    ]
)


filter_my_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Все карты", callback_data="rarity_all"),
        ],
        [
            InlineKeyboardButton(
                text="🀄 По редкости", callback_data="mycardsrarities"),
        ],
        [
            InlineKeyboardButton(
                text="📋 Посмотреть списком", callback_data="list_my_cards"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="startplay")
        ]
    ]
)


def my_cards_kb(page, last, sorting):
    page_btns = []
    if page > 1:
        page_btns.append(InlineKeyboardButton(
            text="<<", callback_data=PageCB(num=1, last=last).pack()))
        page_btns.append(InlineKeyboardButton(
            text="<", callback_data=PageCB(num=page-1, last=last).pack()))

    page_btns.append(InlineKeyboardButton(
        text=f"({page}/{last})", callback_data="useless"))

    if page < last:
        page_btns.append(InlineKeyboardButton(
            text=">", callback_data=PageCB(num=page+1, last=last).pack()))
        page_btns.append(InlineKeyboardButton(
            text=">>", callback_data=PageCB(num=last, last=last).pack()))

    btns = [page_btns]

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append([
        InlineKeyboardButton(text=txt, callback_data=f"sortmycards_{sorting}")])
    btns.append([
        InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_mycards")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


my_card_rarities_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Обычные", callback_data="rarity_ОБЫЧНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Необычные", callback_data="rarity_НЕОБЫЧНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Редкие", callback_data="rarity_РЕДКАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Эпические", callback_data="rarity_ЭПИЧЕСКАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Уникальные", callback_data="rarity_УНИКАЛЬНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Легендарные", callback_data="rarity_ЛЕГЕНДАРНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Эксклюзивные", callback_data="rarity_ЭКСКЛЮЗИВНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Мифические", callback_data="rarity_МИФИЧЕСКАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_mycards")
        ]
    ]
)


my_card_list_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Получить карту", callback_data="getcard"),
        ],
        [
            InlineKeyboardButton(
                text="📲 Начать просмотр по карточкам", callback_data="rarity_all"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_mycards")
        ]
    ]
)
