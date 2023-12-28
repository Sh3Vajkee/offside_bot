from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem
from db.queries.card_queries import get_free_card
from keyboards.cards_kbs import accept_new_card_btn, card_kb, no_free_card_kb
from utils.format_texts import format_new_free_card_text
from utils.misc import format_delay_text

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "getcard", flags=flags)
async def get_card_cmd(c: CQ):
    txt = """
    🃏 Если ты хочешь получить карточку, то ты попал куда надо!

    Раз в 24 часа ты можешь получать одну карточку бесплатно, но если ты хочешь продвигаться по таблице рейтинга быстрее других и пополнять свою коллекцию, то рекомендуем тебе посетить магазин карт 🛍
    """
    await c.message.edit_text(dedent(txt), reply_markup=card_kb)


@router.callback_query(F.data == "getfreecard", flags=flags)
async def get_free_card_cmd(c: CQ, ssn):
    card: CardItem = await get_free_card(ssn, c.from_user.id)
    if isinstance(card, int):
        timer = await format_delay_text(card)
        txt = f"Ты недавно получал свою бесплатную карточку! Следующую ты можешь получить через {timer} ⏱️. Если не хочешь ждать - приобретай дополнительные карточки"
        await c.message.edit_text(txt, reply_markup=no_free_card_kb)
    elif card == "no_cards":
        await c.answer("⚠️ Возникла ошибка! Попробуй позже")
    else:
        txt = await format_new_free_card_text(card)
        await c.message.delete()
        await c.message.answer_photo(
            card.image, txt, reply_markup=accept_new_card_btn)
