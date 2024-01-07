import datetime
import logging
import random

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, CardXPack, Duel, DuelCard, Player, UserCard

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
    if (duel.status != "active") or (user_id not in (duel.owner, duel.target)):
        return "not_available"

    u_ids_q = await ssn.execute(select(DuelCard.user_card_id).filter(
        DuelCard.duel_id == duel_id).filter(
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


async def update_target_msg_id(ssn: AsyncSession, duel_id, msg_id):
    await ssn.execute(update(Duel).filter(
        Duel.id == duel_id).values(target_msg_id=msg_id))
    await ssn.commit()


async def update_msg_ids(ssn: AsyncSession, duel_id, owner_msg_id, target_msg_id):
    await ssn.execute(update(Duel).filter(
        Duel.id == duel_id).values(
            owner_msg_id=owner_msg_id, target_msg_id=target_msg_id))
    await ssn.commit()


async def update_owner_msg_id_db(db, duel_id, msg_id):
    ssn: AsyncSession
    async with db() as ssn:
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

    date = datetime.datetime.now()
    date_ts = int(date.timestamp())

    await ssn.execute(update(Duel).filter(
        Duel.id == duel_id).values(
            owner_ready=0, target_ready=0,
            owner_ts=0, target_ts=date_ts + 60,
            owner_points=Duel.owner_points + card.points))
    await ssn.merge(DuelCard(
        duel_id=duel_id, user_card_id=user_card_id, kind="owner"))
    await ssn.commit()
    return duel


async def get_active_duel_lobbies(ssn: AsyncSession, low, high):
    duels_q = await ssn.execute(select(Duel).filter(
        Duel.owner_points >= low).filter(
            Duel.owner_points <= high).filter(
                Duel.target == 0).filter(
                    Duel.status == "active").order_by(Duel.id.desc()))
    duels = duels_q.scalars().all()
    return duels


async def join_duel(ssn: AsyncSession, user_id, username, duel_id, msg_id):
    duels_q = await ssn.execute(select(Duel).filter(
        or_(Duel.target == user_id, Duel.owner == user_id)).filter(
            Duel.status == "active"))
    duels_res = duels_q.fetchone()
    if duels_res is not None:
        return "already_playing"

    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if (duel.status != "active") or (duel.target != 0):
        return "not_available"

    date = datetime.datetime.now()
    date_ts = int(date.timestamp())
    await ssn.execute(update(Duel).filter(
        Duel.id == duel_id).values(
            target=user_id, target_username=username,
            target_points=0, target_ready=0,
            target_msg_id=msg_id, target_ts=date_ts + 60))
    await ssn.commit()

    return duel


async def leave_from_duel(ssn: AsyncSession, user_id, duel_id):
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if (duel.status != "active") or (duel.target != user_id):
        return "not_available"

    await ssn.execute(update(Duel).filter(
        Duel.id == duel_id).values(
            target=0, target_username="nouser",
            target_msg_id=0, target_ts=0))
    await ssn.execute(delete(DuelCard).filter(
        DuelCard.duel_id == duel_id).filter(DuelCard.kind == "target"))
    await ssn.commit()

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    return duel, user


async def get_duel_cards(ssn: AsyncSession, user_id, duel_id):
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if (duel.status != "active") or (user_id not in (duel.owner, duel.target)):
        return "not_available"

    owner_cards_ids_q = await ssn.execute(select(DuelCard.user_card_id).filter(
        DuelCard.duel_id == duel_id).filter(DuelCard.kind == "owner"))
    owner_cards_ids = owner_cards_ids_q.scalars().all()

    owner_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(owner_cards_ids)).options(
        selectinload(UserCard.card)))
    owner_cards = owner_cards_q.scalars().all()

    target_cards_ids_q = await ssn.execute(select(DuelCard.user_card_id).filter(
        DuelCard.duel_id == duel_id).filter(DuelCard.kind == "target"))
    target_cards_ids = target_cards_ids_q.scalars().all()

    target_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(target_cards_ids)).options(
        selectinload(UserCard.card)))
    target_cards = target_cards_q.scalars().all()

    return duel, owner_cards, target_cards


async def add_target_card_to_duel(ssn: AsyncSession, user_id, duel_id, user_card_id):
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if (duel.status != "active") or (user_id not in (duel.owner, duel.target)):
        return "not_available"

    card_q = await ssn.execute(select(UserCard).filter(
        UserCard.id == user_card_id).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    card = card_q.fetchone()[0]

    date = datetime.datetime.now()
    date_ts = int(date.timestamp())

    await ssn.execute(update(Duel).filter(
        Duel.id == duel_id).values(
            owner_ready=0, target_ready=0,
            owner_ts=0, target_ts=date_ts + 60,
            target_points=Duel.target_points + card.points))
    await ssn.merge(DuelCard(
        duel_id=duel_id, user_card_id=user_card_id, kind="target"))
    await ssn.commit()
    return duel


async def get_duel_info(ssn: AsyncSession, duel_id, user_id):
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if (duel.status != "active") or (user_id not in (duel.owner, duel.target)):
        return "not_available"

    return duel


async def duel_user_ready(ssn: AsyncSession, user_id, duel_id):
    duel_q = await ssn.execute(select(Duel).filter(Duel.id == duel_id))
    duel: Duel = duel_q.fetchone()[0]
    if (duel.status != "active") or (user_id not in (duel.owner, duel.target)):
        return "not_available"

    if user_id == duel.owner:
        if duel.owner_ready == 1:
            return "already_ready"
        elif duel.target_points == 0:
            return "target_cards_not_found"
    else:
        if duel.target_ready == 1:
            return "already_ready"
        elif duel.target_points == 0:
            return "your_cards_not_found"

    if duel.owner == user_id:
        if duel.target_ready == 0:
            await ssn.execute(update(Duel).filter(
                Duel.id == duel_id).values(owner_ready=1))
            await ssn.commit()
            return duel, "not_ready"
        else:
            total_rating = duel.owner_points + duel.target_points
            result = random.randint(1, total_rating)
            if result <= duel.owner_points:
                target_cards_ids_q = await ssn.execute(select(DuelCard.user_card_id).filter(
                    DuelCard.duel_id == duel_id).filter(DuelCard.kind == "target"))
                target_cards_ids = target_cards_ids_q.scalars().all()

                target_cards_q = await ssn.execute(select(UserCard.points).filter(
                    UserCard.id.in_(target_cards_ids)))
                target_cards = target_cards_q.scalars().all()

                if len(target_cards) != len(target_cards_ids):
                    await ssn.execute(update(Duel).filter(
                        Duel.id == duel_id).values(
                        owner_ts=0, target_ts=0, status="error"))
                    await ssn.commit()
                    return duel, "error"

                rating = sum(target_cards)
                await ssn.execute(update(UserCard).filter(
                    UserCard.id.in_(target_cards_ids)).values(user_id=duel.owner))
                await ssn.execute(update(Player).filter(
                    Player.id == duel.owner).values(
                        rating=Player.rating + rating,
                        card_quants=Player.card_quants + len(target_cards_ids)))
                await ssn.execute(update(Player).filter(
                    Player.id == duel.target).values(
                        rating=Player.rating - rating,
                        card_quants=Player.card_quants - len(target_cards_ids)))
                await ssn.execute(update(Duel).filter(
                    Duel.id == duel_id).values(
                        owner_ts=0, target_ts=0,
                    winner=duel.owner, status="finished"))
                await ssn.commit()
                return duel, "owner_win"
            else:
                owner_cards_ids_q = await ssn.execute(select(DuelCard.user_card_id).filter(
                    DuelCard.duel_id == duel_id).filter(DuelCard.kind == "owner"))
                owner_cards_ids = owner_cards_ids_q.scalars().all()

                owner_cards_q = await ssn.execute(select(UserCard.points).filter(
                    UserCard.id.in_(owner_cards_ids)))
                owner_cards = owner_cards_q.scalars().all()

                if len(owner_cards) != len(owner_cards_ids):
                    await ssn.execute(update(Duel).filter(
                        Duel.id == duel_id).values(
                        owner_ts=0, target_ts=0, status="error"))
                    await ssn.commit()
                    return duel, "error"

                rating = sum(owner_cards)
                await ssn.execute(update(UserCard).filter(
                    UserCard.id.in_(owner_cards_ids)).values(user_id=duel.target))
                await ssn.execute(update(Player).filter(
                    Player.id == duel.owner).values(
                        rating=Player.rating - rating,
                        card_quants=Player.card_quants - len(owner_cards_ids)))
                await ssn.execute(update(Player).filter(
                    Player.id == duel.target).values(
                        rating=Player.rating + rating,
                        card_quants=Player.card_quants + len(owner_cards_ids)))
                await ssn.execute(update(Duel).filter(
                    Duel.id == duel_id).values(
                        owner_ts=0, target_ts=0,
                    winner=duel.target, status="finished"))
                await ssn.commit()
                return duel, "target_win"
    else:
        if duel.owner_ready == 0:
            date = datetime.datetime.now()
            date_ts = int(date.timestamp())

            await ssn.execute(update(Duel).filter(
                Duel.id == duel_id).values(
                    owner_ts=date_ts + 60, target_ts=0,
                    target_ready=1))
            await ssn.commit()
            return duel, "not_ready"
        else:
            total_rating = duel.owner_points + duel.target_points
            result = random.randint(1, total_rating)

            if result <= duel.owner_points:
                target_cards_ids_q = await ssn.execute(select(DuelCard.user_card_id).filter(
                    DuelCard.duel_id == duel_id).filter(DuelCard.kind == "target"))
                target_cards_ids = target_cards_ids_q.scalars().all()

                target_cards_q = await ssn.execute(select(UserCard.points).filter(
                    UserCard.id.in_(target_cards_ids)))
                target_cards = target_cards_q.scalars().all()

                if len(target_cards) != len(target_cards_ids):
                    await ssn.execute(update(Duel).filter(
                        Duel.id == duel_id).values(
                        owner_ts=0, target_ts=0, status="error"))
                    await ssn.commit()
                    return duel, "error"

                rating = sum(target_cards)
                await ssn.execute(update(UserCard).filter(
                    UserCard.id.in_(target_cards_ids)).values(user_id=duel.owner))
                await ssn.execute(update(Player).filter(
                    Player.id == duel.owner).values(
                        rating=Player.rating + rating,
                        card_quants=Player.card_quants + len(target_cards_ids)))
                await ssn.execute(update(Player).filter(
                    Player.id == duel.target).values(
                        rating=Player.rating - rating,
                        card_quants=Player.card_quants - len(target_cards_ids)))
                await ssn.execute(update(Duel).filter(
                    Duel.id == duel_id).values(
                        owner_ts=0, target_ts=0,
                    winner=duel.owner, status="finished"))
                await ssn.commit()
                return duel, "owner_win"
            else:
                owner_cards_ids_q = await ssn.execute(select(DuelCard.user_card_id).filter(
                    DuelCard.duel_id == duel_id).filter(DuelCard.kind == "owner"))
                owner_cards_ids = owner_cards_ids_q.scalars().all()

                owner_cards_q = await ssn.execute(select(UserCard.points).filter(
                    UserCard.id.in_(owner_cards_ids)))
                owner_cards = owner_cards_q.scalars().all()

                if len(owner_cards) != len(owner_cards_ids):
                    await ssn.execute(update(Duel).filter(
                        Duel.id == duel_id).values(
                        owner_ts=0, target_ts=0, status="error"))
                    await ssn.commit()
                    return duel, "error"

                rating = sum(owner_cards)
                await ssn.execute(update(UserCard).filter(
                    UserCard.id.in_(owner_cards_ids)).values(user_id=duel.target))
                await ssn.execute(update(Player).filter(
                    Player.id == duel.owner).values(
                        rating=Player.rating - rating,
                        card_quants=Player.card_quants - len(owner_cards_ids)))
                await ssn.execute(update(Player).filter(
                    Player.id == duel.target).values(
                        rating=Player.rating + rating,
                        card_quants=Player.card_quants + len(owner_cards_ids)))
                await ssn.execute(update(Duel).filter(
                    Duel.id == duel_id).values(
                        owner_ts=0, target_ts=0,
                    winner=duel.target, status="finished"))
                await ssn.commit()
                return duel, "target_win"


async def check_duel(db, duel_id, kind, user_id, date_ts):
    ssn: AsyncSession
    async with db() as ssn:
        duel_q = await ssn.execute(
            select(Duel).filter(Duel.id == duel_id))
        duel: Duel = duel_q.fetchone()[0]
        if duel.status == "active":
            if kind == "owner":
                if date_ts == duel.owner_ts:
                    await ssn.execute(update(Duel).filter(
                        Duel.id == duel_id).values(status="timedout"))
                    await ssn.commit()
                    logging.info(f"Duel {duel_id} owner timed out")
                    return duel, "owner_timeout"
                else:
                    return duel, "continued"
            else:
                if (user_id == duel.target) and (date_ts == duel.target_ts):
                    old_user_id = duel.target
                    old_msg_id = duel.target_msg_id
                    old_username = duel.target_username
                    await ssn.execute(update(Duel).filter(
                        Duel.id == duel_id).values(
                            target=0, target_username="nouser",
                            target_msg_id=0, target_ts=0))
                    await ssn.execute(delete(DuelCard).filter(
                        DuelCard.duel_id == duel_id).filter(DuelCard.kind == "target"))
                    await ssn.commit()
                    logging.info(f"Duel {duel_id} target timed out")
                    return duel, "target_timeout", old_user_id, old_msg_id, old_username
                else:
                    return duel, "continued"


async def get_active_duels(db):
    ssn: AsyncSession
    async with db() as ssn:
        duels_q = await ssn.execute(
            select(Duel).filter(Duel.status == "active"))
        duels = duels_q.scalars().all()

        return duels
