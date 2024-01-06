from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from keyboards.cb_data import PageCB

duel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎪 Создать своё лобби", callback_data="duelcreate")
        ],
        [
            InlineKeyboardButton(
                text="🏹 Войти в лобби", callback_data="duellobbies")
        ],
        [
            InlineKeyboardButton(
                text="🧑💻 В личный кабинет", callback_data="startplay")
        ]
    ]
)

create_lobby_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Выбрать карты", callback_data="duelcardscreate")
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="duel")
        ]
    ]
)

new_lobby_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Добавить карты", callback_data="duelcardscreate")
        ],
        [
            InlineKeyboardButton(
                text="🎪 Создать лобби", callback_data="duellobbystart")
        ],
        [
            InlineKeyboardButton(
                text="🧑💻 В личный кабинет", callback_data="startplay")
        ]
    ]
)


def duel_first_cards_kb(page, last, sorting, user_card_id, cards):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append([
        InlineKeyboardButton(text=txt, callback_data=f"srtfrstcrds_{sorting}")])
    btns.append([
        InlineKeyboardButton(
            text="⚔️ Добавить в дуэль", callback_data=f"ownrcrtduel_{user_card_id}")])

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

    if cards > 0:
        btns.append([
            InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_owner_lobby")])
    else:
        btns.append([
            InlineKeyboardButton(text="🧑💻 В личный кабинет", callback_data="startplay")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


def no_opp_duel_kb(duel_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            # [
            #     InlineKeyboardButton(
            #         text=f"⚔️ Начать дуэль ({ready}/2)",
            #         callback_data=f"ordy_{duel_id}")
            # ],
            # [
            #     InlineKeyboardButton(
            #         text="🃏 Добавить карты",
            #         callback_data=f"addwnrduelcrds_{duel_id}")
            # ],
            [
                InlineKeyboardButton(
                    text="⚖️ Проверить ставки",
                    callback_data=f"checkbets_{duel_id}")
            ],
            [
                InlineKeyboardButton(
                    text="🧑‍💻 В личный кабинет",
                    callback_data=f"ownrcancelduel_{duel_id}")
            ],
        ]
    )
    return keyboard


def duel_owner_cards_kb(page, last, sorting, user_card_id, duel_id):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append([
        InlineKeyboardButton(text=txt, callback_data=f"srtownrcrds_{sorting}")])
    btns.append([
        InlineKeyboardButton(
            text="⚔️ Добавить в дуэль", callback_data=f"ownrmorcards_{user_card_id}")])

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
        InlineKeyboardButton(text="⏪ Назад", callback_data=f"owntolobby_{duel_id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard
