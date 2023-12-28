from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    mycards = State()


class AdminStates(StatesGroup):
    reason = State()
    img = State()
