from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from keyboards.cb_data import PageCB

trade_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Все карты", callback_data=f"trdrar_all")
        ],
        [
            InlineKeyboardButton(
                text="🀄 По редкости", callback_data=f"traderarities")
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить активные обмены", callback_data="cancel_all_trades")
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="backtostart")
        ]
    ]
)


def card_trade_kb(page, last, sorting, card_id):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append([
        InlineKeyboardButton(text=txt, callback_data=f"sorttrd_{sorting}")])
    btns.append([
        InlineKeyboardButton(
            text="Выбрать для обмена", callback_data=f"chstrdcard_{card_id}")])

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
        InlineKeyboardButton(
            text="❌Отклонить обмен", callback_data="cancel_trade")])
    btns.append([
        InlineKeyboardButton(
            text="⏪ Назад", callback_data="trade")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


def offer_to_owner_kb(trade_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"accepttrade_{trade_id}")
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить обмен",
                    callback_data=f"ownerdeclinetrade_{trade_id}")
            ]
        ]
    )
    return keyboard


def offer_to_target_kb(trade_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Выбрать карту для обмена",
                    callback_data=f"answertrade_{trade_id}")
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить обмен",
                    callback_data=f"targetdeclinetrade_{trade_id}")
            ]
        ]
    )
    return keyboard


def target_cards_kb(trade_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Все карты", callback_data=f"answtrdrar_all_{trade_id}")
            ],
            [
                InlineKeyboardButton(
                    text="🀄 По редкости", callback_data=f"answtraderarities_{trade_id}")
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить активные обмены", callback_data="cancel_all_trades")
            ],
            [
                InlineKeyboardButton(
                    text="⏪ Назад", callback_data="backtostart")
            ]
        ]
    )
    return keyboard


def target_card_trade_kb(page, last, sorting, card_id, trade_id):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append([
        InlineKeyboardButton(text=txt, callback_data=f"answsorttrd_{sorting}")])
    btns.append([
        InlineKeyboardButton(
            text="Выбрать для обмена", callback_data=f"answtrdcard_{card_id}")])

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
        InlineKeyboardButton(
            text="❌Отклонить обмен",
            callback_data=f"targetdeclinetrade_{trade_id}")])
    btns.append([
        InlineKeyboardButton(
            text="⏪ Назад", callback_data=f"answertrade_{trade_id}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard
