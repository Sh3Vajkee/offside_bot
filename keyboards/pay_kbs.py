from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from keyboards.cb_data import PageCB, PayCB


def pay_kb(pay_id, url, kind):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Оплатить", url=url)
            ],
            [
                InlineKeyboardButton(
                    text="Проверить оплату",
                    callback_data=PayCB(pay_id=pay_id, act="paid", kind=kind).pack())
            ],
            [
                InlineKeyboardButton(
                    text="⏪ Назад",
                    callback_data=PayCB(pay_id=pay_id, act="cncl", kind=kind).pack())
            ]
        ]
    )
    return keyboard


def cards_pack_btn(pack_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👀 Посмотреть карты", callback_data=f"viewpack_{pack_id}")
            ]
        ]
    )
    return keyboard
