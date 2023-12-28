import logging
from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from keyboards.main_kbs import games_kb
from middlewares.actions import ActionMiddleware

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "startplay", flags=flags)
async def games_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = "Тут находятся мини-игры, в которые можешь поиграть с друзьями и выяснить, кто из вас лучший🥇"
    await c.message.edit_text(txt, reply_markup=games_kb)
