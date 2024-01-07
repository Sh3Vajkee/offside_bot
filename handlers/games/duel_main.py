import asyncio
import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ

from db.queries.craft_queries import craft_card, get_user_duplicates
from db.queries.duel_queries import (duel_user_ready, get_active_duel_lobbies,
                                     get_duel_cards, update_owner_msg_id,
                                     update_target_msg_id)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.duel_kbs import duel_kb, lobbies_kb, opp_duel_kb, rooms_kb
from keyboards.main_kbs import close_window_btn
from middlewares.actions import ActionMiddleware
from utils.duel_misc import (check_duel_timer, create_lobbies_btns,
                             format_duel_cards, format_duel_lobby_text,
                             resent_lobby_info, send_duel_finish_messages)
from utils.format_texts import format_craft_text, format_new_free_card_text

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "duel", flags=flags)
async def duel_cmd(c: CQ, action_queue):
    txt = """
    ⚔️ В Дуэли карт ты ставишь свои карты на кон против других игроков.
    Один игрок может поставить на кон 5 карт любой редкости.

    За победу ты получаешь карты противника, которые он поставил на дуэль.
    За поражение - теряешь свои, которые поставил на дуэль.

    Ты можешь либо создать свое лобби, либо войти в лобби другого игрока
    """
    await c.message.edit_text(dedent(txt), reply_markup=duel_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data == "duellobbies", flags=flags)
async def duel_rooms_cmd(c: CQ, action_queue):
    txt = """
    🏹 Выбери подходящую комнату
    Комнаты отсортированы по количеству очков на дуэли
    От меньшего к большему

    🎪 Список активных комнат:
    """
    await c.message.edit_text(dedent(txt), reply_markup=rooms_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("duelroom_"), flags=flags)
async def duel_rooms_cmd(c: CQ, action_queue, ssn):
    data = c.data.split("_")
    duels = await get_active_duel_lobbies(ssn, int(data[1]), int(data[2]))
    if len(duels) == 0:
        await c.answer("В этой комнате нет активных лобби")
    else:
        txt = "🎪 Список активных лобби:"
        btns = await create_lobbies_btns(duels)
        await c.message.edit_text(dedent(txt), reply_markup=lobbies_kb(btns))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("checkbets_"), flags=flags)
async def duel_rooms_cmd(c: CQ, action_queue, ssn):
    duel_id = int(c.data.split("_")[-1])
    res = await get_duel_cards(ssn, c.from_user.id, duel_id)
    if res == "not_available":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=duel_kb)
    else:
        txt = await format_duel_cards(res[0], res[1], res[2])
        await c.message.answer(txt, reply_markup=close_window_btn)
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("rdyduel_"), flags=flags)
async def duel_ready_cmd(c: CQ, action_queue, ssn, bot, db):
    duel_id = int(c.data.split("_")[-1])
    res = await duel_user_ready(ssn, c.from_user.id, duel_id)
    if res == "not_available":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=duel_kb)
    elif res == "already_ready":
        await c.answer("Вы уже подтвердили готовность!")
    elif res == "target_cards_not_found":
        await c.answer(
            "Вы не можете подтвердить готовность пока соперник не добавил хотябы одну карту")
    elif res == "your_cards_not_found":
        await c.answer(
            "Вы не можете подтвердить готовность пока не добавили хотябы одну карту")
    else:
        if res[1] == "error":
            txt = "Возникла ошибка! Попробуйте позже"
            await c.message.edit_text(txt, reply_markup=duel_kb)
        elif res[1] == "not_ready":
            txts = await format_duel_lobby_text(res[0])
            if res[0].owner == c.from_user.id:
                await c.message.edit_reply_markup(
                    reply_markup=opp_duel_kb(duel_id, "owner", 1))
                msg_id = await resent_lobby_info(
                    bot, res[0], "target", txts[0], opp_duel_kb(duel_id, "target", 1))
                await update_target_msg_id(ssn, duel_id, msg_id)
            else:
                await c.message.edit_reply_markup(
                    reply_markup=opp_duel_kb(duel_id, "target", 1))
                msg_id = await resent_lobby_info(
                    bot, res[0], "owner", txts[0], opp_duel_kb(duel_id, "owner", 1))
                await update_owner_msg_id(ssn, duel_id, msg_id)
                asyncio.create_task(check_duel_timer(
                    db, bot, duel_id, "owner", res[0].owner, res[0].owner_ts, 60))
        else:
            logging.info(f"Duel {duel_id} finished. Winner {res[0].winner}")
            await send_duel_finish_messages(res[0], bot)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
