import asyncio
import logging
from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem, PayItem, Player
from db.queries.games_queries import lucky_shot
from db.queries.global_queries import get_user_info
from db.queries.payment_queries import (add_ls_after_pay, add_new_payment,
                                        cancel_payment, get_payment_info)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.cb_data import PayCB
from keyboards.games_kbs import games_kb, lucky_shot_btn, no_free_ls_btn
from keyboards.main_kbs import main_kb
from keyboards.pay_kbs import pay_kb
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_new_free_card_text
from utils.misc import format_delay_text
from utils.pay_actions import check_bill_for_pay, create_new_bill

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(PayCB.filter(F.act == "cncl"), flags=flags)
async def cancel_payment_cmd(c: CQ, callback_data: PayCB, ssn):
    pay_id = int(callback_data.pay_id)
    user = await cancel_payment(ssn, pay_id, c.from_user.id)

    await c.message.delete()
    txt = f"""
    Твои достижения:

    🃏 Собранное количество карточек: {user.card_quants}
    🏆 Рейтинг собранных карточек: {user.rating}

    ⚽️ Рейтинг в игре Пенальти: {user.penalty_rating}
    """
    await c.message.answer(dedent(txt), reply_markup=main_kb)


@router.callback_query(F.data == "buyls", flags=flags)
async def buy_ls_cmd(c: CQ, wallet, ssn):
    pay_res = await create_new_bill(
        100, c.from_user.id, "3 Lucky Shots", wallet)
    pay_id = await add_new_payment(
        ssn, c.from_user.id, pay_res[0], pay_res[1], "3 Lucky Shots", 100)
    logging.info(
        f"User {c.from_user.id} created new bill {pay_id} label {pay_res[0]} kind ls3")

    txt = "Ваш заказ сформирован\nОплатите его по кнопке ниже"
    await c.message.edit_text(txt, reply_markup=pay_kb(pay_id, pay_res[1], "ls3"))


@router.callback_query(PayCB.filter((F.act == "paid") & (F.kind == "ls3")), flags=flags)
async def paid_ls_cmd(c: CQ, callback_data: PayCB, ssn, yoo_token):
    pay_id = int(callback_data.pay_id)
    pay: PayItem = await get_payment_info(ssn, pay_id)
    # result = await check_bill_for_pay(pay.label, yoo_token)
    result = "found"
    if result == "found":
        await add_ls_after_pay(ssn, c.from_user.id)
        logging.info(
            f"User {c.from_user.id} payd bill {pay_id} label {pay.label} kind {pay.kind}")
        txt = "Успешно ✅!\nКупленные удары уже начисленны вам, время проверить удачу!"
        await c.message.edit_text(txt, reply_markup=lucky_shot_btn)
    else:
        await c.answer("⚠️ Счет не оплачен", show_alert=True)
