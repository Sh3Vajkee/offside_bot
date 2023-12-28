import datetime
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from cachetools import TTLCache


class DateMessageMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ):
        date_ts = int(datetime.datetime.now().timestamp())
        if date_ts < 1702112400:
            txt = "Moscow Unicorn Race стартует 9 декабря в 12:00. Мы напомним тебе о старте!"
            await event.answer(txt)
            return
        elif date_ts >= 1702137600:
            txt = "Событие Moscow Unicorn Race уже завершилось"
            await event.answer(txt)
            return
        return await handler(event, data)


class DateCallbackQueryMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any],
    ):
        date_ts = int(datetime.datetime.now().timestamp())
        if date_ts < 1702112400:
            txt = "Moscow Unicorn Race стартует 9 декабря в 12:00. Мы напомним тебе о старте!"
            await event.answer(txt, show_alert=True)
            return
        elif date_ts >= 1702137600:
            txt = "Событие Moscow Unicorn Race уже завершилось"
            await event.answer(txt, show_alert=True)
            return
        return await handler(event, data)
