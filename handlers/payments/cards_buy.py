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
from db.queries.payment_queries import (add_cards_pack, add_leg_card_pack,
                                        add_ls_after_pay, add_new_payment,
                                        cancel_payment, get_payment_info)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.cb_data import PayCB
from keyboards.games_kbs import games_kb, lucky_shot_btn, no_free_ls_btn
from keyboards.main_kbs import main_kb
from keyboards.pay_kbs import cards_pack_btn, pay_kb
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_new_free_card_text
from utils.misc import format_delay_text
from utils.pay_actions import check_bill_for_pay, create_new_bill

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data.startswith("cardbuy_"), flags=flags)
async def buy_ls_cmd(c: CQ, wallet, ssn, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    quant = c.data.split("_")[-1]
    if quant == "leg":
        kind = "Legendary Box"
        k = "leg"
        amount = 990
    elif quant == "50":
        kind = "50 Cards"
        k = "cards50"
        amount = 1990
    elif quant == "10":
        kind = "10 Cards"
        k = "cards10"
        amount = 425
    elif quant == "5":
        kind = "5 Cards"
        k = "cards5"
        amount = 245
    else:
        kind = "3 Cards"
        k = "cards3"
        amount = 170

    pay_res = await create_new_bill(
        amount, c.from_user.id, kind, wallet)
    pay_id = await add_new_payment(
        ssn, c.from_user.id, pay_res[0], pay_res[1], kind, amount)
    logging.info(
        f"User {c.from_user.id} created new bill {pay_id} label {pay_res[0]} kind {k}")

    txt = "Ваш заказ сформирован\nОплатите его по кнопке ниже"
    await c.message.edit_text(txt, reply_markup=pay_kb(pay_id, pay_res[1], k))


@router.callback_query(PayCB.filter((F.act == "paid") & (F.kind == "leg")), flags=flags)
async def paid_leg_cardpack_cmd(c: CQ, callback_data: PayCB, ssn, yoo_token, action_queue, bot: Bot):
    pay_id = int(callback_data.pay_id)
    pay: PayItem = await get_payment_info(ssn, pay_id)
    # result = await check_bill_for_pay(pay.label, yoo_token)
    result = "found"
    if result == "found":
        await bot.send_chat_action(c.from_user.id, "typing")
        pack_id = await add_leg_card_pack(ssn, c.from_user.id)
        logging.info(
            f"User {c.from_user.id} payd bill {pay_id} label {pay.label} kind {pay.kind}")
        txt = "Успешно ✅!\nПолучите ваш заказ!"
        await c.message.edit_text(txt, reply_markup=cards_pack_btn(pack_id))
    else:
        await c.answer("⚠️ Счет не оплачен", show_alert=True)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    PayCB.filter((F.act == "paid") & (F.kind.in_(
        {"cards3", "cards5", "cards10", "cards50"}))),
    flags=flags
)
async def paid_cardpack_cmd(c: CQ, callback_data: PayCB, ssn, yoo_token, action_queue, bot: Bot):
    pay_id = int(callback_data.pay_id)
    pay: PayItem = await get_payment_info(ssn, pay_id)
    # result = await check_bill_for_pay(pay.label, yoo_token)
    result = "found"
    if result == "found":
        kind = callback_data.kind
        quant = int(kind[5:])
        await bot.send_chat_action(c.from_user.id, "typing")
        pack_id = await add_cards_pack(ssn, c.from_user.id, quant)
        logging.info(
            f"User {c.from_user.id} payd bill {pay_id} label {pay.label} kind {pay.kind}")
        txt = "Успешно ✅!\nПолучите ваш заказ!"
        await c.message.edit_text(txt, reply_markup=cards_pack_btn(pack_id))
    else:
        await c.answer("⚠️ Счет не оплачен", show_alert=True)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
