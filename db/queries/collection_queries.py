from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import UserCard


async def get_user_rarity_cards(ssn: AsyncSession, user_id, rarity, sorting):
    if rarity == "all":
        if sorting == "up":
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.duplicate == 0).order_by(
                    UserCard.points).options(
                        selectinload(UserCard.card)))
        elif sorting == "down":
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.duplicate == 0).order_by(
                        UserCard.points.desc()).options(
                            selectinload(UserCard.card)))
        else:
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.duplicate == 0).options(
                        selectinload(UserCard.card)))
    else:
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.card_rarity == rarity).filter(
                    UserCard.duplicate == 0).options(
                        selectinload(UserCard.card)))
    cards = cards_q.scalars().all()

    return cards


async def get_user_list_cards(ssn: AsyncSession, user_id):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == user_id).order_by(
        UserCard.points).options(
        selectinload(UserCard.card)))
    cards = cards_q.scalars().all()

    return cards
