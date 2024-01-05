import asyncio
import logging
from textwrap import dedent

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem, Penalty, Player
from db.queries.collection_queries import get_user_rarity_cards
from db.queries.games_queries import lucky_shot
from db.queries.penalty_queries import (answer_card_penalty, cancel_pen_queue,
                                        cancel_penalty,
                                        check_for_active_penalty,
                                        check_for_active_penalty_card,
                                        create_new_card_penalty,
                                        create_new_penalty, find_penalty_opp,
                                        keeper_action, kicker_action,
                                        penalty_switch, start_penalty)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.cb_data import PageCB
from keyboards.games_kbs import (after_penalty_kb, answ_card_pen_kb,
                                 answ_card_penalty_kb,
                                 answ_pen_rarity_cards_kb,
                                 cancel_penalty_queue_btn, card_pen_kb,
                                 card_penalty_kb, draw_penalty_kb, games_kb,
                                 lucky_shot_btn, no_free_ls_btn,
                                 pen_rarities_kb, penalty_kind_kb,
                                 penalty_opp_kb, to_games_btn)
from keyboards.main_kbs import to_main_btn
from middlewares.actions import ActionMiddleware
from utils.format_texts import (format_new_free_card_text,
                                format_penalty_final_result_text,
                                format_penalty_round_result_text,
                                format_view_my_cards_text)
from utils.misc import format_delay_text
from utils.scheduled import check_penalty_timer
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(
    F.data.startswith("penawscard_"), flags={"throttling_key": "pages"}
)
async def answ_pen_card_game_cmd(c: CQ, action_queue):
    pen_id = int(c.data.split("_")[-1])
    await c.message.delete()
    await c.message.answer(
        "🧳 Выберите формат отображения коллекции",
        reply_markup=answ_card_pen_kb(pen_id))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("answpenrarities_"), flags={"throttling_key": "pages"}
)
async def answ_pen_card_rar_cmd(c: CQ, action_queue):
    pen_id = int(c.data.split("_")[-1])
    txt = "Выберите редкость карт"
    await c.message.edit_text(txt, reply_markup=answ_pen_rarity_cards_kb(pen_id))
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("answpenrar_"), flags={"throttling_key": "pages"}
)
async def view_trade_trade_rarity_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    c_data = c.data.split("_")
    rarity = c_data[1]
    pen_id = int(c_data[2])

    cards = await get_user_rarity_cards(ssn, c.from_user.id, rarity, "nosort")

    if len(cards) == 0:
        if rarity == "all":
            await c.answer("ℹ️ У тебя еще нет карт")
        else:
            await c.answer("ℹ️ У тебя нет карт этой редкости")
    else:
        page = 1
        last = len(cards)

        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=answ_card_penalty_kb(
                page, last, "nosort", cards[0].card_id, pen_id))

        await state.set_state(UserStates.answ_pen_card)
        await state.update_data(
            cards=cards, sorting="nosort", pen_id=pen_id)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("answsrtpen_"), flags={"throttling_key": "pages"}
)
async def view_answ_pen_sorted_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    cards = await get_user_rarity_cards(ssn, c.from_user.id, "all", sorting)
    if len(cards) == 0:
        await c.answer("ℹ️ У тебя еще нет карт")
        await c.message.delete()
    else:
        page = 1
        last = len(cards)

        data = await state.get_data()
        pen_id = data.get("pen_id")
        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=answ_card_penalty_kb(
                page, last, sorting, cards[0].card_id, pen_id))

        await state.set_state(UserStates.answ_pen_card)
        await state.update_data(cards=cards, sorting=sorting)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(UserStates.answ_pen_card),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_target_pen_cards_cmd(c: CQ, state: FSM, callback_data: PageCB, action_queue):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")
    pen_id = data.get("pen_id")

    card = cards[page-1]
    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media, reply_markup=answ_card_penalty_kb(
                page, last, sorting, card.card_id, pen_id))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("answpencard_"), flags=flags)
async def choose_target_penalty_card_cmd(c: CQ, ssn, state: FSM, bot, action_queue, db):
    card_id = int(c.data.split("_")[-1])
    data = await state.get_data()
    await state.clear()
    pen_id = data.get("pen_id")
    res = await answer_card_penalty(ssn, c.from_user.id, pen_id, card_id, bot)
    if res == "not_active":
        await c.message.delete()
        await c.message.answer(
            "❌ Эта игра больше недоступна", reply_markup=to_games_btn)
    elif res in ("no_card", "error"):
        await c.message.delete()
        await c.message.answer(
            "⚠️ Возникла ошибка! Поробуйте позже", reply_markup=to_games_btn)
    else:
        txt = f"📩 Ваш ответ отправлен {res[1]}!"
        await c.message.delete_reply_markup()
        await c.message.answer(txt)
        asyncio.create_task(check_penalty_timer(db, pen_id, res[0], 60, bot))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
