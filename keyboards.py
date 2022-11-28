# keyboards.py
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

inline_btn_1 = InlineKeyboardButton('Подсказка', callback_data='button1')
inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)
