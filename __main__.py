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
from handlers import admin, info, start
from handlers.card import buy_cards, get_card, my_cards
from handlers.games import lucky_shot
from handlers.trade import confirm_trade, owner_trade, target_trade
from middlewares.db import DbSessionMiddleware
from middlewares.throttling import (ThrottlingCallbackQueryMiddleware,
                                    ThrottlingMessageMiddleware)


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

    # sheduler = AsyncIOScheduler()
    # sheduler.add_job(send_one_day_off, "cron", month="11", day="27",
    #                  hour="20", minute="29", second="0", args=(bot, sessionmaker))
    # sheduler.start()

    # Регистрация роутеров с хэндлерами
    dp.include_router(start.router)
    dp.include_router(info.router)

    dp.include_router(lucky_shot.router)

    dp.include_router(get_card.router)
    dp.include_router(buy_cards.router)
    dp.include_router(my_cards.router)

    dp.include_router(owner_trade.router)
    dp.include_router(target_trade.router)
    dp.include_router(confirm_trade.router)

    dp.include_router(admin.router)

    # Регистрация мидлварей
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    dp.message.middleware(ThrottlingMessageMiddleware())
    dp.callback_query.middleware(ThrottlingCallbackQueryMiddleware())

    await set_bot_commands(bot)

    action_queue = TTLCache(maxsize=10000, ttl=60)

    logging.getLogger('aiogram.event').setLevel(logging.WARNING)
    logging.getLogger('apscheduler.executors.default').setLevel(
        logging.WARNING)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot, db=sessionmaker, yoo_token=config.yoo_token.get_secret_value(),
            allowed_updates=dp.resolve_used_update_types(),
            action_queue=action_queue)
    finally:
        await dp.storage.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
