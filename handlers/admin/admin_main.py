import asyncio
import logging

from aiogram import Bot, F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from filters.filters import IsAdmin
from keyboards.admin_kbs import admin_cards_kb, admin_kb, admin_promos_kb
from keyboards.main_kbs import cancel_btn
from utils.states import AdminStates

flags = {"throttling_key": "default"}
router = Router()


@router.message(Command("admin"), IsAdmin(), flags=flags)
async def admin_cmd(m: Mes, state: FSM):
    await state.clear()
    txt = "Добро пожаловать в админскую панель\nВыберете раздел с которым вы хотите работать"
    await m.answer(txt, reply_markup=admin_kb)


@router.callback_query(F.data == "back_to_admin", IsAdmin(), flags=flags)
async def back_to_admin_cmd(c: CQ, state: FSM):
    await state.clear()
    txt = "Добро пожаловать в админскую панель\nВыберете раздел с которым вы хотите работать"
    await c.message.delete()
    await c.message.answer(txt, reply_markup=admin_kb)


@router.callback_query(F.data == "admincards", IsAdmin(), flags=flags)
async def admin_cards_cmd(c: CQ, state: FSM):
    await state.clear()
    txt = "Вы находитесь в разделе управления карточками!\nВыберете действие, которое хотите выполнить"
    await c.message.edit_text(txt, reply_markup=admin_cards_kb)


@router.callback_query(F.data == "adminpromos", IsAdmin(), flags=flags)
async def admin_promos_cmd(c: CQ, state: FSM):
    await state.clear()
    txt = "Вы находитесь в разделе управления промокодами!\nВыберете действие, которое хотите выполнить"
    await c.message.edit_text(txt, reply_markup=admin_promos_kb)


@router.message(Command("ph"), IsAdmin(), flags=flags)
async def image_id_cmd(m: Mes, state: FSM):
    await m.answer("Need Image")
    await state.set_state(AdminStates.image_id)


@router.message(StateFilter(AdminStates.image_id), F.photo, flags=flags)
async def send_image_id_cmd(m: Mes, state: FSM):
    await state.clear()

    image = m.photo[-1].file_id
    await m.answer(f"<code>{image}</code>")
