import logging
from textwrap import dedent

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.models import Duel
from db.queries.craft_queries import craft_card, get_user_duplicates
from db.queries.duel_queries import (add_duel_first_card, create_duel_lobby,
                                     get_duel_cards_for_create,
                                     get_user_duel_cards)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.cb_data import PageCB
from keyboards.duel_kbs import (create_lobby_kb, duel_first_cards_kb, duel_kb,
                                duel_owner_cards_kb, new_lobby_kb,
                                no_opp_duel_kb)
from keyboards.main_kbs import to_main_btn
from middlewares.actions import ActionMiddleware
from utils.format_texts import (format_craft_text, format_new_free_card_text,
                                format_view_my_cards_text)
from utils.states import DuelStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "duelcreate", flags=flags)
async def create_duel_cmd(c: CQ, state: FSM, action_queue):
    txt = "🃏 Выберите карты, которые хотите добавить в дуэль."
    await c.message.edit_text(txt, reply_markup=create_lobby_kb)
    await state.set_state(DuelStates.create_lobby)
    await state.update_data(selected=[], rating=0, duel_id=0)
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.create_lobby),
    F.data == "duelcardscreate", flags={"throttling_key": "pages"}
)
async def add_first_cards_cmd(c: CQ, ssn, action_queue, state: FSM):
    data = await state.get_data()
    selected = data.get("selected")

    cards = await get_duel_cards_for_create(ssn, c.from_user.id, "nosort", selected)
    if len(cards) == 0:
        await c.answer("У тебя больше нет карт для дуэли")
    else:
        page = 1
        last = len(cards)

        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=duel_first_cards_kb(
                page, last, "nosort", cards[0].id, len(selected)))

        await state.set_state(DuelStates.create_lobby)
        await state.update_data(cards=cards, sorting="nosort")

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.create_lobby),
    F.data.startswith("srtfrstcrds_"), flags={"throttling_key": "pages"}
)
async def view_sorted_duel_first_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    data = await state.get_data()
    selected = data.get("selected")

    cards = await get_duel_cards_for_create(ssn, c.from_user.id, sorting, selected)

    page = 1
    last = len(cards)

    await c.message.delete()

    txt = await format_view_my_cards_text(cards[0].card)
    await c.message.answer_photo(
        cards[0].card.image, txt,
        reply_markup=duel_first_cards_kb(page, last, sorting, cards[0].id, len(selected)))

    await state.set_state(DuelStates.create_lobby)
    await state.update_data(cards=cards, sorting=sorting)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.create_lobby),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_first_duel_cards_cmd(c: CQ, state: FSM, callback_data: PageCB, action_queue):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")
    selected = data.get("selected")

    card = cards[page-1]
    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media, reply_markup=duel_first_cards_kb(
                page, last, sorting, card.id, len(selected)))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.create_lobby),
    F.data == "back_to_owner_lobby", flags={"throttling_key": "pages"}
)
async def back_to_create_lobby_cmd(c: CQ, state: FSM, action_queue):
    data = await state.get_data()
    rating = data.get("rating")
    txt = f"⚔️ Очки на текущую дуэль - {rating}"
    await c.message.delete()
    await c.message.answer(txt, reply_markup=new_lobby_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.create_lobby),
    F.data.startswith("ownrcrtduel_"), flags={"throttling_key": "pages"}
)
async def add_duel_first_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    u_card_id = int(c.data.split("_")[-1])

    data = await state.get_data()
    selected = data.get("selected")
    if len(selected) >= 5:
        await c.answer("Вы не можете добавить больше 5 карт")
    else:
        card = await add_duel_first_card(ssn, c.from_user.id, u_card_id)

        rating = data.get("rating")

        selected.append(u_card_id)
        rating += card.points

        txt = f"""
        ⚔️ Вы добавили в дуэль {card.card.nickname} с рейтингом {card.points}
        Очки на текущую дуэль - {rating}
        """
        await c.message.delete()
        await c.message.answer(dedent(txt), reply_markup=new_lobby_kb)
        await state.update_data(selected=selected, rating=rating)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.create_lobby),
    F.data == "duellobbystart", flags=flags
)
async def create_lobby_cmd(c: CQ, ssn, action_queue, state: FSM):
    data = await state.get_data()
    selected = data.get("selected")
    rating = data.get("rating")
    await state.clear()

    if c.from_user.username:
        username = f"@{c.from_user.username}"
    else:
        username = c.from_user.mention_html()

    duel: Duel = await create_duel_lobby(
        ssn, c.from_user.id, username, selected,
        rating, c.message.message_id)
    if duel == "already_playing":
        txt = "Вы уже состоите в дуэли, закончите ее, чтобы начать следующую"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    elif duel == "error":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    else:
        txt = f"""
        🎪 Ваше лобби создано:

        Очки на текущую дуэль:
        🟣 {duel.owner_username} - {duel.owner_points}

        Статус лобби - Ожидание соперника
        """
        await c.message.edit_text(
            dedent(txt), reply_markup=no_opp_duel_kb(duel.id))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
