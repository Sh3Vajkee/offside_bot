import logging

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.queries.card_queries import get_user_card_rarities
from db.queries.collection_queries import (get_pack_cards, get_user_list_cards,
                                           get_user_rarity_cards)
from keyboards.cards_kbs import (filter_my_cards_kb, my_card_list_kb,
                                 my_card_rarities_kb, my_cards_kb,
                                 pack_cards_kb)
from keyboards.cb_data import PageCB
from utils.format_texts import (format_list_my_cards_text,
                                format_view_my_cards_text)
from utils.misc import calc_cards_quant
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "mycards", flags=flags)
async def get_card_cmd(c: CQ):
    txt = "🎭 Выберите формат отображения коллекции"
    await c.message.edit_text(txt, reply_markup=filter_my_cards_kb)


@router.callback_query(F.data == "back_to_mycards", flags=flags)
async def get_card_cmd(c: CQ, state: FSM):
    txt = "🎭 Выберите формат отображения коллекции"
    await c.message.delete()
    await state.clear()
    await c.message.answer(txt, reply_markup=filter_my_cards_kb)


@router.callback_query(
    F.data.startswith("rarity_"), flags={"throttling_key": "pages"}
)
async def view_rarity_cards_cmd(c: CQ, ssn, state: FSM):
    rarity = c.data.split("_")[-1]
    cards = await get_user_rarity_cards(ssn, c.from_user.id, rarity, "nosort")
    if len(cards) == 0:
        if rarity == "all":
            await c.answer("ℹ️ У тебя еще нет карт")
        else:
            await c.answer("ℹ️ У тебя нет карт этой редкости")
    else:
        page = 1
        last = len(cards)

        await state.clear()
        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=my_cards_kb(page, last, "nosort"))

        await state.set_state(UserStates.mycards)
        await state.update_data(cards=cards, sorting="nosort")


@router.callback_query(
    StateFilter(UserStates.mycards),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_rarity_cards_cmd(c: CQ, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")

    card = cards[page-1]
    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media, reply_markup=my_cards_kb(page, last, sorting))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()


@router.callback_query(
    F.data.startswith("sortmycards_"), flags={"throttling_key": "pages"}
)
async def view_sorted_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    cards = await get_user_rarity_cards(ssn, c.from_user.id, "all", sorting)
    if len(cards) == 0:
        await c.answer("ℹ️ У тебя еще нет карт")
        await c.message.delete()
    else:
        page = 1
        last = len(cards)

        await state.clear()
        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=my_cards_kb(page, last, sorting))

        await state.set_state(UserStates.mycards)
        await state.update_data(cards=cards, sorting=sorting)


@router.callback_query(F.data == "mycardsrarities", flags=flags)
async def rarity_cards_cmd(c: CQ, ssn):
    txt = "Выберите редкость карт"
    rarities = await get_user_card_rarities(ssn, c.from_user.id)
    await c.message.edit_text(txt, reply_markup=my_card_rarities_kb(rarities))


@router.callback_query(F.data == "list_my_cards", flags=flags)
async def list_of_my_cards_cmd(c: CQ, ssn):
    cards = await get_user_list_cards(ssn, c.from_user.id)
    data = await calc_cards_quant(cards)
    txts = await format_list_my_cards_text(data)
    await c.message.delete()

    for num, txt in enumerate(txts):
        if num + 1 == len(txts):
            await c.message.answer(txt, reply_markup=my_card_list_kb)
        else:
            await c.message.answer(txt)


@router.callback_query(F.data.startswith("viewpack_"), flags=flags)
async def view_pack_cards_cmd(c: CQ, ssn, state: FSM):
    pack_id = int(c.data.split("_")[-1])

    cards = await get_pack_cards(ssn, pack_id, c.from_user.id)
    page = 1
    last = len(cards)

    await state.clear()

    txt = await format_view_my_cards_text(cards[0].card)
    await c.message.answer_photo(
        cards[0].card.image, txt,
        reply_markup=pack_cards_kb(page, last))

    await state.set_state(UserStates.pack_cards)
    await state.update_data(cards=cards)


@router.callback_query(
    StateFilter(UserStates.pack_cards),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_pack_cards_cmd(c: CQ, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")

    card = cards[page-1]
    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media, reply_markup=pack_cards_kb(page, last))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()
