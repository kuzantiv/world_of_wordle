import logging
import random
from collections import Counter
from enum import Enum

import wikipedia as wikipedia
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, executor, types

import config

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

word = ""
initial_tries = 6
tries = initial_tries
guess = ""
guesses = []
dicty = {}
# CHAT_ID = -1001741490206  # ПИЗДЮШНЯ


class Hint(Enum):
    ABSENT = 0
    PRESENT = 1
    CORRECT = 2


keyboard = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"


chats = {}

# def draw_grid(secret_word, guessed_words):
#     global initial_tries
#     new_line = '\n'
#     delimiter = "-----" * len(secret_word)
#     delimiter = delimiter[:-3]
#     grid = f"{delimiter}{new_line}"
#     for i in range(initial_tries):
#         row = "|"
#         # w = ""
#         if i >= len(guessed_words):
#             w = " " * 5
#         else:
#             w = guessed_words[i]
#
#         for c in w:
#             row += f" {c.upper()} |"
#         grid += f"{row}{new_line}{delimiter}{new_line}"
#     return grid


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


# the picture of guess history and the keyboard

def send_picture(guesses_text, keyboard_text):
    global word

    img = Image.new('RGBA', (500, 300), 'black')
    idraw = ImageDraw.Draw(img)
    font_keyboard = ImageFont.truetype('RubikMonoOne-Regular.ttf', size=20)
    font_grid = ImageFont.truetype('cour.ttf', size=30)
    delimiter = "--------"

    grid_height = 65
    grid_width = 60
    ad_pix_grid = 30
    for item in guesses_text:
        idraw.text((grid_width, grid_height - 15), delimiter, font=font_grid)
        hint = tip(word, item)
        for i, h in enumerate(hint):
            letter = item[i]
            if letter in dicty:
                if h == Hint.CORRECT:
                    idraw.text((grid_width, grid_height), letter.upper(), fill="green", font=font_grid)
                    grid_width += ad_pix_grid
                elif h == Hint.PRESENT:
                    idraw.text((grid_width, grid_height), letter.upper(), fill="yellow", font=font_grid)
                    grid_width += ad_pix_grid
                else:
                    idraw.text((grid_width, grid_height), letter.upper(), fill="red", font=font_grid)
                    grid_width += ad_pix_grid
            else:
                idraw.text((grid_width, grid_height), letter.upper(), font=font_grid)
        grid_height += 35
        grid_width = 60
        idraw.text((grid_width, grid_height - 15), delimiter, font=font_grid)

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
                idraw.text((width, height), i.upper(), fill="green", font=font_keyboard)
                width += additional_pixels
            elif dicty[i] == Hint.PRESENT:
                idraw.text((width, height), i.upper(), fill="yellow", font=font_keyboard)
                width += additional_pixels
            else:
                idraw.text((width, height), i.upper(), fill="black", font=font_keyboard)
                width += additional_pixels
        else:
            idraw.text((width, height), i.upper(), font=font_keyboard)
            width += additional_pixels

    img.save('canvas.png')
    return img


def start_game():
    global word, dictionary, tries, guesses, dicty
    tries = initial_tries
    word = random.choice(dictionary)
    # word = "нитка"
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


# ERROR:asyncio:Task exception was never retrieved

# bot gets and returns the defeniton/meaning of the word from wikipedia
def word_definition(word_def):
    new_line = "\n"
    wikipedia.set_lang("ru")
    definition = wikipedia.summary(word_def, sentences=1)
    try:
        definition
    except wikipedia.DisambiguationError as e:
        s = random.choice(e.options)
        definition = wikipedia.page(s)
    return f"{new_line}{definition}"


@dp.message_handler(commands=['Начало'])
async def send_start(message: types.Message):
    await message.reply(start_game())


@dp.message_handler(commands=['сдаюсь'])
async def send_start(message: types.Message):
    await bot.send_message(message.chat.id, f"Вы проебали, слово было такое: *{word.upper()}*_{word_definition(word)}_",
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
        # await message.reply(f"Вы проебали, слово было такое: {word}{word_definition(word)}")
        await bot.send_message(message.chat.id, f"Вы проебали, слово было такое:"
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
        with open('canvas.png', "rb") as photo:
            await bot.send_photo(message.chat.id, photo)


if __name__ == '__main__':
    with open("five_letter_nouns.txt", "r", encoding="utf-8") as fr:
        dictionary = fr.read().splitlines()
    start_game()
    executor.start_polling(dp, skip_updates=True)
