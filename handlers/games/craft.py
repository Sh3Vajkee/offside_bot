import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ

from db.queries.craft_queries import craft_card, get_user_duplicates
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.main_kbs import craft_kb
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_craft_text, format_new_free_card_text

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "craft", flags=flags)
async def craft_cmd(c: CQ, ssn, action_queue):
    duplicates = await get_user_duplicates(ssn, c.from_user.id)
    txt = await format_craft_text(duplicates)
    await c.message.edit_text(txt, reply_markup=craft_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("craft_"), flags=flags)
async def craft_card_cmd(c: CQ, ssn, action_queue):
    rarity = c.data.split("_")[-1]

    if rarity == "ОБЫЧНАЯ":
        next_rarity = "НЕОБЫЧНАЯ"
    elif rarity == "НЕОБЫЧНАЯ":
        next_rarity = "РЕДКАЯ"
    elif rarity == "РЕДКАЯ":
        next_rarity = "ЭПИЧЕСКАЯ"
    elif rarity == "ЭПИЧЕСКАЯ":
        next_rarity = "УНИКАЛЬНАЯ"
    elif rarity == "УНИКАЛЬНАЯ":
        next_rarity = "ЛЕГЕНДАРНАЯ"

    card = await craft_card(ssn, c.from_user.id, rarity, next_rarity, 5)
    if card == "not_enough":
        await c.answer(
            "У тебя недостаточно карт этой редкости", show_alert=True)
    elif card == "limit":
        await c.answer(
            "Ты уже крафтил легендарную карту сегодня", show_alert=True)
    else:
        logging.info(
            f"User {c.from_user.id} crafted card {card.id} ({next_rarity}) from 5x{rarity} cards")

        txt = await format_new_free_card_text(card)
        await c.message.delete()
        await c.message.answer_photo(
            card.image, txt, reply_markup=accept_new_card_btn)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
