import asyncio
import logging
from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem, Player
from db.queries.games_queries import lucky_shot
from db.queries.penalty_queries import (check_for_active_penalty,
                                        create_new_penalty)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.games_kbs import games_kb, lucky_shot_btn, no_free_ls_btn
from keyboards.main_kbs import back_to_main_btn, to_main_btn
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_new_free_card_text
from utils.misc import format_delay_text
from utils.scheduled import check_penalty_timer
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "penalty", flags=flags)
async def lucky_shot_cmd(c: CQ, action_queue, state: FSM, ssn):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    res = await check_for_active_penalty(ssn, c.from_user.id)
    if res == "already_playing":
        txt = "Вы уже состоите в игре, закончите ее, чтобы начать следующую"
        await c.message.edit_text(txt, reply_markup=back_to_main_btn)
    else:
        txt = "✉️ Напишите @username пользователя, которому хотите предложить игру в Пенальти"
        await c.message.edit_text(txt, reply_markup=back_to_main_btn)
        await state.set_state(UserStates.target_penalty)


@router.message(StateFilter(UserStates.target_penalty), F.text, flags=flags)
async def save_target_penalty_username_cmd(m: Mes, state: FSM, ssn, bot: Bot, db):
    await state.clear()

    target = m.text

    if m.from_user.username:
        username = f"@{m.from_user.username}"
    else:
        username = m.from_user.mention_html()

    res = await create_new_penalty(ssn, m.from_user.id, username, target, bot)
    if res == "already_playing":
        txt = "Вы уже состоите в игре, закончите ее, чтобы начать следующую"
        await m.answer(txt, reply_markup=back_to_main_btn)
    elif res == "rating_diff":
        txt = f"Ты не можешь сыграть в пенальти с {target} из-за большой разницы в рейтинге☹️"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res == "rating_diff":
        txt = f"Этому пользователю нельзя предложить игру в Пенальти ☹️\nОн уже находится в игре, дождитесь конца или предложите игру кому-нибудь другому"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res in ("not_found", "error"):
        txt = "Этому пользователю нельзя отправить предложение сыграть, попробуйте снова"
        await m.answer(txt, reply_markup=to_main_btn)
    else:
        txt = f"📩Ваше предложение сыграть в Пенальти было отправлено {username}!"
        await m.answer(txt)
        asyncio.create_task(check_penalty_timer(db, res[0], res[1]))
