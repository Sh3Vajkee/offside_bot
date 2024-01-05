import datetime as dt
import logging
import random

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Player, PromoCode, PromoUser, UserCard
from utils.misc import card_rarity_randomize


async def get_free_card(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    if date_ts < user.last_open:
        return user.last_open - date_ts

    rarity = await card_rarity_randomize("card")
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
        user_id=user_id, card_id=card.id, points=card.points,
        card_rarity=card.rarity, duplicate=duplicate))

    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
        last_open=date_ts + 86400,
        rating=Player.rating + card.points,
        card_quants=Player.card_quants + 1))

    await ssn.commit()

    return card


async def use_promo(ssn: AsyncSession, user_id, promocode):
    promo_q = await ssn.execute(
        select(PromoCode).filter(PromoCode.promo.ilike(promocode)))
    promo_res = promo_q.fetchone()
    if promo_res is None:
        return "not_found"

    promo: PromoCode = promo_res[0]

    promo_user_q = await ssn.execute(select(PromoUser.id).filter(
        PromoUser.promo_id == promo.id).filter(
            PromoUser.user_id == user_id))
    promo_user_res = promo_user_q.fetchone()
    if promo_user_res is not None:
        return "already_used"

    if promo.card_id == 0:
        rarity = await card_rarity_randomize("card")
        cards_q = await ssn.execute(
            select(CardItem).filter(CardItem.rarity == rarity))
        cards = cards_q.scalars().all()

        if len(cards) == 0:
            return "no_cards"

        card: CardItem = random.choice(cards)
    else:
        card_q = await ssn.execute(
            select(CardItem).filter(CardItem.id == promo.card_id))
        card: CardItem = card_q.fetchone()[0]

    usercard_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == user_id).filter(
        UserCard.card_id == card.id))
    user_card_res = usercard_q.fetchone()
    if user_card_res is None:
        duplicate = 0
    else:
        duplicate = 1

    await ssn.merge(UserCard(
        user_id=user_id, card_id=card.id, points=card.points,
        card_rarity=card.rarity, duplicate=duplicate))

    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
        rating=Player.rating + card.points,
        card_quants=Player.card_quants + 1))

    await ssn.merge(PromoUser(promo_id=promo.id, user_id=user_id))

    if promo.quant <= 1:
        await ssn.execute(delete(PromoCode).filter(PromoCode.id == promo.id))
    else:
        await ssn.execute(update(PromoCode).filter(
            PromoCode.id == promo.id).values(quant=PromoCode.quant - 1))

    await ssn.commit()
    logging.info(f"User {user_id} used promo {promocode} ({promo.id})")

    return card
