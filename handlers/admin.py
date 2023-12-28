import asyncio
import logging

from aiogram import Bot, F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from filters.filters import IsAdmin
from keyboards.main_kbs import cancel_btn
from utils.states import AdminStates

flags = {"throttling_key": "default"}
router = Router()
