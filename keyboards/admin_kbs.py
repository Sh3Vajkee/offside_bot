from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from db.models import PromoCode
from keyboards.cb_data import PageCB

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

admin_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Все карты", callback_data="admrarity_all"),
        ],
        [
            InlineKeyboardButton(
                text="🀄 По редкости", callback_data="admcardsrarities"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

adm_card_rarities_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Обычные", callback_data="admrarity_ОБЫЧНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Необычные", callback_data="admrarity_НЕОБЫЧНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Редкие", callback_data="admrarity_РЕДКАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Эпические", callback_data="admrarity_ЭПИЧЕСКАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Уникальные", callback_data="admrarity_УНИКАЛЬНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Легендарные", callback_data="admrarity_ЛЕГЕНДАРНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Эксклюзивные", callback_data="admrarity_ЭКСКЛЮЗИВНАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="Мифические", callback_data="admrarity_МИФИЧЕСКАЯ"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)


def adm_view_cards_kb(page, last, card_id, kind):
    btns = []

    if kind == "edit":
        btns.append([
            InlineKeyboardButton(text="Изменить картинку", callback_data=f"imgedit_{card_id}")])
        btns.append([
            InlineKeyboardButton(text="Изменить характеристики", callback_data=f"txtedit_{card_id}")])
    else:
        btns.append([
            InlineKeyboardButton(text="Выбрать для промокода", callback_data=f"prmcard_{card_id}")])

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

    btns.append(page_btns)

    btns.append([
        InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_admin")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


promo_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Выбрать карточку",
                                 callback_data="choosepromocard")
        ],
        [
            InlineKeyboardButton(text="Рандомная карточка",
                                 callback_data="randompromocards")
        ],
        [
            InlineKeyboardButton(text="⏪ Назад",
                                 callback_data="back_to_admin")
        ]
    ]
)


def view_promos_kb(promos):
    btns = []
    promo: PromoCode
    for promo in promos:
        btns.append(
            [InlineKeyboardButton(
                text=f"{promo.promo} - {promo.card_id}",
                callback_data=f"delpromo_{promo.id}")]
        )

    btns.append([
        InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_admin")])

    return InlineKeyboardMarkup(inline_keyboard=btns)
