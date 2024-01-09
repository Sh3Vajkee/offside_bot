import datetime
from textwrap import dedent

from db.models import CardItem, Duel, Penalty, Player, UserCard


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


async def format_list_my_cards_text(cards: dict):
    txt = "Список всех ваших карт:\n"
    for k, v in cards.items():
        txt += f"\n{v['nickname']} | Рейтинг: {v['rating']} | {v['quant']} шт."

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
            plc = f" {num + 1}."

        txt += f"\n{plc} {top.username} - {top.rating}"

    if place > len(tops):
        txt += f"\n\n{place}. {user.username} - {user.rating}"

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
            plc = f" {num + 1}."

        txt += f"\n{plc} {top.username} - {top.penalty_rating}"

    if place > len(tops):
        txt += f"\n\n{place}. {user.username} - {user.penalty_rating}"

    return txt


async def format_penalty_round_result_text(penalty: Penalty, result):
    # Условие инвертировано, так как уже произошла смена сторон
    if penalty.keeper == penalty.owner:
        keeper_username = penalty.target_username
        kicker_username = penalty.owner_username
    else:
        keeper_username = penalty.owner_username
        kicker_username = penalty.target_username

    if result:
        keeper_res_txt = f"🏆 Ты отбил удар\n{kicker_username} бил в тот же угол\n"
        kicker_res_txt = f"❌ Увы ты не забил\n{keeper_username} угадал твой удар\n"
    else:
        keeper_res_txt = f"❌ Ты пропустил гол\n{kicker_username} бил в другой угол\n"
        kicker_res_txt = f"⚽️ ГОЛ!!!\n{keeper_username} прыгнул в другую сторону\n"

    owner_res_txt = penalty.owner_txt.replace("0", "❌").replace("1", "⚽️")
    target_res_txt = penalty.target_txt.replace("0", "❌").replace("1", "⚽️")

    if (penalty.round % 2) == 0:
        target_res_txt += "⌛️"
    else:
        owner_res_txt += "⌛️"

    # Условие инвертировано, так как уже произошла смена сторон
    if penalty.keeper == penalty.target:
        keeper_txt = keeper_res_txt + "Результаты твоих ударов:\n" + \
            owner_res_txt + "\nРезультаты ударов противника:\n" + target_res_txt
        kicker_txt = kicker_res_txt + "Результаты твоих ударов:\n" + \
            target_res_txt + "\nРезультаты ударов противника:\n" + owner_res_txt

    else:
        keeper_txt = keeper_res_txt + "Результаты твоих ударов:\n" + \
            target_res_txt + "\nРезультаты ударов противника:\n" + owner_res_txt
        kicker_txt = kicker_res_txt + "Результаты твоих ударов:\n" + \
            owner_res_txt + "\nРезультаты ударов противника:\n" + target_res_txt

    return keeper_txt, kicker_txt


async def format_penalty_final_result_text(penalty: Penalty):
    owner_res_txt = f"Результаты ударов {penalty.owner_username}\n"
    target_res_txt = f"Результаты ударов {penalty.target_username}\n"

    owner_res_txt += penalty.owner_txt.replace("0", "❌").replace("1", "⚽️")
    target_res_txt += penalty.target_txt.replace("0", "❌").replace("1", "⚽️")

    if penalty.owner_card_id == 0:
        if penalty.owner == penalty.winner:
            winner_txt = f"\nПобедитель - {penalty.owner_username}"
        elif penalty.target == penalty.winner:
            winner_txt = f"\nПобедитель - {penalty.target_username}"
        else:
            winner_txt = "\n🏆 Вы забили одинаковое количество голов! Предлагаем вам переигровку или же ничью, выбор за вами!"
    else:
        if penalty.owner == penalty.winner:
            winner_txt = f"\n{penalty.owner_username} победил и получил карту соперника"
        elif penalty.target == penalty.winner:
            winner_txt = f"\n{penalty.target_username} победил и получил карту соперника"
        else:
            winner_txt = "\n🏆 Вы забили одинаковое количество голов! Предлагаем вам переигровку или же ничью, выбор за вами!"

    return target_res_txt + "\n" + owner_res_txt + winner_txt


async def format_user_info_text(user: Player):
    last_date = datetime.datetime.fromtimestamp(user.last_open - 86400)
    date_str = last_date.strftime("%d.%m.%Y %H:%M")
    txt = f"""
    Данные по пользователю {user.username} (ID {user.id})

    Дата регистрации - {user.joined_at_txt}
    Собранное количество карточек - {user.card_quants}
    Рейтинг собранных карточек - {user.rating}
    Рейтинг в игре пенальти - {user.penalty_rating}

    Забирал бесплатную карточку - {date_str}
    Количество транзакций - {user.transactions}
    """
    return dedent(txt)


async def format_craft_text(duplicates):
    txt = f"""
    🛠️ Ты находишься в меню крафта.

    Тут ты можешь обменять несколько карт одной редкости на карту более высокой редкости.

    <b>Количество карт:</b>

    ⚪️ Обычные карты: {duplicates[0]}
    🟡 Необычные карты: {duplicates[1]}
    🔵 Редкие карты: {duplicates[2]}
    🟣 Эпические карты: {duplicates[3]}
    🟢 Уникальные карты: {duplicates[4]}

    <b>Чтобы осуществить обмен - нужно иметь 5 карт одной редкости.</b>
    """
    return dedent(txt)
