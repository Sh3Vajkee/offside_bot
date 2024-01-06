import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ

from db.queries.craft_queries import craft_card, get_user_duplicates
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.duel_kbs import duel_kb
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_craft_text, format_new_free_card_text

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "duel", flags=flags)
async def duel_cmd(c: CQ, action_queue):
    txt = """
    ⚔️ В Дуэли карт ты ставишь свои карты на кон против других игроков.
    Один игрок может поставить на кон 5 карт любой редкости.

    За победу ты получаешь карты противника, которые он поставил на дуэль.
    За поражение - теряешь свои, которые поставил на дуэль.

    Ты можешь либо создать свое лобби, либо войти в лобби другого игрока
    """
    await c.message.edit_text(dedent(txt), reply_markup=duel_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
