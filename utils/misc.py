import random

from db.models import UserCard


async def card_rarity_randomize():
    rarities = [
        "ОБЫЧНАЯ", "НЕОБЫЧНАЯ",  "РЕДКАЯ",
        "ЭПИЧЕСКАЯ", "УНИКАЛЬНАЯ", "ЛЕГЕНДАРНАЯ"]

    chances = [30, 25, 20, 15, 9, 1]

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
