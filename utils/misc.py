import logging
import random

from aiogram import Bot

from db.models import UserCard
from keyboards.games_kbs import penalty_offer_kb


async def card_rarity_randomize(kind):
    if kind == "card":
        rarities = [
            "ОБЫЧНАЯ", "НЕОБЫЧНАЯ",  "РЕДКАЯ",
            "ЭПИЧЕСКАЯ", "УНИКАЛЬНАЯ", "ЛЕГЕНДАРНАЯ"]
        chances = [30, 25, 20, 15, 9, 1]
    else:
        rarities = [
            "ОБЫЧНАЯ", "НЕОБЫЧНАЯ",  "РЕДКАЯ",
            "ЭПИЧЕСКАЯ", "УНИКАЛЬНАЯ"]
        chances = [30, 25, 25, 19, 1]

    result = random.choices(rarities, chances, k=1)
    return result[0]


async def format_delay_text(delay):
    if delay >= 3600:
        hours = delay // 3600
        minutes = (delay % 3600) // 60
        txt = f"{hours}ч {minutes}мин"
    else:
        minutes = delay // 60
        txt = f"{minutes}мин"

    return txt


async def calc_cards_quant(cards):
    data = {}
    card: UserCard
    for card in cards:
        if str(card.card_id) in data:
            quant = data[str(card.card_id)]['quant']
            quant += 1
            data[str(card.card_id)]['quant'] = quant
        else:
            data[str(card.card_id)] = {
                'nickname': card.card.nickname,
                'rating': card.points, 'quant': 1
            }

    return data


async def send_action_emoji(bot: Bot, user_id, emoji):
    msg = await bot.send_dice(user_id, emoji=emoji)
    value = msg.dice.value

    return value


async def send_penalty_offer(bot: Bot, user_id, username, pen_id):
    txt = f"{username} предлагает вам сыграть в Пенальти!"

    msg_id = 0
    try:
        msg = await bot.send_message(
            user_id, txt, reply_markup=penalty_offer_kb(pen_id))
        msg_id = msg.message_id
    except Exception as error:
        logging.error(f"Send error | chat {user_id}\n{error}")

    return msg_id
