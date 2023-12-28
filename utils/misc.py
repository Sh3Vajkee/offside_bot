import random


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
