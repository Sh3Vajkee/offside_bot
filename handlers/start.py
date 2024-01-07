from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.global_queries import check_and_add_user, get_user_info
from keyboards.main_kbs import main_kb, start_kb, sub_kb
from utils.const import channel_username

flags = {"throttling_key": "default"}
router = Router()


@router.message(Command("start"), flags=flags)
async def start_cmd(m: Mes, state: FSM, ssn, bot: Bot):
    await state.clear()

    if m.from_user.username:
        username = f"@{m.from_user.username}"
    else:
        username = m.from_user.full_name

    await check_and_add_user(ssn, m.from_user.id, username)
    txt = """
    👋 <b>Добро пожаловать в OFFSide</b>

    ⚽️ Здесь ты сможешь собирать карточки своих любимых футболистов из медиафутбола и играть в мини-игры.

    🏆 У нас есть таблицы рейтинга среди коллекционеров карточек и игроков в мини-игры! Приобретай карточки и побеждай в мини-играх, чтобы подняться в рейтинге и обойти своих друзей.

    Все правила игры вы можете узнать в разделе: 
    «ℹ️ <b>Информация</b>»

    Если ты готов к игре, то нажимай
    «🎮 <b>Начать игру</b>»

    <i>Все персонажи игры являются вымышленными, любые совпадения — случайны.</i>
    """

    await m.answer(dedent(txt), reply_markup=start_kb)


@router.callback_query(F.data == "backtostart", flags=flags)
async def back_to_start_cmd(c: CQ):
    txt = """
    👋 <b>Добро пожаловать в OFFSide</b>

    ⚽️ Здесь ты сможешь собирать карточки своих любимых футболистов из медиафутбола и играть в мини-игры.

    🏆 У нас есть таблицы рейтинга среди коллекционеров карточек и игроков в мини-игры! Приобретай карточки и побеждай в мини-играх, чтобы подняться в рейтинге и обойти своих друзей.

    Все правила игры вы можете узнать в разделе: 
    «ℹ️ <b>Информация</b>»

    Если ты готов к игре, то нажимай
    «🎮 <b>Начать игру</b>»

    <i>Все персонажи игры являются вымышленными, любые совпадения — случайны.</i>
    """
    await c.message.edit_text(dedent(txt), reply_markup=start_kb)


@router.callback_query(F.data == "startplay", flags=flags)
async def start_play_cmd(c: CQ, ssn, bot: Bot):

    sub = await bot.get_chat_member(channel_username, c.from_user.id)

    await c.message.delete()

    if sub.status == "left":
        txt = "Чтобы начать играть, необходимо 1️⃣ Подписаться на канал @offsidecard"
        await c.message.answer(txt, reply_markup=sub_kb)

    else:
        user = await get_user_info(ssn, c.from_user.id)
        txt = f"""
        Твои достижения:

        🃏 Собранное количество карточек: {user.card_quants}
        🏆 Рейтинг собранных карточек: {user.rating}

        ⚽️ Рейтинг в игре Пенальти: {user.penalty_rating}
        """
        await c.message.answer(dedent(txt), reply_markup=main_kb)


@router.callback_query(F.data == "cancel_cb")
async def cancel_cb_cmd(c: CQ, state: FSM):
    await state.clear()
    await c.answer("✅ Действие отменено")
    await c.message.delete()


@router.callback_query(F.data == "closewindow")
async def close_window_cmd(c: CQ):
    await c.message.delete()
