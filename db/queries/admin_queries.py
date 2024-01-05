import datetime as dt
import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Player, PromoCode, UserCard


async def get_user_role(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    return user.role


async def add_new_card(ssn: AsyncSession, data: dict, image):
    card = await ssn.merge(CardItem(
        name=data['name'], team=data['team'], nickname=data['nickname'],
        image=image, rarity=data['rarity'], points=data['points']))
    await ssn.commit()
    logging.info(f"Added new card {card.id}")


async def update_card_image(ssn: AsyncSession, card_id, image):
    await ssn.execute(update(CardItem).filter(
        CardItem.id == card_id).values(image=image))
    await ssn.commit()


async def update_card_text(ssn: AsyncSession, card_id, name, nickname, team, rarity, points):
    await ssn.execute(update(CardItem).filter(
        CardItem.id == card_id).values(
            name=name, nickname=nickname,
            team=team, rarity=rarity, points=points))
    await ssn.execute(update(UserCard).filter(
        UserCard.card_id == card_id).values(
            points=points, card_rarity=rarity))
    await ssn.commit()


async def add_new_promo(ssn: AsyncSession, card_id, text, quant):
    await ssn.merge(PromoCode(promo=text, card_id=card_id, quant=quant))
    await ssn.commit()


async def get_promos(ssn: AsyncSession):
    promos_q = await ssn.execute(select(PromoCode).order_by(PromoCode.id))
    promos = promos_q.scalars().all()
    return promos


async def delete_promo(ssn: AsyncSession, promo_id):
    await ssn.execute(delete(PromoCode).filter(PromoCode.id == promo_id))
    await ssn.commit()

    promos_q = await ssn.execute(select(PromoCode).order_by(PromoCode.id))
    promos = promos_q.scalars().all()
    return promos


async def get_adm_user_info(ssn: AsyncSession, username):
    if username.isdigit():
        user_q = await ssn.execute(
            select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username)))
        user_res = user_q.fetchone()

    if user_res is None:
        res = "not_found"
    else:
        res = user_res[0]

    return res
