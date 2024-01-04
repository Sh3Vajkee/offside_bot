import asyncio
import logging
from textwrap import dedent

from aiogram import Bot, F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.admin_queries import add_new_card
from filters.filters import IsAdmin
from keyboards.admin_kbs import admin_kb, back_to_admin_btn
from keyboards.main_kbs import cancel_btn
from utils.const import rarities
from utils.states import AdminStates, UserStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "addcard", IsAdmin(), flags=flags)
async def add_card_cmd(c: CQ, state: FSM):
    await state.clear()

    txt = """
    Для начала укажите характеристики карточки в формате
    1.Имя игрока
    2.Никнейм игрока
    3.Команда игрока
    4.Редкость карточки
    5.Рейтинг карточки

    цифры указывать не надо
    """

    await c.message.delete()
    await c.message.answer(dedent(txt), reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.add_card)


@router.message(StateFilter(AdminStates.add_card), F.text, flags=flags)
async def add_new_card_cmd(m: Mes, state: FSM):
    data = m.text.split("\n")
    if len(data) != 5:
        await state.clear()
        await m.answer(
            "Некорректный ввод данных, попробуйте снова",
            reply_markup=back_to_admin_btn)
    else:
        name = data[0]
        nickname = data[1]
        team = data[2]
        rarity = data[3]
        points = data[4]

        if rarity not in rarities:
            await m.answer(
                "Такая редкость не найдена, попробуйте снова",
                reply_markup=back_to_admin_btn)
        elif not points.isdigit():
            await m.answer(
                "Некорректный ввод данных, попробуйте снова",
                reply_markup=back_to_admin_btn)
        else:
            await m.answer(
                "Теперь отправьте фото карточки игрока",
                reply_markup=back_to_admin_btn)
            await state.set_state(AdminStates.card_image)
            await state.update_data(
                name=name, nickname=nickname, team=team,
                rarity=rarity, points=int(points))


@router.message(StateFilter(AdminStates.card_image), F.photo, flags=flags)
async def save_new_card_cmd(m: Mes, state: FSM, ssn):
    image = m.photo[-1].file_id
    data = await state.get_data()
    await state.clear()
    await add_new_card(ssn, data, image)

    txt = f"""
    Новая карточка добавлена!

    {data['name']} aka {data['nickname']}
    Рейтинг: <b>{data['points']}</b>
    Редкость: <b>{data['rarity']}</b>
    Команда: <b>{data['team']}</b>
    """
    await m.answer_photo(
        image, dedent(txt), reply_markup=back_to_admin_btn)
