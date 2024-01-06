import logging
from textwrap import dedent

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.admin_queries import update_card_image, update_card_text
from db.queries.collection_queries import get_rarity_cards
from filters.filters import IsAdmin
from keyboards.admin_kbs import (adm_card_rarities_kb, adm_view_cards_kb,
                                 admin_cards_kb, admin_kb, back_to_admin_btn)
from keyboards.cb_data import PageCB
from utils.const import rarities
from utils.format_texts import format_view_my_cards_text
from utils.states import AdminStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "editcards", IsAdmin(), flags=flags)
async def edit_cards_cmd(c: CQ):
    txt = "🎭 Выберите формат отображения карточек"
    await c.message.edit_text(txt, reply_markup=admin_cards_kb)


@router.callback_query(F.data == "admcardsrarities", flags=flags)
async def adm_rarity_cards_cmd(c: CQ):
    txt = "Выберите редкость карт"
    await c.message.edit_text(txt, reply_markup=adm_card_rarities_kb)


@router.callback_query(
    F.data.startswith("admrarity_"), IsAdmin(), flags={"throttling_key": "pages"}
)
async def view_admin_rarity_cards_cmd(c: CQ, ssn, state: FSM):
    rarity = c.data.split("_")[-1]
    cards = await get_rarity_cards(ssn, rarity)

    page = 1
    last = len(cards)

    await state.clear()
    await c.message.delete()

    txt = await format_view_my_cards_text(cards[0])
    await c.message.answer_photo(
        cards[0].image, txt,
        reply_markup=adm_view_cards_kb(page, last, cards[0].id, "edit"))

    await state.set_state(AdminStates.view_cards)
    await state.update_data(cards=cards, kind="edit")


@router.callback_query(
    StateFilter(AdminStates.view_cards),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_adm_rarity_cards_cmd(c: CQ, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    kind = data.get("kind")

    card = cards[page-1]
    txt = await format_view_my_cards_text(card)

    media = types.InputMediaPhoto(caption=txt, media=card.image)

    try:
        await c.message.edit_media(
            media=media, reply_markup=adm_view_cards_kb(page, last, card.id, kind))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()


@router.callback_query(
    F.data.startswith("imgedit_"), IsAdmin(), flags=flags
)
async def edit_card_image_cmd(c: CQ, state: FSM):
    card_id = int(c.data.split("_")[-1])

    txt = c.message.html_text + "\n\nПришлите новое фото карточки"
    await c.message.edit_caption(caption=txt, reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.new_image)
    await state.update_data(card_id=card_id)


@router.message(StateFilter(AdminStates.new_image), F.photo, flags=flags)
async def save_new_card_image_cmd(m: Mes, state: FSM, ssn):
    data = await state.get_data()
    await state.clear()
    card_id = data.get("card_id")
    image = m.photo[-1].file_id
    await update_card_image(ssn, card_id, image)

    await m.answer(
        "✅ Новое фото для карточки установлено!", reply_markup=admin_kb)


@router.callback_query(
    F.data.startswith("txtedit_"), IsAdmin(), flags=flags
)
async def edit_card_text_cmd(c: CQ, state: FSM):
    card_id = int(c.data.split("_")[-1])

    footer_txt = """
    Укажите новые характеристики карточки в формате
    1.Имя игрока
    2.Никнейм игрока
    3.Команда игрока
    4.Редкость карточки
    5.Рейтинг карточки

    цифры указывать не надо
    """
    txt = c.message.html_text + "\n" + dedent(footer_txt)
    await c.message.edit_caption(caption=txt, reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.new_text)
    await state.update_data(card_id=card_id)


@router.message(StateFilter(AdminStates.new_text), F.text, flags=flags)
async def save_new_card_text_cmd(m: Mes, state: FSM, ssn):
    data = await state.get_data()
    await state.clear()
    card_id = data.get("card_id")

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
            await update_card_text(
                ssn, card_id, name, nickname, team, rarity, int(points))
            await m.answer("✅ Новые характеристики для карточки установлены!", reply_markup=admin_kb)
