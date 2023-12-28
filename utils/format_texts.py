from textwrap import dedent

from db.models import CardItem, Player, UserCard


async def format_new_free_card_text(card: CardItem):
    txt = f"""
    {card.name} aka {card.nickname}
    Рейтинг: <b>{card.points}</b>
    Редкость: <b>{card.rarity}</b>
    Команда: <b>{card.team}</b>
    """
    return dedent(txt)


async def format_view_my_cards_text(card: CardItem):
    txt = f"""
    {card.name} <b>{card.nickname}</b>
    Рейтинг: <b>{card.points}</b>
    Редкость: <b>{card.rarity}</b>
    Команда: <b>{card.team}</b>
    """
    return dedent(txt)


async def format_list_my_cards_text(cards):
    txt = "Список всех ваших карт:\n"
    card: UserCard
    for card in cards:
        txt += f"{card.card.nickname} | Рейтинг: {card.points} | {card.quant} шт."

    return txt


async def format_top_rating_text(tops, user: Player, place):
    txt = "🏆 Рейтинг игроков по картам\n"

    top: Player
    for num, top in enumerate(tops):
        if num == 0:
            plc = "🥇"
        elif num == 1:
            plc = "🥈"
        elif num == 2:
            plc = "🥉"
        else:
            plc = f"{num + 1}."

        txt += f"{plc} {top.username} - {top.rating}"

    txt += f"\n{place}. {user.username} - {user.rating}"

    return txt


async def format_top_penalty_text(tops, user: Player, place):
    txt = "🏆 Рейтинг игроков по пенальти\n"

    top: Player
    for num, top in enumerate(tops):
        if num == 0:
            plc = "🥇"
        elif num == 1:
            plc = "🥈"
        elif num == 2:
            plc = "🥉"
        else:
            plc = f"{num + 1}."

        txt += f"{plc} {top.username} - {top.penalty_rating}"

    txt += f"\n{place}. {user.username} - {user.penalty_rating}"

    return txt
