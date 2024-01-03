from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    mycards = State()
    owner_trade = State()
    target_trade = State()
    target_penalty = State()


class AdminStates(StatesGroup):
    reason = State()
    img = State()
