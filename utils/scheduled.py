import asyncio
import datetime as dt
import logging

from aiogram import Bot

from db.models import Penalty
from db.queries.penalty_queries import check_penalty, get_active_penalties
from db.queries.scheduled_queries import day_reset
from keyboards.games_kbs import after_penalty_kb
from keyboards.main_kbs import back_to_main_btn, to_main_btn


async def new_day(db):
    await day_reset(db)
    logging.info("DAY RESETED")


async def re_check_active_penalties(db, bot):
    date = dt.datetime.now()
    date_ts = int(date.timestamp())
    penalties = await get_active_penalties(db)
    if len(penalties) > 0:
        penalty: Penalty
        for num, penalty in enumerate(penalties):
            delay = penalty.last_action - date_ts
            if delay <= 0:
                delay = num + 1
            asyncio.create_task(check_penalty_timer(
                db, penalty.id, penalty.last_action, delay, bot))
            await asyncio.sleep(.001)


async def check_penalty_timer(db, penalty_id, date_ts, delay, bot: Bot):
    await asyncio.sleep(delay)
    penalty = await check_penalty(db, penalty_id, date_ts)

    if penalty:
        if penalty.kicker == penalty.keeper == 0:
            if penalty.target_card_id == 0:
                del_id = penalty.owner
                del_msg_id = penalty.owner_msg_id
                u_id = penalty.target
            else:
                del_id = penalty.target
                del_msg_id = penalty.target_msg_id
                u_id = penalty.owner

            try:
                await bot.delete_message(del_id, del_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {del_id}\n{error}")

            await asyncio.sleep(.2)

            txt = "К сожалению, ваш оппонент не принял игру за минуту"
            try:
                await bot.send_message(
                    u_id, txt, reply_markup=to_main_btn)
            except Exception as error:
                logging.error(f"Send error | chat {u_id}\n{error}")

        else:
            try:
                await bot.delete_message(penalty.owner, penalty.owner_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {penalty.owner}\n{error}")
            await asyncio.sleep(.03)
            try:
                await bot.delete_message(penalty.target, penalty.target_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {penalty.target}\n{error}")

            if penalty.turn_user_id == penalty.owner:
                owner_txt = "Тебя слишком долго не было в игре, поэтому тебе засчитано поражение"
                target_txt = f"Игрок {penalty.owner_username} слишком долго не отвечал, вы победили!"
            else:
                owner_txt = f"Игрок {penalty.target_username} слишком долго не отвечал, вы победили!"
                target_txt = f"Тебя слишком долго не было в игре, поэтому тебе засчитано поражение"

            try:
                await bot.send_message(
                    penalty.owner, owner_txt, reply_markup=after_penalty_kb)
            except Exception as error:
                logging.error(f"Send error | chat {penalty.owner}\n{error}")

            await asyncio.sleep(.2)

            try:
                await bot.send_message(
                    penalty.target, target_txt, reply_markup=after_penalty_kb)
            except Exception as error:
                logging.error(f"Send error | chat {penalty.target}\n{error}")
