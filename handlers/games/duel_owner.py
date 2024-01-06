import logging

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.queries.craft_queries import craft_card, get_user_duplicates
from db.queries.duel_queries import (add_owner_card_to_duel,
                                     get_user_duel_cards, owner_duel_candcel,
                                     update_owner_msg_id)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.cb_data import PageCB
from keyboards.duel_kbs import create_lobby_kb, duel_kb, duel_owner_cards_kb
from keyboards.main_kbs import to_main_btn
from middlewares.actions import ActionMiddleware
from utils.format_texts import (format_craft_text, format_new_free_card_text,
                                format_view_my_cards_text)
from utils.states import DuelStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(
    F.data.startswith("ownrcancelduel_"), flags=flags
)
async def owner_duel_cancel_cmd(c: CQ, ssn, bot: Bot, action_queue):
    duel_id = int(c.data.split("_")[-1])
    duel = await owner_duel_candcel(ssn, duel_id)
    if duel == "not_active":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    else:
        await c.message.edit_text(
            "🎪 Текущее лобби удалено", reply_markup=duel_kb)
        if duel.target != 0:
            try:
                await bot.delete_message(duel.target, duel.target_msg_id)
            except Exception as error:
                logging.info(f"Delete error | chat {duel.target}\n{error}")
            try:
                await bot.send_message(
                    duel.target, "🎪 Текущее лобби удалено", reply_markup=duel_kb)
            except Exception as error:
                logging.info(f"Send error | chat {duel.target}\n{error}")

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("addwnrduelcrds_"), flags={"throttling_key": "pages"}
)
async def add_duel_owner_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    duel_id = int(c.data.split("_")[-1])

    res = await get_user_duel_cards(
        ssn, c.from_user.id, "nosort", duel_id, "owner")
    if res == "not_active":
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
                reply_markup=duel_owner_cards_kb(page, last, "nosort", cards[0].id, duel_id))
            await update_owner_msg_id(ssn, duel_id, msg.message_id)
            await state.set_state(DuelStates.owner_cards)
            await state.update_data(cards=cards, sorting="nosort", duel_id=duel_id)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(DuelStates.owner_cards),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_owner_duel_cards_cmd(c: CQ, state: FSM, callback_data: PageCB, action_queue):
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
            media=media, reply_markup=duel_owner_cards_kb(
                page, last, sorting, card.id, duel_id))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("srtownrcrds_"), flags={"throttling_key": "pages"}
)
async def view_sorted_duel_owner_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
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
        ssn, c.from_user.id, sorting, duel_id, "owner")
    cards = res[0]

    page = 1
    last = len(cards)
    txt = await format_view_my_cards_text(cards[0].card)
    media = types.InputMediaPhoto(caption=txt, media=cards[0].card.image)
    try:
        await c.message.edit_media(
            media=media, reply_markup=duel_owner_cards_kb(
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
    StateFilter(DuelStates.owner_cards),
    F.data.startswith("ownrmorcards_"), flags={"throttling_key": "pages"}
)
async def add_duel_owner_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    u_card_id = int(c.data.split("_")[-1])

    data = await state.get_data()
    duel_id = data.get("duel_id")
    res = await add_owner_card_to_duel(ssn, c.from_user.id, duel_id, u_card_id)
    if res == "not_active":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    else:
        await c.message.delete()
        msg = await c.message.answer()
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
