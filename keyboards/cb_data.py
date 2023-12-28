from aiogram.filters.callback_data import CallbackData


class PageCB(CallbackData, prefix="page"):
    num: int
    last: int
