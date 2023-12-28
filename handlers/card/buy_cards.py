from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from keyboards.cards_kbs import buy_cards_kb

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "cardsstore", flags=flags)
async def buy_cards_cmd(c: CQ):
    txt = """
    🛍 Ты находишься в магазине карт, у нас есть несколько товаров:

    💰3 рандомных карточки - 170 руб
    💰5 рандомных карточек - 245 руб
    💰10 рандомных карточек - 425 руб
    💰50 рандомных карточек - 1990 руб
    💰Легендарный набор - 990 руб

    🏆 Легендарный набор содержит:
    1 рандомную Легендарную карту + 9 рандомных карт
    """
    await c.message.edit_text(dedent(txt), reply_markup=buy_cards_kb)
