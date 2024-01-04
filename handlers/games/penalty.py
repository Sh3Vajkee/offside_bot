import asyncio
import logging
from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem, Penalty, Player
from db.queries.games_queries import lucky_shot
from db.queries.penalty_queries import (cancel_penalty,
                                        check_for_active_penalty,
                                        create_new_penalty, keeper_action,
                                        kicker_action, penalty_switch,
                                        start_penalty)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.games_kbs import (after_penalty_kb, draw_penalty_kb, games_kb,
                                 lucky_shot_btn, no_free_ls_btn)
from keyboards.main_kbs import back_to_main_btn, to_main_btn
from middlewares.actions import ActionMiddleware
from utils.format_texts import (format_new_free_card_text,
                                format_penalty_final_result_text,
                                format_penalty_round_result_text)
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
async def save_target_penalty_username_cmd(m: Mes, state: FSM, ssn, bot: Bot, db, action_queue):
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
    elif res == "self_error":
        txt = f"Нельзя играть с самим собой ☹️"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res in ("not_found", "error"):
        txt = "Этому пользователю нельзя отправить предложение сыграть, попробуйте снова"
        await m.answer(txt, reply_markup=to_main_btn)
    else:
        txt = f"📩Ваше предложение сыграть в Пенальти было отправлено {target}!"
        await m.answer(txt)
        asyncio.create_task(check_penalty_timer(db, res[0], res[1], 60, bot))


@router.callback_query(F.data.startswith("pencancel_"), flags=flags)
async def decline_penalty_cmd(c: CQ, ssn, bot: Bot, action_queue):
    pen_id = int(c.data.split("_")[-1])

    penalty = await cancel_penalty(ssn, pen_id)
    await c.message.edit_text(
        "❌ Вы отклонили игру в пенальти", reply_markup=to_main_btn)

    if penalty != "not_active":
        await bot.send_message(
            penalty.owner, f"❌ {penalty.target_username} отклонил предложение игры",
            reply_markup=to_main_btn)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("penstart_"), flags=flags)
async def start_penalty_cmd(c: CQ, ssn, bot: Bot, action_queue, db):
    pen_id = int(c.data.split("_")[-1])
    res = await start_penalty(ssn, pen_id, bot)
    if res in ("not_active", "error"):
        await c.message.edit_text(
            "❌ Эта игра больше недоступна", reply_markup=to_main_btn)
    asyncio.create_task(check_penalty_timer(db, pen_id, res, 60, bot))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("pnactn_kicker"), flags=flags)
async def kicker_penalty_cmd(c: CQ, ssn, action_queue, db, bot):
    data = c.data.split("_")
    pen_id = int(data[2])
    corner = int(data[3])

    res = await kicker_action(ssn, pen_id, c.from_user.id, corner)
    if res == "not_active":
        await c.message.delete()
        await c.message.answer(
            "❌ Эта игра больше недоступна", reply_markup=to_main_btn)
    else:
        txt = f"Ваш выбор - {corner}\nОжидайте хода второго игрока"
        await c.message.edit_caption(caption=txt)
        asyncio.create_task(check_penalty_timer(db, pen_id, res, 60, bot))
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("pnactn_keeper"), flags=flags)
async def keeper_penalty_cmd(c: CQ, ssn, bot: Bot, action_queue, db):
    data = c.data.split("_")
    pen_id = int(data[2])
    corner = int(data[3])

    res = await keeper_action(ssn, pen_id, c.from_user.id, corner)
    if res == "not_active":
        await c.message.delete()
        await c.message.answer(
            "❌ Эта игра больше недоступна", reply_markup=to_main_btn)
    elif res == "not_ready":
        await c.answer("Твой соперник еще не сделал удар.", show_alert=True)
    else:
        penalty: Penalty = res[0]
        txt = f"Ваш выбор - {corner}"
        await c.message.edit_caption(caption=txt)

        if penalty.status == "finished":
            if penalty.winner == 0:
                keyboard = draw_penalty_kb
            else:
                keyboard = after_penalty_kb

            txt = await format_penalty_final_result_text(res[0])
            await c.message.answer(txt, reply_markup=keyboard)

            await bot.send_message(penalty.kicker, txt, reply_markup=keyboard)

        else:
            new_ts = penalty.last_action
            asyncio.create_task(check_penalty_timer(
                db, pen_id, new_ts, 60, bot))
            texts = await format_penalty_round_result_text(*res)

            await c.message.answer(texts[0])
            await asyncio.sleep(.01)

            await bot.send_message(penalty.keeper, texts[1])

            await asyncio.sleep(.01)
            await penalty_switch(ssn, pen_id, bot)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
