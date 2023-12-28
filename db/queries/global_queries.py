import datetime as dt
import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Player


async def check_and_add_user(ssn: AsyncSession, user_id, username):
    user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
    user_res = user_q.fetchone()
    if user_res is None:
        date = dt.datetime.now()
        date_ts = int(date.timestamp())
        date_str = date.strftime("%d.%m.%Y %H:%M")

        await ssn.merge(Player(
            id=user_id, joined_at_ts=date_ts, joined_at_txt=date_str,
            username=username, last_open=date_ts - 86500))
        await ssn.commit()
        logging.info(f"New User {username} ({user_id})")
    else:
        res: Player = user_res[0]
        if res.username != username:
            await ssn.execute(update(Player).filter(
                Player.id == res.id).values(username=username))
            await ssn.commit()
    return res


async def get_user_info(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    return user


async def get_top_rating(ssn: AsyncSession, user_id):
    top_q = await ssn.execute(
        select(Player).order_by(Player.rating.desc()).limit(10))
    top = top_q.scalars().all()

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    user_top_q = await ssn.execute(select(Player.id).filter(
        Player.rating >= user.rating).filter(
            Player.id != user_id))
    user_top = user_top_q.scalars().all()
    place = len(user_top) + 1

    return top, user, place


async def get_top_penalty(ssn: AsyncSession, user_id):
    top_q = await ssn.execute(
        select(Player).order_by(Player.penalty_rating.desc()).limit(10))
    top = top_q.scalars().all()

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    user_top_q = await ssn.execute(select(Player.id).filter(
        Player.penalty_rating >= user.penalty_rating).filter(
            Player.id != user_id))
    user_top = user_top_q.scalars().all()
    place = len(user_top) + 1

    return top, user, place
