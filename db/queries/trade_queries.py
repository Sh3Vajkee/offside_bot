import datetime as dt
import logging

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Player, Trade, UserCard


async def check_target_trade(ssn: AsyncSession, user_id, card_id):
    # cards_q = await ssn.execute(select(UserCard).filter(
    #     UserCard.card_id == card_id).filter(
    #         UserCard.user_id == user_id).order_by(
    #             UserCard.duplicate.desc()))
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

    trade = await ssn.merge(Trade(
        status="target_wait", owner=user_id,
        owner_username=username, owner_card_id=card_id,
        target=target.id, target_username=target.username))
    await ssn.commit()

    trade_id = trade.id

    return trade_id, target.id, cards[0].card


async def update_trade_status(ssn: AsyncSession, user_id, card_id, trade_id):
    # cards_q = await ssn.execute(select(UserCard).filter(
    #     UserCard.card_id == card_id).filter(
    #         UserCard.user_id == user_id).order_by(
    #             UserCard.duplicate.desc()))
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
            Trade.id == trade.id).values(target_card_id=card_id))
        await ssn.commit()
        return trade, cards[0].card

    return "trade_not_available"
