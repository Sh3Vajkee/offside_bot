from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    mycards = State()
    owner_trade = State()
    target_trade = State()
    target_penalty = State()
    pack_cards = State()
    promo_text = State()


class AdminStates(StatesGroup):
    add_card = State()
    card_image = State()

    image_id = State()

    view_cards = State()
    new_image = State()
    new_text = State()

    promo_text = State()
    promo_card = State()

    user_info = State()
