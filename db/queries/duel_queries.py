import logging

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, CardXPack, Duel, DuelCard, UserCard

# async def check_active_duel()


async def get_duel_cards_for_create(ssn: AsyncSession, user_id, sorting, u_ids):
    if sorting == "up":
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.id.not_in(u_ids)).order_by(
                    UserCard.points).options(
                        selectinload(UserCard.card)))
    elif sorting == "down":
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.id.not_in(u_ids)).order_by(
                    UserCard.points.desc()).options(
                        selectinload(UserCard.card)))
    else:
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.id.not_in(u_ids)).options(
                    selectinload(UserCard.card)))
    cards = cards_q.scalars().all()

    return cards


async def add_duel_first_card(ssn: AsyncSession, user_id, user_card_id):
    card_q = await ssn.execute(select(UserCard).filter(
        UserCard.id == user_card_id).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    card = card_q.fetchone()[0]
    return card


async def create_duel_lobby(
        ssn: AsyncSession, user_id, username, selected, rating, msg_id):
    duel_q = await ssn.execute(select(Duel).filter(
        or_(Duel.target == user_id, Duel.owner == user_id)).filter(
            Duel.status == "active"))
    duel_res = duel_q.fetchone()
    if duel_res is not None:
        return "already_playing"

    cards_q = await ssn.execute(select(UserCard.id).filter(
        UserCard.id.in_(selected)).filter(
            UserCard.user_id == user_id))
    cards = cards_q.scalars().all()
    if len(cards) != len(selected):
        return "error"

    new_duel = await ssn.merge(Duel(
        owner_msg_id=msg_id, owner_points=rating,
        owner=user_id, owner_username=username))
    await ssn.commit()
    for u_id in selected:
        await ssn.merge(
            DuelCard(duel_id=new_duel.id, user_card_id=u_id,
                     kind="owner", ))
    await ssn.commit()
    logging.info(
        f"User {user_id} ({username}) created duel lobby {new_duel.id}")
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == new_duel.id))
    duel = duel_q.fetchone()[0]
    return duel


async def get_user_duel_cards(ssn: AsyncSession, user_id, sorting, duel_id, kind):
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if duel.status != "active":
        return "not_active"

    u_ids_q = await ssn.execute(select(DuelCard.user_card_id).filter(
        DuelCard.id == duel_id).filter(
            DuelCard.kind == kind))
    u_ids = u_ids_q.scalars().all()

    if len(u_ids) >= 5:
        return "limit"

    if sorting == "up":
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.id.not_in(u_ids)).order_by(
                    UserCard.points).options(
                        selectinload(UserCard.card)))
    elif sorting == "down":
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.id.not_in(u_ids)).order_by(
                    UserCard.points.desc()).options(
                        selectinload(UserCard.card)))
    else:
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.id.not_in(u_ids)).options(
                    selectinload(UserCard.card)))
    cards = cards_q.scalars().all()

    return cards, duel


async def owner_duel_candcel(ssn: AsyncSession, duel_id):
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if duel.status != "active":
        return "not_active"

    await ssn.execute(update(Duel).filter(
        Duel.id == duel_id).values(status="canceled"))
    await ssn.commit()
    logging.info(f"User {duel.owner} canceled duel {duel_id}")
    return duel


async def update_owner_msg_id(ssn: AsyncSession, duel_id, msg_id):
    await ssn.execute(update(Duel).filter(
        Duel.id == duel_id).values(owner_msg_id=msg_id))
    await ssn.commit()


async def add_owner_card_to_duel(ssn: AsyncSession, user_id, duel_id, user_card_id):
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if duel.status != "active":
        return "not_active"

    card_q = await ssn.execute(select(UserCard).filter(
        UserCard.id == user_card_id).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    card = card_q.fetchone()[0]

    if duel.target == 0:
        await ssn.execute(update(Duel).filter(
            Duel.id == duel_id).values(
                owner_points=Duel.owner_points + card.points))
        await ssn.merge(DuelCard(
            duel_id=duel_id, user_card_id=user_card_id, kind="owner"))
        await ssn.commit()
        return duel, card
    else:
        pass
