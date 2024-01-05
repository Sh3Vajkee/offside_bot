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
from db.queries.penalty_queries import (cancel_pen_queue, cancel_penalty,
                                        check_for_active_penalty,
                                        check_for_active_penalty_card,
                                        create_new_card_penalty,
                                        create_new_penalty, find_penalty_opp,
                                        keeper_action, kicker_action,
                                        penalty_switch, start_penalty)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.cb_data import PageCB
from keyboards.games_kbs import (after_penalty_kb, cancel_penalty_queue_btn,
                                 card_pen_kb, card_penalty_kb, draw_penalty_kb,
                                 games_kb, lucky_shot_btn, no_free_ls_btn,
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


@router.callback_query(F.data == "pengame_card", flags=flags)
async def card_pen_game_cmd(c: CQ, action_queue):
    await c.message.answer(
        "🧳 Выберите формат отображения коллекции",
        reply_markup=card_pen_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = "⚽️ Выберите соперника"
    await c.message.edit_text(txt, reply_markup=penalty_opp_kb)


@router.callback_query(F.data == "penrarities", flags=flags)
async def card_pen_rarities_cmd(c: CQ, action_queue):
    txt = "Выберите редкость карт"
    await c.message.edit_text(txt, reply_markup=pen_rarities_kb)
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("srtpen_"), flags={"throttling_key": "pages"}
)
async def view_pen_sorted_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
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

        await state.clear()
        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=card_penalty_kb(page, last, sorting, cards[0].card_id))

        await state.set_state(UserStates.pen_owner_card)
        await state.update_data(cards=cards, sorting=sorting)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    F.data.startswith("penrar_"), flags={"throttling_key": "pages"}
)
async def view_owner_pen_rarity_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    c_data = c.data.split("_")
    rarity = c_data[1]

    cards = await get_user_rarity_cards(ssn, c.from_user.id, rarity, "nosort")
    if len(cards) == 0:
        if rarity == "all":
            await c.answer("ℹ️ У тебя еще нет карт")
        else:
            await c.answer("ℹ️ У тебя нет карт этой редкости")
    else:
        page = 1
        last = len(cards)

        await state.clear()
        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=card_penalty_kb(
                page, last, "nosort", cards[0].card_id))

        await state.set_state(UserStates.pen_owner_card)
        await state.update_data(cards=cards, sorting="nosort")

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(UserStates.pen_owner_card),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_owner_pen_cards_cmd(c: CQ, state: FSM, callback_data: PageCB, action_queue):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")

    card = cards[page-1]
    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media, reply_markup=card_penalty_kb(
                page, last, sorting, card.card_id))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("chspencard_"), flags=flags)
async def choose_penalty_card_cmd(c: CQ, ssn, state: FSM, action_queue):
    card_id = int(c.data.split("_")[-1])
    res = await check_for_active_penalty_card(ssn, c.from_user.id)
    if res == "already_playing":
        await state.clear()
        await c.message.delete()
        txt = "Вы уже состоите в игре, закончите ее, чтобы начать следующую"
        await c.message.answer(txt, reply_markup=to_games_btn)
    elif res == "active_trade":
        await c.message.delete()
        await state.clear()
        txt = "У тебя уже есть активные обмены"
        await c.message.answer(txt, reply_markup=to_main_btn)
    else:
        txt = "Напишите юзернейм пользователя (@username), с которым хотите сыграть"
        await c.message.delete_reply_markup()
        await c.message.answer(txt, reply_markup=to_games_btn)
        await state.clear()
        await state.set_state(UserStates.pen_target_card)
        await state.update_data(card_id=card_id)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.message(StateFilter(UserStates.pen_target_card), F.text, flags=flags)
async def save_target_card_pen_username_cmd(m: Mes, state: FSM, ssn, bot: Bot, db):
    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    target = m.text

    if m.from_user.username:
        username = f"@{m.from_user.username}"
    else:
        username = m.from_user.mention_html()

    res = await create_new_card_penalty(ssn, m.from_user.id, username, target, card_id, bot)
    if res == "already_playing":
        txt = "Вы уже состоите в игре, закончите ее, чтобы начать следующую"
        await m.answer(txt, reply_markup=to_games_btn)
    elif res == "no_card":
        await m.answer(
            "⚠️ Возникла ошибка! Поробуйте позже", reply_markup=to_games_btn)
    elif res == "rating_diff":
        txt = f"Ты не можешь сыграть в пенальти с {target} из-за большой разницы в рейтинге☹️"
        await m.answer(txt, reply_markup=to_games_btn)
    elif res == "rating_diff":
        txt = f"Этому пользователю нельзя предложить игру в Пенальти ☹️\nОн уже находится в игре, дождитесь конца или предложите игру кому-нибудь другому"
        await m.answer(txt, reply_markup=to_games_btn)
    elif res == "self_error":
        txt = f"Нельзя играть с самим собой ☹️"
        await m.answer(txt, reply_markup=to_games_btn)
    elif res in ("not_found", "error"):
        txt = "Этому пользователю нельзя отправить предложение сыграть, попробуйте снова"
        await m.answer(txt, reply_markup=to_games_btn)
    else:
        txt = f"📩Ваше предложение сыграть в Пенальти было отправлено {target}!"
        await m.answer(txt)
        asyncio.create_task(check_penalty_timer(db, res[0], res[1], 60, bot))
