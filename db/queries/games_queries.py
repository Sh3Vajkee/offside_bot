import datetime as dt
import logging
import random

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Player, UserCard
from utils.misc import card_rarity_randomize, send_action_emoji


async def lucky_shot(ssn: AsyncSession, user_id, bot):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    if user.last_lucky < date_ts:
        value = await send_action_emoji(bot, user_id, "⚽")
        if value < 3:
            card = "lose"
            await ssn.execute(update(Player).filter(
                Player.id == user_id).values(last_lucky=date_ts + 14400))

            logging.info(f"User {user_id} lost in lucky shot")
        else:
            rarity = await card_rarity_randomize("ls")

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
                last_lucky=date_ts + 14400,
                rating=Player.rating + card.points,
                card_quants=Player.card_quants + 1))

            logging.info(f"User {user_id} won card {card.id} in lucky shot")

        await ssn.commit()
        return card, user, "attempts"

    elif user.lucky_quants > 0:
        value = await send_action_emoji(bot, user_id, "⚽")
        if value < 3:
            card = "lose"
            await ssn.execute(update(Player).filter(
                Player.id == user_id).values(
                    lucky_quants=Player.lucky_quants - 1))

            logging.info(f"User {user_id} lost in lucky shot")

        else:
            rarity = await card_rarity_randomize("ls")

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
                lucky_quants=Player.lucky_quants - 1,
                rating=Player.rating + card.points,
                card_quants=Player.card_quants + 1))

            logging.info(f"User {user_id} won card {card.id} in lucky shot")

        await ssn.commit()
        return card, user, "free"

    else:
        return user.last_lucky - date_ts
