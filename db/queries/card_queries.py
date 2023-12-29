import datetime as dt
import logging
import random

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Player, UserCard
from utils.misc import card_rarity_randomize


async def get_free_card(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    if date_ts < user.last_open:
        return user.last_open - date_ts

    rarity = await card_rarity_randomize()
    cards_q = await ssn.execute(
        select(CardItem).filter(CardItem.rarity == rarity))
    cards = cards_q.scalars().all()

    if len(cards) == 0:
        return "no_cards"

    card: CardItem = random.choice(cards)

    usercard_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == user_id).filter(
            UserCard.card_id == card.id))
    user_card_res = usercard_q.fetchone()
    if user_card_res is None:
        duplicate = 0
    else:
        duplicate = 1

    await ssn.merge(UserCard(
        user_id=user_id, card_id=card.id,
        card_rarity=card.rarity, duplicate=duplicate))

    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
        last_open=date_ts + 86400,
        rating=Player.rating + card.points,
        card_quants=Player.card_quants + 1))

    await ssn.commit()

    return card
