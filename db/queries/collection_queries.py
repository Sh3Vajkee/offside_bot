from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, CardXPack, UserCard


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


async def get_pack_cards(ssn: AsyncSession, pack_id, user_id):
    pack_ids_q = await ssn.execute(select(
        CardXPack.user_card_id).filter(CardXPack.pack_id == pack_id))
    pack_ids = pack_ids_q.scalars().all()

    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == user_id).filter(
            UserCard.id.in_(pack_ids)).order_by(
                UserCard.points.desc()).options(
                    selectinload(UserCard.card)))
    cards = cards_q.scalars().all()

    return cards


async def get_rarity_cards(ssn: AsyncSession, rarity):
    if rarity == "all":
        cards_q = await ssn.execute(select(CardItem))
    else:
        cards_q = await ssn.execute(select(CardItem).filter(
            CardItem.rarity == rarity))
    cards = cards_q.scalars().all()

    return cards
