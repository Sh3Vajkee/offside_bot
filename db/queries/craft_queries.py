import random

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Player, UserCard


async def get_user_duplicates(ssn: AsyncSession, user_id):
    rarities = [
        "ОБЫЧНАЯ", "НЕОБЫЧНАЯ",  "РЕДКАЯ",
        "ЭПИЧЕСКАЯ", "УНИКАЛЬНАЯ"]

    duplicates = []
    for rarity in rarities:
        cards_q = await ssn.execute(select(UserCard.id).filter(
            UserCard.user_id == user_id).filter(
                UserCard.card_rarity == rarity).filter(
                    UserCard.duplicate == 1))
        cards = cards_q.scalars().all()
        duplicates.append(len(cards))

    return duplicates


async def craft_card(ssn: AsyncSession, user_id, rarity, next_rarity, quant):
    used_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == user_id).filter(
            UserCard.card_rarity == rarity).filter(
                UserCard.duplicate == 1).limit(quant))
    used_cards = used_cards_q.scalars().all()
    if len(used_cards) < quant:
        return "not_enough"

    cards_q = await ssn.execute(
        select(CardItem).filter(CardItem.rarity == next_rarity))
    cards = cards_q.scalars().all()
    card: CardItem = random.choice(cards)

    usercard_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == user_id).filter(
            UserCard.card_id == card.id))
    user_card_res = usercard_q.fetchone()
    if user_card_res is None:
        duplicate = 0
    else:
        duplicate = 1

    rating = card.points
    u_ids = []
    for usercard in used_cards:
        rating -= usercard.points
        u_ids.append(usercard.id)

    await ssn.merge(UserCard(
        user_id=user_id, card_id=card.id, points=card.points,
        card_rarity=card.rarity, duplicate=duplicate))

    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
        rating=Player.rating + rating,
        card_quants=Player.card_quants - 4))

    await ssn.execute(delete(UserCard).filter(UserCard.id.in_(u_ids)))
    await ssn.commit()

    return card
