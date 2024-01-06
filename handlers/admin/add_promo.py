from textwrap import dedent

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.admin_queries import add_new_promo, delete_promo, get_promos
from db.queries.collection_queries import get_rarity_cards
from filters.filters import IsAdmin
from keyboards.admin_kbs import (adm_view_cards_kb, admin_kb,
                                 back_to_admin_btn, promo_kb, view_promos_kb)
from utils.format_texts import format_view_my_cards_text
from utils.states import AdminStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "addpromo", IsAdmin(), flags=flags)
async def add_promo_cmd(c: CQ, state: FSM):
    await state.clear()

    txt = """
    Напишите промокод, который хотите добавить
    Чтобы указать количество использований напишите это число через пробел от промокода
    """
    await c.message.edit_text(dedent(txt), reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.promo_text)


@router.message(StateFilter(AdminStates.promo_text), F.text, flags=flags)
async def save_promo_text_cmd(m: Mes, state: FSM, ssn):
    data = m.text.split()
    if len(data) == 2:
        quant = int(data[1])
    else:
        quant = 2000000

    text = data[0]
    print(data)
    txt = "Теперь нажмите кнопку выбрать карточку, чтобы она выдавалась при вводе промокода"
    await m.answer(txt, reply_markup=promo_kb)
    await state.set_state(AdminStates.promo_card)
    await state.update_data(text=text, quant=quant)


@router.callback_query(
    F.data == "choosepromocard", IsAdmin(),
    flags={"throttling_key": "pages"}
)
async def choose_promo_card_cmd(c: CQ, state: FSM, ssn):
    rarity = "all"
    cards = await get_rarity_cards(ssn, rarity)

    page = 1
    last = len(cards)

    await c.message.delete()

    txt = await format_view_my_cards_text(cards[0])
    await c.message.answer_photo(
        cards[0].image, txt,
        reply_markup=adm_view_cards_kb(page, last, cards[0].id, "promo"))

    await state.set_state(AdminStates.view_cards)
    await state.update_data(cards=cards, kind="promo")


@router.callback_query(
    StateFilter(AdminStates.view_cards),
    F.data.startswith("prmcard_"), IsAdmin(), flags=flags
)
async def save_new_promo_cmd(c: CQ, state: FSM, ssn):
    card_id = int(c.data.split("_")[-1])
    data = await state.get_data()
    await state.clear()
    text = data.get("text")
    quant = data.get("quant")

    await add_new_promo(ssn, card_id, text, quant)
    txt = "Промокод был успешно добавлен! Время его проверить"
    await c.message.delete()
    await c.message.answer(txt, reply_markup=admin_kb)


@router.callback_query(F.data == "randompromocards", IsAdmin(), flags=flags)
async def random_promo_card_cmd(c: CQ, state: FSM, ssn):
    card_id = 0
    data = await state.get_data()
    await state.clear()
    text = data.get("text")
    quant = data.get("quant")

    await add_new_promo(ssn, card_id, text, quant)
    txt = "Промокод был успешно добавлен! Время его проверить"
    await c.message.delete()
    await c.message.answer(txt, reply_markup=admin_kb)


@router.callback_query(F.data == "delpromos", IsAdmin(), flags=flags)
async def view_promos_cmd(c: CQ, ssn):
    promos = await get_promos(ssn)

    txt = """
    Выберете промокод для удаления
    Все промокоды указаны в формате промокод - карточка
    """
    await c.message.edit_text(dedent(txt), reply_markup=view_promos_kb(promos))


@router.callback_query(
    F.data.startswith("delpromo_"), IsAdmin(), flags=flags
)
async def delete_promo_cmd(c: CQ, ssn):
    promo_id = int(c.data.split("_")[-1])

    promos = await delete_promo(ssn, promo_id)

    await c.answer("Промокод удален", show_alert=True)
    await c.message.edit_reply_markup(reply_markup=view_promos_kb(promos))
