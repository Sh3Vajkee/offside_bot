import asyncio
import datetime
import logging
from textwrap import dedent

from aiogram import Bot

from db.models import Duel
from db.queries.duel_queries import (check_duel, get_active_duels,
                                     update_owner_msg_id_db)
from keyboards.duel_kbs import duel_kb, no_opp_duel_kb
from keyboards.main_kbs import to_main_btn
from utils.const import images


async def create_lobbies_btns(duels):
    btns = []
    duel: Duel
    for duel in duels:
        txt = f"🟣 {duel.owner_username}- {duel.owner_points} очков на дуэли ⚔️"
        btns.append([duel.id, txt])

    return btns


async def format_duel_lobby_text(duel: Duel):
    if duel.target == 0:
        txt = f"""
        🎪 Ваше лобби:

        Очки на текущую дуэль:
        🟣 {duel.owner_username} - {duel.owner_points}

        Статус лобби - Ожидание соперника
        """
        return dedent(txt), ""
    else:
        txt_header = f"""
        🎪 Ваше лобби:

        Очки на текущую дуэль:
        🟣 {duel.owner_username} - {duel.owner_points}
        🟠 {duel.target_username} - {duel.target_points}
        """
        total_rating = duel.owner_points + duel.target_points
        owner_chance = duel.owner_points / total_rating
        target_chance = duel.target_points / total_rating

        owner_footer = f"\nВероятность на победу - {float('{:.2f}'.format(owner_chance * 100))}%"
        target_footer = f"\nВероятность на победу - {float('{:.2f}'.format(target_chance * 100))}% "

        return dedent(txt_header) + owner_footer, dedent(txt_header) + target_footer


async def resent_lobby_info(bot: Bot, duel: Duel, kind, text, markup):
    if kind == "owner":
        user_id = duel.owner
        del_msg_id = duel.owner_msg_id
    else:
        user_id = duel.target
        del_msg_id = duel.target_msg_id

    msg_id = del_msg_id
    try:
        msg = await bot.send_message(user_id, text, reply_markup=markup)
        msg_id = msg.message_id
    except Exception as error:
        logging.error(f"Send error | chat {user_id}\n{error}")

    try:
        await bot.delete_message(user_id, del_msg_id)
    except Exception as error:
        logging.error(f"Delete error | chat {user_id}\n{error}")

    return msg_id


async def format_duel_cards(duel: Duel, owner_cards, target_cards):
    txt = f"🟣 {duel.owner_username}:"
    for card in owner_cards:
        txt += f"\n{card.card.nickname} | Рейтинг: {card.card.points}"

    if duel.target != 0:
        txt += f"\n\n🟠 {duel.target_username}:"
        if len(target_cards) > 0:
            for tcard in target_cards:
                txt += f"\n{tcard.card.nickname} | Рейтинг: {tcard.card.points}"

    return txt


async def send_duel_finish_messages(duel: Duel, bot: Bot):
    try:
        await bot.delete_message(duel.owner, duel.owner_msg_id)
    except Exception as error:
        logging.error(f"Delete error | chat {duel.owner}\n{error}")
    try:
        await bot.delete_message(duel.target, duel.target_msg_id)
    except Exception as error:
        logging.error(f"Delete error | chat {duel.target}\n{error}")

    await asyncio.sleep(.01)

    if duel.winner == duel.owner:
        owner_sticker = images.get("duelwin")
        target_sticker = images.get("duellose")
    else:
        owner_sticker = images.get("duellose")
        target_sticker = images.get("duelwin")

    try:
        await bot.send_sticker(duel.owner, owner_sticker)
    except Exception as error:
        logging.error(f"Send error | chat {duel.owner}\n{error}")
    try:
        await bot.send_sticker(duel.target, target_sticker)
    except Exception as error:
        logging.error(f"Send error | chat {duel.target}\n{error}")

    await asyncio.sleep(.01)

    txt = f"""
    ⚔️ Дуэль окончена!

    🏆 Победитель: {duel.owner_username if duel.winner == duel.owner else duel.target_username}

    🃏 Коллекции карт обновлены.
    """

    try:
        await bot.send_message(duel.owner, dedent(txt), reply_markup=to_main_btn)
    except Exception as error:
        logging.error(f"Send error | chat {duel.owner}\n{error}")
    try:
        await bot.send_message(duel.target, dedent(txt), reply_markup=to_main_btn)
    except Exception as error:
        logging.error(f"Send error | chat {duel.target}\n{error}")


async def re_check_active_duels(db, bot):
    date = datetime.datetime.now()
    date_ts = int(date.timestamp())
    duels = await get_active_duels(db)
    if len(duels) > 0:
        duel: Duel
        for num, duel in enumerate(duels):
            if duel.owner_ts > 0:
                delay = duel.owner_ts - date_ts
                if delay <= 0:
                    delay = num + 1
                asyncio.create_task(check_duel_timer(
                    db, bot, duel.id, "owner", duel.owner, duel.owner_ts, delay))
            elif duel.target_ts > 0:
                delay = duel.target_ts - date_ts
                if delay <= 0:
                    delay = num + 1
                asyncio.create_task(check_duel_timer(
                    db, bot, duel.id, "target", duel.target, duel.target_ts, delay))

            await asyncio.sleep(.001)


async def check_duel_timer(db, bot: Bot, duel_id, kind, user_id, date_ts, delay):
    await asyncio.sleep(delay)
    res = await check_duel(db, duel_id, kind, user_id, date_ts)
    duel = res[0]
    if res[1] == "owner_timeout":
        try:
            await bot.delete_message(duel.owner, duel.owner_msg_id)
        except Exception as error:
            logging.error(f"Delete error | chat {duel.owner}\n{error}")
        try:
            await bot.delete_message(duel.target, duel.target_msg_id)
        except Exception as error:
            logging.error(f"Delete error | chat {duel.target}\n{error}")

        await asyncio.sleep(.01)

        txt = f"""
        🎪 Текущее лобби удалено

        🟣 {duel.owner_username} долго бездействовал, лобби было удалено
        """

        try:
            await bot.send_message(duel.owner, dedent(txt), reply_markup=duel_kb)
        except Exception as error:
            logging.error(f"Send error | chat {duel.owner}\n{error}")
        try:
            await bot.send_message(duel.target, dedent(txt), reply_markup=duel_kb)
        except Exception as error:
            logging.error(f"Send error | chat {duel.target}\n{error}")
    elif res[1] == "target_timeout":
        try:
            await bot.delete_message(duel.owner, duel.owner_msg_id)
        except Exception as error:
            logging.error(f"Delete error | chat {duel.owner}\n{error}")
        try:
            await bot.delete_message(res[2], res[3])
        except Exception as error:
            logging.error(f"Delete error | chat {duel.target}\n{error}")

        await asyncio.sleep(.01)

        txt = f"🟠 {res[4]} долго бездействовал и был удален из лобби"
        try:
            await bot.send_message(duel.owner, txt)
        except Exception as error:
            logging.error(f"Send error | chat {duel.owner}\n{error}")

        await asyncio.sleep(.01)

        duel_txt = await format_duel_lobby_text(duel)
        try:
            msg = await bot.send_message(
                duel.owner, duel_txt[0], reply_markup=no_opp_duel_kb(duel_id))
            await update_owner_msg_id_db(db, duel_id, msg.message_id)
        except Exception as error:
            logging.error(f"Send error | chat {duel.owner}\n{error}")
