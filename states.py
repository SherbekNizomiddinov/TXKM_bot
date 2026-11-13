from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    phone = State()
    inn = State()
    fiscal = State()