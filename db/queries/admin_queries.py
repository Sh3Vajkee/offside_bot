import datetime as dt
import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Player


async def get_user_role(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    return user.role


async def add_new_card(ssn: AsyncSession, data: dict, image):
    card = await ssn.merge(CardItem(
        name=data['name'], team=data['team'], nickname=data['nickname'],
        image=image, rarity=data['rarity'], points=data['points']))
    await ssn.commit()
    logging.info(f"Added new card {card.id}")
