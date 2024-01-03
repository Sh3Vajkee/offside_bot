import asyncio
import datetime as dt
import logging

from aiogram import Bot

from db.queries.penalty_queries import check_penalty
from keyboards.games_kbs import after_penalty_kb
from keyboards.main_kbs import back_to_main_btn, to_main_btn


async def check_penalty_timer(db, penalty_id, date_ts, delay, bot: Bot):
    await asyncio.sleep(delay)
    penalty = await check_penalty(db, penalty_id, date_ts)
    if penalty:
        if penalty.kicker == penalty.keeper == 0:
            try:
                await bot.delete_message(penalty.target, penalty.target_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {penalty.target}\n{error}")

            await asyncio.sleep(.2)

            txt = "К сожалению, ваш оппонент не принял игру за минуту"
            try:
                await bot.send_message(
                    penalty.owner, txt, reply_markup=to_main_btn)
            except Exception as error:
                logging.error(f"Send error | chat {penalty.owner}\n{error}")

        else:
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
