import asyncio
import datetime as dt
import logging
import random

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Penalty, Player, Trade, UserCard
from utils.misc import send_penalty_action, send_penalty_offer


async def check_for_active_penalty(ssn: AsyncSession, user_id):
    penalty_q = await ssn.execute(select(Penalty).filter(
        or_(Penalty.target == user_id, Penalty.owner == user_id)).filter(
            Penalty.status == "active"))
    penalty_res = penalty_q.fetchone()
    if penalty_res is None:
        return "available"

    return "already_playing"


async def create_new_penalty(ssn: AsyncSession, user_id, username, target_username, bot):
    penalty_q = await ssn.execute(select(Penalty).filter(
        or_(Penalty.target == user_id, Penalty.owner == user_id)).filter(
            Penalty.status == "active"))
    penalty_res = penalty_q.fetchone()
    if penalty_res is not None:
        return "already_playing"

    target_q = await ssn.execute(
        select(Player).filter(Player.username.ilike(target_username)))
    target_res = target_q.fetchone()
    if target_res is None:
        return "not_found"

    if user_id == target_res[0].id:
        return "self_error"

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]
    target: Player = target_res[0]

    rating_delta = abs(user.penalty_rating - target.penalty_rating)
    if rating_delta > 300:
        return "rating_diff"

    target_penalty_q = await ssn.execute(select(Penalty).filter(
        or_(Penalty.target == target.id, Penalty.owner == target.id)).filter(
            Penalty.status == "active"))
    target_penalty_res = target_penalty_q.fetchone()
    if target_penalty_res is not None:
        return "target_already_playing"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    penalty = await ssn.merge(Penalty(
        owner=user_id, owner_username=username,
        target=target.id, target_username=target.username))
    await ssn.commit()
    penalty_id = penalty.id
    msg_id = await send_penalty_offer(bot, target.id, username, penalty_id)
    if msg_id == 0:
        await ssn.execute(update(Penalty).filter(
            Penalty.id == penalty_id).values(status="error"))
        await ssn.commit()
        return "error"
    else:
        await ssn.execute(update(Penalty).filter(
            Penalty.id == penalty_id).values(
                target_msg_id=msg_id, last_action=date_ts+60))
        await ssn.commit()
        logging.info(
            f"User {user_id} created new penaly #{penalty_id} to {target.id} ({target.username})")
        return penalty_id, date_ts + 60


async def check_penalty(db, penalty_id, date_ts):
    ssn: AsyncSession
    async with db() as ssn:
        penalty_q = await ssn.execute(
            select(Penalty).filter(Penalty.id == penalty_id))
        penalty: Penalty = penalty_q.fetchone()[0]
        if penalty.last_action == date_ts:
            if penalty.kicker == penalty.keeper == 0:
                await ssn.execute(update(Penalty).filter(
                    Penalty.id == penalty_id).values(
                        status="auto_canceled", last_action=0))
                logging.info(f"Penalty {penalty_id} auto canceled")
            else:
                if penalty.turn_user_id == penalty.owner:
                    await ssn.execute(update(Player).filter(
                        Player.id == penalty.target).values(
                            penalty_rating=Player.penalty_rating + 25))
                    await ssn.execute(update(Player).filter(
                        Player.id == penalty.owner).values(
                            penalty_rating=Player.penalty_rating - 25))
                    await ssn.execute(update(Penalty).filter(
                        Penalty.id == penalty_id).values(
                            status="target_auto_win", last_action=0,
                            winner=penalty.target))
                    logging.info(f"Penalty {penalty_id} target auto win")

                else:
                    await ssn.execute(update(Player).filter(
                        Player.id == penalty.owner).values(
                            penalty_rating=Player.penalty_rating + 25))
                    await ssn.execute(update(Player).filter(
                        Player.id == penalty.target).values(
                            penalty_rating=Player.penalty_rating - 25))
                    await ssn.execute(update(Penalty).filter(
                        Penalty.id == penalty_id).values(
                            status="owner_auto_win", last_action=0,
                            winner=penalty.owner))
                    logging.info(f"Penalty {penalty_id} owner auto win")

            await ssn.commit()
            return penalty
        return False


async def cancel_penalty(ssn: AsyncSession, pen_id):
    penalty_q = await ssn.execute(
        select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status == "active":
        await ssn.execute(update(Penalty).filter(
            Penalty.id == pen_id).values(status="canceled", last_action=0))
        await ssn.commit()
        logging.info(f"User {penalty.target} canceled penalty {pen_id}")
        return penalty

    return "not_active"


async def start_penalty(ssn: AsyncSession, pen_id, bot):
    penalty_q = await ssn.execute(
        select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status != "active":
        return "not_active"

    msg_owner_id = await send_penalty_action(
        bot, penalty.owner, pen_id, "kicker")
    await asyncio.sleep(.01)
    msg_target_id = await send_penalty_action(
        bot, penalty.target, pen_id, "keeper")

    if (msg_owner_id == 0) or (msg_target_id == 0):
        await ssn.execute(update(Penalty).filter(
            Penalty.id == pen_id).values(status="canceled", last_action=0))
        await ssn.commit()
        logging.info(f"Penalty {pen_id} canceled with error")
        return "error"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    await ssn.execute(update(Penalty).filter(
        Penalty.id == pen_id).values(
            owner_msg_id=msg_owner_id, target_msg_id=msg_target_id,
            turn_user_id=penalty.owner, kicker=penalty.owner,
            keeper=penalty.target, last_action=date_ts + 60))
    await ssn.commit()
    logging.info(f"Penalty {pen_id} started")
    return date_ts + 60


async def kicker_action(ssn: AsyncSession, pen_id, user_id, kicker_pick):
    penalty_q = await ssn.execute(
        select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status != "active":
        return "not_active"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    await ssn.execute(update(Penalty).filter(
        Penalty.id == pen_id).values(
            turn_user_id=penalty.keeper,
            kicker_pick=kicker_pick, last_action=date_ts + 60))
    await ssn.commit()
    logging.info(
        f"Penalty {pen_id} | Kicker {user_id} kick to pos {kicker_pick}")
    return date_ts + 60


async def keeper_action(ssn: AsyncSession, pen_id, user_id, keeper_pick):
    penalty_q = await ssn.execute(
        select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status != "active":
        return "not_active"

    if penalty.kicker_pick == 0:
        return "not_ready"

    result = (penalty.kicker_pick == keeper_pick)
    if penalty.round == 10:
        if penalty.kicker_pick == keeper_pick:
            if penalty.kicker == penalty.owner:
                owner_txt = penalty.owner_txt + "0"
                target_txt = penalty.target_txt
            else:
                owner_txt = penalty.owner_txt
                target_txt = penalty.target_txt + "0"
            owner_score = penalty.owner_score
            target_score = penalty.target_score
        else:
            if penalty.kicker == penalty.owner:
                owner_txt = penalty.owner_txt + "1"
                target_txt = penalty.target_txt
                owner_score = penalty.owner_score + 1
                target_score = penalty.target_score
            else:
                owner_txt = penalty.owner_txt
                target_txt = penalty.target_txt + "1"
                owner_score = penalty.owner_score
                target_score = penalty.target_score + 1
        if owner_score > target_score:
            owner_rating = 25
            target_rating = -25
            winner = penalty.owner
        elif owner_score < target_score:
            owner_rating = -25
            target_rating = 25
            winner = penalty.target
        else:
            owner_rating = 0
            target_rating = 0
            winner = 0

        if owner_rating != 0:
            await ssn.execute(update(Player).filter(
                Player.id == penalty.owner).values(
                    penalty_rating=Player.penalty_rating + owner_rating))
            await ssn.execute(update(Player).filter(
                Player.id == penalty.target).values(
                    penalty_rating=Player.penalty_rating + target_rating))

        await ssn.execute(update(Penalty).filter(
            Penalty.id == pen_id).values(
                owner_txt=owner_txt, target_txt=target_txt,
                owner_score=owner_score, target_score=target_score,
                last_action=0, winner=winner, status="finished"))
        await ssn.commit()
        logging.info(
            f"Penalty {pen_id} | Keeper {user_id} saved pos {keeper_pick} | Winner {winner}")
        return penalty, result
    else:
        if penalty.kicker_pick == keeper_pick:
            if penalty.kicker == penalty.owner:
                owner_txt = penalty.owner_txt + "0"
                target_txt = penalty.target_txt
            else:
                owner_txt = penalty.owner_txt
                target_txt = penalty.target_txt + "0"
            owner_score = 0
            target_score = 0
        else:
            if penalty.kicker == penalty.owner:
                owner_txt = penalty.owner_txt + "1"
                target_txt = penalty.target_txt
                owner_score = 1
                target_score = 0
            else:
                owner_txt = penalty.owner_txt
                target_txt = penalty.target_txt + "1"
                owner_score = 0
                target_score = 1

        if penalty.turn_user_id == penalty.owner:
            kicker = penalty.owner
            keeper = penalty.target
        else:
            kicker = penalty.target
            keeper = penalty.owner

        date = dt.datetime.now()
        date_ts = int(date.timestamp())
        await ssn.execute(update(Penalty).filter(
            Penalty.id == pen_id).values(
                owner_txt=owner_txt, target_txt=target_txt,
                owner_score=Penalty.owner_score + owner_score,
                target_score=Penalty.target_score + target_score,
                kicker=kicker, keeper=keeper, last_action=date_ts + 60,
                kicker_pick=0, round=Penalty.round + 1))
        await ssn.commit()
        logging.info(
            f"Penalty {pen_id} | Keeper {user_id} saved  pos {keeper_pick}")

        return penalty, result


async def penalty_switch(ssn: AsyncSession, pen_id, bot):
    penalty_q = await ssn.execute(
        select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.turn_user_id == penalty.owner:
        owner_kind = "kicker"
        target_kind = "keeper"
    else:
        owner_kind = "keeper"
        target_kind = "kicker"

    msg_owner_id = await send_penalty_action(
        bot, penalty.owner, pen_id, owner_kind)
    await asyncio.sleep(.01)
    msg_target_id = await send_penalty_action(
        bot, penalty.target, pen_id, target_kind)

    if (msg_owner_id == 0) or (msg_target_id == 0):
        await ssn.execute(update(Penalty).filter(
            Penalty.id == pen_id).values(status="canceled", last_action=0))
        await ssn.commit()
        logging.info(f"Penalty {pen_id} canceled with error")
        return "error"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    await ssn.execute(update(Penalty).filter(
        Penalty.id == pen_id).values(
            owner_msg_id=msg_owner_id, target_msg_id=msg_target_id,
            last_action=date_ts + 60))
    await ssn.commit()
    return None


async def get_active_penalties(db):
    ssn: AsyncSession
    async with db() as ssn:
        penalties_q = await ssn.execute(
            select(Penalty).filter(Penalty.status == "active"))
        penalties = penalties_q.scalars().all()

        return penalties
