import logging
import random
import sqlite3
from collections import Counter
from enum import Enum

from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, executor, types

# Configure logging
logging.basicConfig(level=logging.INFO)

API_TOKEN = "5291360227:AAE3n7EbsTdlRZpSE2qlY1BvxYwDxaopZ6I"

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

word = ""
initial_tries = 6
tries = initial_tries
guess = ""
guesses = []
dicty = {}


class Hint(Enum):
    ABSENT = 0
    PRESENT = 1
    CORRECT = 2


keyboard = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

chats = {}


def tip(secret_word, guessed_word):
    pool = Counter(s for s, g in zip(secret_word, guessed_word) if s != g)
    hint = []

    for s, g in zip(secret_word, guessed_word):
        if s == g:
            hint.append(Hint.CORRECT)
        elif g in word and pool[g] > 0:
            hint.append(Hint.PRESENT)
            pool[g] -= 1
        else:
            hint.append(Hint.ABSENT)

    return hint


#
# def draw_grid(img):
#     draw = ImageDraw.Draw(img)
#     x0, y0 = 60, 65
#     x1, y1 = 250, 65
#     while y0 != 120:
#         draw.line((x0, y0, x1, y1), fill=128)
#         y0 += 15
#         y1 += 15
#     return img


# the picture of guess history and the keyboard
def send_picture(guesses_text, keyboard_text):
    global word

    img = Image.new('RGB', (500, 300), color=(31, 48, 78))

    draw = ImageDraw.Draw(img)
    font_keyboard = ImageFont.truetype('RubikMonoOne-Regular.ttf', size=20)
    font_grid = ImageFont.truetype('Jetbrainsmonobold.ttf', size=30)
    # draw_grid(img)

    x0, y0 = 60, 65
    x1, y1 = 200, 65
    counter = 0
    while counter != 6:
        draw.line((x0, y0, x1, y1), fill='white', width=3)
        y0 += 35
        y1 += 35
        counter += 1

    grid_width = 60
    grid_height = 65
    ad_pix_grid = 30
    for item in guesses_text:
        # draw.text((grid_width, grid_height - 15), delimiter, font=font_grid)
        hint = tip(word, item)
        for i, h in enumerate(hint):
            letter = item[i]
            if letter in dicty:
                if h == Hint.CORRECT:
                    draw.text((grid_width, grid_height), letter.upper(), fill="green", font=font_grid)
                    grid_width += ad_pix_grid
                elif h == Hint.PRESENT:
                    draw.text((grid_width, grid_height), letter.upper(), fill="yellow", font=font_grid)
                    grid_width += ad_pix_grid
                else:
                    draw.text((grid_width, grid_height), letter.upper(), fill="red", font=font_grid)
                    grid_width += ad_pix_grid
            else:
                draw.text((grid_width, grid_height), letter.upper(), font=font_grid)
        grid_height += 35
        grid_width = 60
        # draw.text((grid_width, grid_height - 15), delimiter, font=font_grid)

    width = 250
    height = 100
    additional_pixels = 20
    for i in keyboard_text:
        if width < 470:
            pass
        else:
            width = 250
            height += 25
        if i in dicty:
            if dicty[i] == Hint.CORRECT:
                draw.text((width, height), i.upper(), fill="green", font=font_keyboard)
                width += additional_pixels
            elif dicty[i] == Hint.PRESENT:
                draw.text((width, height), i.upper(), fill="yellow", font=font_keyboard)
                width += additional_pixels
            else:
                draw.text((width, height), i.upper(), fill=(31, 48, 78,), font=font_keyboard)
                width += additional_pixels
        else:
            draw.text((width, height), i.upper(), font=font_keyboard)
            width += additional_pixels

    img.save('result.png')
    return img


def start_game():
    global word, dictionary, tries, guesses, dicty
    tries = initial_tries
    word = random.choice(dictionary)
    # word = "мужик"
    guesses = []
    dicty = {}
    return "Я загадал слово"


# Declension of the word => попытка(ок)
def declension(a):
    if a == 5:
        return "попыток"
    elif a in range(2, 5):
        return "попытки"
    else:
        return "попытка"


# bot gets and returns the definition/meaning of the word from wikipedia
def word_definition(word_def):
    with sqlite3.connect('dict.db') as con:
        definitions = con.execute("select Article from Dict where Word=:word", {"word": word_def}).fetchone()
        if definitions is None:
            return ""
        else:
            return "\n".join(definitions[0].split("<br>")[1:])


@dp.message_handler(commands=['Начало'])
async def send_start(message: types.Message):
    await message.reply(start_game())


@dp.message_handler(commands=['сдаюсь'])
async def send_start(message: types.Message):
    await bot.send_message(message.chat.id,
                           f"Вы проиграли, слово было такое: *{word.upper()}*\n_{word_definition(word)}_",
                           parse_mode="Markdown")
    await message.reply(start_game())


@dp.message_handler(commands=['У'])
async def send_guess(message: types.Message):
    global word, tries, dictionary, guess, dicty
    guess = message.get_args().lower()
    if guess == word:
        guess_with_spaces = ""
        for i in guess:
            guess_with_spaces += i + "__"
        await message.reply(f"🟩  🟩  🟩  🟩  🟩  \n{guess_with_spaces[:-2]}\nПИПЕЦ ТЫ МОЛОДЕЦ{word_definition(word)}")
        await message.reply(start_game())
    elif tries == 1:
        # await message.reply(f"Вы проиграли, слово было такое: {word}{word_definition(word)}")
        await bot.send_message(message.chat.id, f"Вы проиграли, слово было такое:"
                                                f" *{word.upper()}*_{word_definition(word)}_", parse_mode="Markdown")
        await message.reply(start_game())
    elif guess not in dictionary:
        await message.reply("Такого слова нет в пяти-буквенном словаре")
    else:
        colorful_hint = ""
        green = "🟩  "
        yellow = "🟨  "
        red = "🟥  "

        hint = tip(word, guess)
        for i, h in enumerate(hint):
            g = guess[i]
            if h == Hint.CORRECT:
                colorful_hint += green
                dicty[g] = h
            elif h == Hint.PRESENT:
                colorful_hint += yellow
                if g not in dicty.keys() or dicty[g] != Hint.CORRECT:
                    dicty[g] = h
            else:
                colorful_hint += red
                dicty[g] = Hint.ABSENT

        guesses.append(guess)
        tries -= 1
        await message.reply(f"{colorful_hint}\nосталось {str(tries)} {declension(tries)}")

        send_picture(guesses, keyboard)
        with open('result.png', "rb") as photo:
            await bot.send_photo(message.chat.id, photo)


if __name__ == '__main__':
    with open("five_letter_nouns.txt", "r", encoding="utf-8") as fr:
        dictionary = fr.read().splitlines()
    start_game()
    executor.start_polling(dp, skip_updates=True)
