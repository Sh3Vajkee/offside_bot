import asyncio
import datetime as dt
import logging
from logging.handlers import TimedRotatingFileHandler

from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cachetools import TTLCache
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config_reader import config
from db.base import Base
from handlers import info, ratings, start
from handlers.admin import add_card, add_promo, admin_main, edit_cards
from handlers.card import buy_cards, get_card, my_cards
from handlers.games import (craft, duel_create, duel_main, duel_owner,
                            duel_target, lucky_shot, penalty,
                            penalty_card_owner, penalty_card_target)
from handlers.payments import cards_buy, ls_buy
from handlers.trade import confirm_trade, owner_trade, target_trade
from middlewares.db import DbSessionMiddleware
from middlewares.throttling import (ThrottlingCallbackQueryMiddleware,
                                    ThrottlingMessageMiddleware)
from utils.duel_misc import re_check_active_duels
from utils.scheduled import new_day, re_check_active_penalties


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Перезапустить бота"),
    ]

    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())


async def main():
    date = dt.datetime.now()

    # Логгирование
    logging.basicConfig(
        # handlers=[TimedRotatingFileHandler(
        #     f"logs/offside-{date.day}-{date.month}-{date.year}-{date.hour}-{date.minute}.log", when="d", interval=1)],
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S"
    )

    engine = create_async_engine(
        url=config.db_url.unicode_string(), echo=False,
        pool_size=500, max_overflow=500, pool_timeout=5)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher()

    dp.message.filter(F.chat.type == "private")
    dp.callback_query.filter(F.message.chat.type == "private")

    sheduler = AsyncIOScheduler()
    sheduler.add_job(new_day, "cron", hour="0", minute="0",
                     second="10", args=(sessionmaker, ))
    sheduler.start()

    # Регистрация роутеров с хэндлерами
    dp.include_router(start.router)
    dp.include_router(info.router)
    dp.include_router(ratings.router)

    dp.include_router(lucky_shot.router)
    dp.include_router(penalty.router)
    dp.include_router(penalty_card_owner.router)
    dp.include_router(penalty_card_target.router)
    dp.include_router(craft.router)

    dp.include_router(duel_main.router)
    dp.include_router(duel_create.router)
    dp.include_router(duel_owner.router)
    dp.include_router(duel_target.router)

    dp.include_router(get_card.router)
    dp.include_router(buy_cards.router)
    dp.include_router(my_cards.router)

    dp.include_router(owner_trade.router)
    dp.include_router(target_trade.router)
    dp.include_router(confirm_trade.router)

    dp.include_router(admin_main.router)
    dp.include_router(add_card.router)
    dp.include_router(edit_cards.router)
    dp.include_router(add_promo.router)

    dp.include_router(ls_buy.router)
    dp.include_router(cards_buy.router)

    # Регистрация мидлварей
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    dp.message.middleware(ThrottlingMessageMiddleware())
    dp.callback_query.middleware(ThrottlingCallbackQueryMiddleware())

    action_queue = TTLCache(maxsize=10000, ttl=60)

    logging.getLogger('aiogram.event').setLevel(logging.WARNING)
    logging.getLogger('apscheduler.executors.default').setLevel(
        logging.WARNING)
    try:
        await re_check_active_penalties(sessionmaker, bot)
        await re_check_active_duels(sessionmaker, bot)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot, db=sessionmaker, yoo_token=config.yoo_token.get_secret_value(),
            allowed_updates=dp.resolve_used_update_types(),
            wallet=config.wallet, action_queue=action_queue)
    finally:
        await dp.storage.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
