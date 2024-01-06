import asyncio
import datetime as dt
import logging
import random

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, CardPack, CardXPack, PayItem, Player, UserCard
from utils.misc import card_rarity_randomize


async def cancel_payment(ssn: AsyncSession, pay_id, user_id):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="canceled"))
    await ssn.commit()
    logging.info(f"User {user_id} canceled payment {pay_id}")

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    return user


async def add_new_payment(ssn: AsyncSession, user_id, label, url, kind, amount):
    pay = await ssn.merge(PayItem(
        label=label, url=url, user_id=user_id, amount=amount, kind=kind))
    await ssn.commit()
    return pay.id


async def get_payment_info(ssn: AsyncSession, pay_id):
    pay_q = await ssn.execute(select(PayItem).filter(PayItem.id == pay_id))
    pay = pay_q.fetchone()[0]
    return pay


async def add_ls_after_pay(ssn: AsyncSession, user_id, pay_id):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))

    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
            lucky_quants=Player.lucky_quants + 3,
            transactions=Player.transactions + 1))
    await ssn.commit()


async def add_leg_card_pack(ssn: AsyncSession, user_id, pay_id):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))

    leg_cards_q = await ssn.execute(
        select(CardItem).filter(CardItem.rarity == "ЛЕГЕНДАРНАЯ"))
    leg_cards = leg_cards_q.scalars().all()
    leg_card: CardItem = random.choice(leg_cards)

    points = leg_card.points
    u_cards_ids = []

    leg_usercard_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == user_id).filter(
            UserCard.card_id == leg_card.id))
    leg_usercard_res = leg_usercard_q.fetchone()
    if leg_usercard_res is None:
        duplicate = 0
    else:
        duplicate = 1

    leg_user_card = await ssn.merge(UserCard(
        user_id=user_id, card_id=leg_card.id, points=leg_card.points,
        card_rarity=leg_card.rarity, duplicate=duplicate))
    await ssn.commit()
    u_cards_ids.append(leg_user_card.id)

    for _ in range(9):
        rarity = await card_rarity_randomize("card")
        cards_q = await ssn.execute(
            select(CardItem).filter(CardItem.rarity == rarity))
        cards = cards_q.scalars().all()
        card: CardItem = random.choice(cards)
        points += card.points
        usercard_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.card_id == card.id))
        user_card_res = usercard_q.fetchone()
        if user_card_res is None:
            duplicate = 0
        else:
            duplicate = 1

        user_card = await ssn.merge(UserCard(
            user_id=user_id, card_id=card.id, points=card.points,
            card_rarity=card.rarity, duplicate=duplicate))
        await ssn.commit()
        u_cards_ids.append(user_card.id)

    new_pack = await ssn.merge(CardPack(user_id=user_id))
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
        rating=Player.rating + points,
        transactions=Player.transactions + 1,
        card_quants=Player.card_quants + 10))
    await ssn.commit()
    pack_id = new_pack.id

    for u_id in u_cards_ids:
        await ssn.merge(CardXPack(pack_id=pack_id, user_card_id=u_id))

    await ssn.commit()

    return pack_id


async def add_cards_pack(ssn: AsyncSession, user_id, quant, pay_id):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))

    points = 0
    u_cards_ids = []

    for _ in range(quant):
        rarity = await card_rarity_randomize("card")
        cards_q = await ssn.execute(
            select(CardItem).filter(CardItem.rarity == rarity))
        cards = cards_q.scalars().all()
        card: CardItem = random.choice(cards)
        points += card.points
        usercard_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.card_id == card.id))
        user_card_res = usercard_q.fetchone()
        if user_card_res is None:
            duplicate = 0
        else:
            duplicate = 1

        user_card = await ssn.merge(UserCard(
            user_id=user_id, card_id=card.id, points=card.points,
            card_rarity=card.rarity, duplicate=duplicate))
        await ssn.commit()
        u_cards_ids.append(user_card.id)

    new_pack = await ssn.merge(CardPack(user_id=user_id))
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
        rating=Player.rating + points,
        transactions=Player.transactions + 1,
        card_quants=Player.card_quants + quant))
    await ssn.commit()
    pack_id = new_pack.id

    for u_id in u_cards_ids:
        await ssn.merge(CardXPack(pack_id=pack_id, user_card_id=u_id))

    await ssn.commit()

    return pack_id
