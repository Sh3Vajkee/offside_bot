import asyncio
import logging
from textwrap import dedent

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.models import Duel
from db.queries.craft_queries import craft_card, get_user_duplicates
from db.queries.duel_queries import (add_duel_first_card,
                                     add_target_card_to_duel,
                                     create_duel_lobby,
                                     get_duel_cards_for_create, get_duel_info,
                                     get_user_duel_cards, join_duel,
                                     leave_from_duel, update_msg_ids,
                                     update_owner_msg_id, update_target_msg_id)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.cb_data import PageCB
from keyboards.duel_kbs import (create_lobby_kb, duel_first_cards_kb, duel_kb,
                                duel_owner_cards_kb, duel_target_cards_kb,
                                new_lobby_kb, no_opp_duel_kb, opp_duel_kb)
from keyboards.main_kbs import main_kb, to_main_btn
from middlewares.actions import ActionMiddleware
from utils.duel_misc import (check_duel_timer, format_duel_lobby_text,
                             resent_lobby_info)
from utils.format_texts import (format_craft_text, format_new_free_card_text,
                                format_view_my_cards_text)
from utils.states import DuelStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data.startswith("joinduel_"), flags=flags)
async def join_duel_cmd(c: CQ, action_queue, ssn, bot: Bot, db):
    duel_id = int(c.data.split("_")[-1])

    if c.from_user.username:
        username = f"@{c.from_user.username}"
    else:
        username = c.from_user.mention_html()

    duel = await join_duel(
        ssn, c.from_user.id, username, duel_id, c.message.message_id)
    if duel == "already_playing":
        txt = "Вы уже состоите в дуэли, закончите ее, чтобы начать следующую"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    elif duel == "not_available":
        txt = "Вы не можете присоединиться к этой дуэли"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    else:
        logging.info(f"User {c.from_user.id} joined duel {duel_id}")
        txts = await format_duel_lobby_text(duel)
        await c.message.edit_text(txts[1], reply_markup=opp_duel_kb(duel_id, "target", 0))

        try:
            await bot.send_message(duel.owner, "🟠 Соперник зашел в лобби!")
        except Exception as error:
            logging.error(f"Send error | chat {duel.owner}\n{error}")

        msg_id = await resent_lobby_info(
            bot, duel, "owner", txts[0], opp_duel_kb(duel_id, "owner", 0))
        await update_owner_msg_id(ssn, duel_id, msg_id)
        asyncio.create_task(check_duel_timer(
            db, bot, duel_id, "target", c.from_user.id, duel.target_ts, 60))
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("targetcancelduel_"), flags=flags
)
async def target_duel_cancel_cmd(c: CQ, ssn, bot: Bot, action_queue):
    duel_id = int(c.data.split("_")[-1])
    duel = await leave_from_duel(ssn, c.from_user.id, duel_id)
    if duel == "not_available":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=duel_kb)
    else:
        txt = f"""
        Твои достижения:

        🃏 Собранное количество карточек: {duel[1].card_quants}
        🏆 Рейтинг собранных карточек: {duel[1].rating}

        ⚽️ Рейтинг в игре Пенальти: {duel[1].penalty_rating}
        """
        await c.message.edit_text(dedent(txt), reply_markup=main_kb)
        logging.info(f"User {c.from_user.id} left from duel {duel_id}")

        owner_txt = await format_duel_lobby_text(duel[0])
        msg_id = await resent_lobby_info(
            bot, duel[0], "owner", owner_txt[0], no_opp_duel_kb(duel_id))
        await update_owner_msg_id(ssn, duel_id, msg_id)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("addtrgduelcrds_"), flags={"throttling_key": "pages"}
)
async def add_duel_target_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    duel_id = int(c.data.split("_")[-1])

    res = await get_user_duel_cards(
        ssn, c.from_user.id, "nosort", duel_id, "target")
    if res == "not_available":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    elif res == "limit":
        await c.answer("Ты не можешь добавить больше 5 карт")
    else:
        cards = res[0]
        if len(cards) == 0:
            await c.answer("У тебя больше нет карт для дуэли")
        else:
            page = 1
            last = len(cards)

            await c.message.delete()

            txt = await format_view_my_cards_text(cards[0].card)
            msg = await c.message.answer_photo(
                cards[0].card.image, txt,
                reply_markup=duel_target_cards_kb(page, last, "nosort", cards[0].id, duel_id))
            await update_target_msg_id(ssn, duel_id, msg.message_id)
            await state.set_state(DuelStates.target_cards)
            await state.update_data(cards=cards, sorting="nosort", duel_id=duel_id)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("srttrgtcrds_"), flags={"throttling_key": "pages"}
)
async def view_sorted_duel_target_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    data = await state.get_data()
    duel_id = data.get("duel_id")

    res = await get_user_duel_cards(
        ssn, c.from_user.id, sorting, duel_id, "target")
    cards = res[0]

    page = 1
    last = len(cards)
    txt = await format_view_my_cards_text(cards[0].card)
    media = types.InputMediaPhoto(caption=txt, media=cards[0].card.image)
    try:
        await c.message.edit_media(
            media=media, reply_markup=duel_target_cards_kb(
                page, last, sorting, cards[0].id, duel_id))
        await state.update_data(cards=cards, sorting=sorting)
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.target_cards),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_target_duel_cards_cmd(c: CQ, state: FSM, callback_data: PageCB, action_queue):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")
    duel_id = data.get("duel_id")

    card = cards[page-1]
    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)
    try:
        await c.message.edit_media(
            media=media, reply_markup=duel_target_cards_kb(
                page, last, sorting, card.id, duel_id))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.target_cards),
    F.data.startswith("trgtmorcards_"), flags=flags
)
async def add_duel_target_cards_cmd(c: CQ, ssn, state: FSM, action_queue, bot: Bot, db):
    u_card_id = int(c.data.split("_")[-1])

    data = await state.get_data()
    duel_id = data.get("duel_id")
    duel = await add_target_card_to_duel(ssn, c.from_user.id, duel_id, u_card_id)
    if duel == "not_available":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    else:
        await c.message.delete()
        await c.message.answer("⚔️ Карта добавлена на дуэль")
        txts = await format_duel_lobby_text(duel)
        msg = await c.message.answer(
            txts[1],
            reply_markup=opp_duel_kb(duel_id, "target", 0))
        target_msg_id = msg.message_id

        try:
            await bot.send_message(duel.owner, "⚔️ Соперник добавил карту на дуэль")
        except Exception as error:
            logging.error(f"Send error | chat {duel.owner}\n{error}")
        owner_msg_id = await resent_lobby_info(
            bot, duel, "owner", txts[0], opp_duel_kb(duel_id, "owner", 0))
        await update_msg_ids(ssn, duel_id, owner_msg_id, target_msg_id)
        asyncio.create_task(check_duel_timer(
            db, bot, duel_id, "target", c.from_user.id, duel.target_ts, 60))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("trgttolobby_"), flags=flags
)
async def target_back_to_lobby_cmd(c: CQ, ssn, action_queue):
    duel_id = int(c.data.split("_")[-1])

    duel = await get_duel_info(ssn, duel_id, c.from_user.id)
    if duel == "not_available":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    else:
        await c.message.delete()
        txts = await format_duel_lobby_text(duel)
        msg = await c.message.answer(
            txts[1],
            reply_markup=opp_duel_kb(
                duel_id, "target", duel.owner_ready + duel.target_ready))
        await update_target_msg_id(ssn, duel_id, msg.message_id)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
