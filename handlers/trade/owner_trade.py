import logging
from textwrap import dedent

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem, Trade
from db.queries.collection_queries import get_user_rarity_cards
from db.queries.trade_queries import (check_target_trade, close_trade,
                                      create_new_trade, decline_trade)
from keyboards.cb_data import PageCB
from keyboards.main_kbs import to_main_btn
from keyboards.trade_kbs import (after_trade_kb, card_trade_kb,
                                 offer_to_owner_kb, offer_to_target_kb,
                                 trade_kb)
from utils.format_texts import format_view_my_cards_text
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "trade", flags=flags)
async def trade_cmd(c: CQ, state: FSM):
    await state.clear()
    await c.message.delete()
    await c.message.answer(
        "🧳 Выберите формат отображения коллекции",
        reply_markup=trade_kb)


@router.callback_query(
    F.data.startswith("trdrar_"), flags={"throttling_key": "pages"}
)
async def view_owner_trade_rarity_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")
    rarity = c_data[1]

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
            reply_markup=card_trade_kb(
                page, last, "nosort", cards[0].card_id))

        await state.set_state(UserStates.owner_trade)
        await state.update_data(cards=cards, sorting="nosort")


@router.callback_query(
    StateFilter(UserStates.owner_trade),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_owner_trade_cards_cmd(c: CQ, state: FSM, callback_data: PageCB):
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
            media=media, reply_markup=card_trade_kb(
                page, last, sorting, card.card_id))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()


@router.callback_query(F.data.startswith("chstrdcard_"), flags=flags)
async def choose_trade_card_cmd(c: CQ, ssn, state: FSM, bot: Bot):
    card_id = int(c.data.split("_")[-1])
    res = await check_target_trade(ssn, c.from_user.id, card_id)
    if res == "no_card":
        await c.message.delete()
        await state.clear()
    elif res == "username":
        txt = "Напишите юзернейм пользователя (@username), с которым хотите обменяться"
        await c.message.answer(txt)
        await state.clear()
        await state.set_state(UserStates.target_trade)
        await state.update_data(card_id=card_id)
        await c.answer()
    elif res == "already_trading":
        await c.message.delete()
        await state.clear()
        txt = "У тебя уже есть активные обмены"
        await c.message.answer(txt, reply_markup=to_main_btn)
    else:
        trade: Trade = res[0]
        card: CardItem = res[1]
        logging.info(
            f"User {c.from_user.id} answered on trade {trade.id} with card {card_id}")

        await c.message.delete()
        await c.message.answer(
            "✅ Предложение обмена успешно отправлено, ожидайте")

        txt = f"""
        ✅ Пользователь ответил на ваше предложение обмена!
        Вы получите эту карточку за вашу:
        {card.name} aka {card.nickname}
        С редкостью - {card.rarity}
        """
        await bot.send_photo(
            trade.owner, card.image, caption=dedent(txt),
            reply_markup=offer_to_owner_kb(trade.id))


@router.message(StateFilter(UserStates.target_trade), F.text, flags=flags)
async def save_target_trade_username_cmd(m: Mes, state: FSM, ssn, bot: Bot):
    data = await state.get_data()
    await state.clear()
    card_id = data.get("card_id")

    target = m.text

    if m.from_user.username:
        username = f"@{m.from_user.username}"
    else:
        username = m.from_user.mention_html()

    res = await create_new_trade(
        ssn, m.from_user.id, username, card_id, target)
    if res == "no_card":
        await m.answer(
            "⚠️ Возникла ошибка при создании обмена",
            reply_markup=to_main_btn)
    elif res == "not_found":
        txt = "Этому пользователю нельзя предложить обмен, попробуйте снова"
        await m.answer(txt, reply_markup=to_main_btn)

    else:
        trade_id = res[0]
        target_id = res[1]
        card: CardItem = res[2]
        logging.info(
            f"User {m.from_user.id} created new trade #{trade_id} to {target_id} ({target})")

        txt = f"✅ Предложение обмена успешно отправлено пользователю - {target}"
        await m.answer(txt)

        target_txt = f"Вам поступило предложение обмена от - {username}"
        await bot.send_photo(
            target_id, card.image, caption=target_txt,
            reply_markup=offer_to_target_kb(trade_id))


@router.callback_query(F.data.startswith("ownerdeclinetrade_"), flags=flags)
async def decline_owner_trade_cmd(c: CQ, ssn, state: FSM, bot: Bot):
    trade_id = int(c.data.split("_")[-1])
    res: Trade = await decline_trade(ssn, c.from_user.id, trade_id)

    await c.message.delete()
    if res == "not_active":
        await state.clear()
        txt = "Это предложение обмена больше недоступно"
        await c.message.answer(txt, reply_markup=to_main_btn)
    else:
        logging.info(f"User {c.from_user.id} canceled trade {trade_id}")

        await c.message.delete()
        await c.message.answer("❌ Вы отменили обмен!", reply_markup=after_trade_kb)

        await bot.send_message(
            res.target, "❌ Увы, сделка сорвалась.", reply_markup=after_trade_kb)
