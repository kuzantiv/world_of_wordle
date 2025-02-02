from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

inline_btn_1 = InlineKeyboardButton(text='Подсказка', callback_data='button1')
inline_kb1 = InlineKeyboardMarkup(inline_keyboard=[[inline_btn_1]])
