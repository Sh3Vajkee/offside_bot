from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.global_queries import check_and_add_user
from keyboards.main_kbs import back_to_info_btn, info_kb, start_kb

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "info", flags=flags)
async def view_info_cmd(c: CQ):
    await c.message.edit_text(
        "В этом разделе можно найти информацию про наш проект",
        reply_markup=info_kb)


@router.callback_query(F.data == "about_cards", flags=flags)
async def about_cards_cmd(c: CQ):
    txt = """
    Каждая карта имеет свою редкость и количество баллов, которые она добавляет к твоему рейтингу:

    1) Легендарная редкость: Карта добавляет 1000 баллов к твоей коллекции.

    2) Уникальная редкость: Карта добавляет 500 баллов к твоей коллекции.

    3) Эпическая редкость: Карта добавляет 250 баллов к твоей коллекции.

    4) Необычная редкость: Карта добавляет 100 баллов к твоей коллекции.

    5) Обычная редкость: Карта добавляет 50 баллов к твоей коллекции.
    """
    await c.message.edit_text(dedent(txt), reply_markup=back_to_info_btn)


@router.callback_query(F.data == "about_penalty", flags=flags)
async def about_penalty_cmd(c: CQ):
    txt = """
    Игра в пенальти, это отдельный режим в OFFSIDE, в которой тебе нужно забивать и отбивать мячи.

    Чтобы начать игру в пенальти, вам нужно:
    1. Зайти в раздел  «🎲 Мини-игры»
    2. Выбрать игру «⚽️ Пенальти»
    3. Отправить приглашение пользователю с которым вы хотите сыграть.
    Игрок пригласивший второго пользователя будет первым делать удары. Второй игрок будет начинать в роли вратаря, его задача: стараться выбрать верную цифру, чтобы прыгнуть в определенный угол и отразить удар. Далее вы меняетесь местами, такой процесс повторяется пять раз для каждого игрока. В итоге, выигрывает тот игрок, который забил больше всего мячей. В результате игры возможна ничья.

    За каждую победу игроку начисляется  +25 баллов, а за поражение снимается -25 баллов. Всем игрокам дается изначальный рейтинг 100. За согласование ничьей рейтинг у обоих игроков не изменяется.
    """
    await c.message.edit_text(dedent(txt), reply_markup=back_to_info_btn)


@router.callback_query(F.data == "about_luckystrike", flags=flags)
async def about_luckystrike_cmd(c: CQ):
    txt = """
    Чтобы начать игру в удачный удар, вам нужно:
    1. Зайти в раздел  «🎲 Мини-игры»
    2. Выбрать игру «☘️ Удачный удар»
    3. Нажать на кнопку «⚽️ Сделать удар»

    ☘️ Удачный удар - это мини-игра, в которой ты делаешь 1 удар по воротам.
    Если забиваешь - получаешь одну рандомную карточку.
    Если не забиваешь - пробуешь еще через 4 часа.
    В день доступно 2 бесплатные попытки.
    Если тебе сегодня везет и хочешь сделать больше ударов по воротам - можешь приобрести дополнительные попытки.
    """
    await c.message.edit_text(dedent(txt), reply_markup=back_to_info_btn)
