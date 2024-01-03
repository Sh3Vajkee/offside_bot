import datetime as dt
import logging
import random

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Penalty, Player, Trade, UserCard
from utils.misc import send_penalty_offer


async def check_for_active_penalty(ssn: AsyncSession, user_id):
    penalty_q = await ssn.execute(select(Penalty).filter(
        or_(Penalty.target == user_id, Penalty.owner == user_id)).filter(
            Trade.status == "active"))
    penalty_res = penalty_q.fetchone()
    if penalty_res is None:
        return "available"

    return "already_playing"


async def create_new_penalty(ssn: AsyncSession, user_id, username, target_username, bot):
    penalty_q = await ssn.execute(select(Penalty).filter(
        or_(Penalty.target == user_id, Penalty.owner == user_id)).filter(
            Trade.status == "active"))
    penalty_res = penalty_q.fetchone()
    if penalty_res is not None:
        return "already_playing"

    target_q = await ssn.execute(
        select(Player).filter(Player.username.ilike(target_username)))
    target_res = target_q.fetchone()
    if target_res is None:
        return "not_found"

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]
    target: Player = target_res[0]

    rating_delta = abs(user.penalty_rating - target.penalty_rating)
    if rating_delta > 300:
        return "rating_diff"

    target_penalty_q = await ssn.execute(select(Penalty).filter(
        or_(Penalty.target == target.id, Penalty.owner == target.id)).filter(
            Trade.status == "active"))
    target_penalty_res = target_penalty_q.fetchone()
    if target_penalty_res is not None:
        return "target_already_playing"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    penalty = await ssn.merge(Trade(
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
            f"User {user_id} created new penaly #{penalty_id} to {target.id} ({target})")
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
                            status="target_auto_win", last_action=0))
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
                            status="owner_auto_win", last_action=0))
                    logging.info(f"Penalty {penalty_id} owner auto win")

            await ssn.commit()
            return penalty
        return False
