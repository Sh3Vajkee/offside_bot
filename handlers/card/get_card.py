import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem
from db.queries.card_queries import get_free_card, use_promo
from keyboards.cards_kbs import (accept_new_card_btn, back_to_cards_kb,
                                 card_kb, no_free_card_kb)
from keyboards.main_kbs import back_to_main_btn
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_new_free_card_text
from utils.misc import format_delay_text
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "getcard", flags=flags)
async def get_card_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = """
    🃏 Если ты хочешь получить карточку, то ты попал куда надо!

    Раз в 24 часа ты можешь получать одну карточку бесплатно, но если ты хочешь продвигаться по таблице рейтинга быстрее других и пополнять свою коллекцию, то рекомендуем тебе посетить магазин карт 🛍
    """
    await c.message.edit_text(dedent(txt), reply_markup=card_kb)


@router.callback_query(F.data == "getfreecard", flags=flags)
async def get_free_card_cmd(c: CQ, ssn, action_queue):
    card: CardItem = await get_free_card(ssn, c.from_user.id)
    if isinstance(card, int):
        timer = await format_delay_text(card)
        txt = f"Ты недавно получал свою бесплатную карточку! Следующую ты можешь получить через {timer} ⏱️. Если не хочешь ждать - приобретай дополнительные карточки"
        await c.message.edit_text(txt, reply_markup=no_free_card_kb)
    elif card == "no_cards":
        await c.answer("⚠️ Возникла ошибка! Попробуй позже")
    else:
        txt = await format_new_free_card_text(card)
        await c.message.delete()
        await c.message.answer_photo(
            card.image, txt, reply_markup=accept_new_card_btn)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data == "promo", flags=flags)
async def user_promo_cmd(c: CQ, ssn, action_queue, state: FSM):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = "Введите промокод ниже"
    await c.message.edit_text(txt, reply_markup=back_to_main_btn)
    await state.set_state(UserStates.promo_text)


@router.message(StateFilter(UserStates.promo_text), flags=flags)
async def use_promo_cmd(m: Mes, state: FSM, ssn):
    await state.clear()

    text = m.text

    card = await use_promo(ssn, m.from_user.id, text)
    if card == "not_found":
        txt = "Увы, но такого промокода не существует, либо он больше недействительный 😔"
        await m.answer(txt, reply_markup=back_to_cards_kb)
    elif card == "already_used":
        txt = "Вы уже использовали этот промокод 😔"
        await m.answer(txt, reply_markup=back_to_cards_kb)
    else:
        txt = await format_new_free_card_text(card)
        await m.answer_photo(
            card.image, txt, reply_markup=accept_new_card_btn)
