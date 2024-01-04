import datetime as dt
import logging

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Player, Trade, UserCard


async def check_target_trade(ssn: AsyncSession, user_id, card_id):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == card_id).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    if len(cards) == 0:
        return "no_card"

    trade_q = await ssn.execute(select(Trade).filter(
        or_(Trade.target == user_id, Trade.owner == user_id)).filter(
            Trade.status.in_(["target_wait", "owner_wait"])))
    trade_res = trade_q.fetchone()
    if trade_res is None:
        return "username"
    else:
        trade: Trade = trade_res[0]
        if trade.owner == user_id:
            return "already_trading"
        else:
            if trade.status == "owner_wait":
                return "already_trading"
            else:
                await ssn.execute(update(Trade).filter(
                    Trade.id == trade.id).values(target_card_id=card_id))
                await ssn.commit()

                return trade, cards[0].card


async def create_new_trade(
        ssn: AsyncSession, user_id, username, card_id, target_username):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == card_id).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    if len(cards) == 0:
        return "no_card"

    target_q = await ssn.execute(
        select(Player).filter(Player.username.ilike(target_username)))
    target_res = target_q.fetchone()
    if target_res is None:
        return "not_found"

    target: Player = target_res[0]
    if user_id == target.id:
        return "not_found"

    trade = await ssn.merge(Trade(
        status="target_wait", owner=user_id,
        owner_username=username, owner_card_id=card_id,
        target=target.id, target_username=target.username))
    await ssn.commit()

    trade_id = trade.id

    return trade_id, target.id, cards[0].card


async def update_trade_status(ssn: AsyncSession, user_id, card_id, trade_id):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == card_id).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    if len(cards) == 0:
        return "no_card"

    trade_q = await ssn.execute(select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]
    if trade.status == "target_wait":
        await ssn.execute(update(Trade).filter(
            Trade.id == trade.id).values(
                target_card_id=card_id, status="owner_wait"))
        await ssn.commit()
        return trade, cards[0].card

    return "trade_not_available"


async def decline_trade(ssn: AsyncSession, trade_id):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]
    if trade.status not in ("target_wait", "owner_wait"):
        return "not_active"

    await ssn.execute(update(Trade).filter(
        Trade.id == trade_id).values(status="declined"))
    await ssn.commit()

    return trade


async def decline_last_trade(ssn: AsyncSession, user_id):
    trade_q = await ssn.execute(select(Trade).filter(
        or_(Trade.target == user_id, Trade.owner == user_id)).filter(
            Trade.status.in_(["target_wait", "owner_wait"])))
    trade_res = trade_q.fetchone()
    if trade_res is None:
        return "not_found"

    await ssn.execute(update(Trade).filter(
        Trade.id == trade_res[0].id).values(status="canceled"))
    await ssn.commit()

    return trade_res[0]


async def close_trade(ssn: AsyncSession, trade_id):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]

    if trade.status != "owner_wait":
        return "already_closed"

    owner_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == trade.owner_card_id).filter(
            UserCard.user_id == trade.owner).options(
                selectinload(UserCard.card)).order_by(
                    UserCard.duplicate.desc()))
    owner_cards = owner_cards_q.scalars().all()

    target_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == trade.target_card_id).filter(
            UserCard.user_id == trade.target).options(
                selectinload(UserCard.card)).order_by(
                    UserCard.duplicate.desc()))
    target_cards = target_cards_q.scalars().all()

    if (len(owner_cards) == 0) or (len(target_cards) == 0):
        await ssn.execute(update(Trade).filter(
            Trade.id == trade_id).values(status="error"))
        await ssn.commit()
        return "error"

    owner_card: UserCard = owner_cards[0]
    target_card: UserCard = target_cards[0]

    # Добавляем карту второго игрока первому игроку
    target_card_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == trade.owner).filter(
        UserCard.card_id == target_card.card_id).filter(
        UserCard.duplicate == 1))
    target_card_res = target_card_q.fetchone()
    if target_card_res is None:
        owner_duplicate = 0
    else:
        owner_duplicate = 1

    await ssn.execute(update(UserCard).filter(
        UserCard.id == target_card.id).values(
        user_id=trade.owner, duplicate=owner_duplicate))

    # Добавляем карту первого игрока второму игроку
    owner_card_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == trade.target).filter(
        UserCard.card_id == owner_card.card_id).filter(
        UserCard.duplicate == 1))
    owner_card_res = owner_card_q.fetchone()
    if owner_card_res is None:
        target_duplicate = 0
    else:
        target_duplicate = 1

    await ssn.execute(update(UserCard).filter(
        UserCard.id == owner_card.id).values(
        user_id=trade.target, duplicate=target_duplicate))

    if owner_card.points > target_card.points:
        diff = owner_card.points - target_card.points
        owner_rating = -diff
        target_rating = diff
    elif target_card.points > owner_card.points:
        diff = target_card.points - owner_card.points
        owner_rating = diff
        target_rating = -diff
    else:
        owner_rating = 0
        target_rating = 0

    await ssn.execute(update(Player).filter(
        Player.id == trade.owner).values(rating=Player.rating + owner_rating))
    await ssn.execute(update(Player).filter(
        Player.id == trade.target).values(rating=Player.rating + target_rating))
    await ssn.execute(update(Trade).filter(
        Trade.id == trade_id).values(status="finished"))
    await ssn.commit()
    logging.info(
        f"Traded {trade_id} | user1 {trade.owner} card {trade.owner_card_id} | user2 {trade.target} card {trade.target_card_id}")

    return trade, owner_card.card, target_card.card
