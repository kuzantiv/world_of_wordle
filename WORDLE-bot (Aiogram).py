import logging
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

# CHAT_ID = -1001741490206  # ПИЗДЮШНЯ
CHAT_ID = -614450004  # ТЕСТ ЧАТ
word = ""
initial_tries = 6
tries = initial_tries
guess = ""
hint = []
guesses = []


class Hint(Enum):
    ABSENT = 0
    PRESENT = 1
    CORRECT = 2


keyboard = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

dicty = {}


def draw_grid(secret_word, guessed_words):
    global initial_tries
    new_line = '\n'
    delimiter = "-----" * len(secret_word)
    delimiter = delimiter[:-3]
    grid = f"{delimiter}{new_line}"
    for i in range(initial_tries):
        row = "|"
        # w = ""
        if i >= len(guessed_words):
            w = " " * 5
        else:
            w = guessed_words[i]

        for c in w:
            row += f" {c.upper()} |"
        grid += f"{row}{new_line}{delimiter}{new_line}"
    return grid


def tip(secret_word, guessed_word):
    global hint
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


# the picture of guess history and the keyboard

def send_picture(guesses_text, keyboard_text):
    img = Image.new('RGBA', (600, 400), 'black')
    idraw = ImageDraw.Draw(img)
    headline = ImageFont.truetype('arial.ttf', size=20)
    idraw.text((50, 50), guesses_text, font=headline)

    # delimiter = ""

    width = 300
    height = 130
    for i in keyboard_text:
        if width < 470:
            pass
        else:
            width = 300
            height += 25
        if i in dicty:
            if dicty[i] == 2:
                idraw.text((width, height), i.upper(), fill="green", font=headline)
                width += 20
            elif dicty[i] == 1:
                idraw.text((width, height), i.upper(), fill="yellow", font=headline)
                width += 20
            else:
                idraw.text((width, height), i.upper(), fill="red", font=headline)
                width += 20
        else:
            idraw.text((width, height), i.upper(), font=headline)
            width += 20

    img.save('canvas.png')
    return img


def start_game():
    global word, dictionary, tries, guesses
    tries = initial_tries
    # word = random.choice(dictionary)
    word = "нитка"
    guesses = []
    return "Я загадал слово"


# Declension of the word => попытка(ок)
def declension(a):
    if a == 5:
        return "попыток"
    elif a in range(2, 5):
        return "попытки"
    else:
        return "попытка"


# bot gets and returns the defeniton/meaning of the word from wikipedia
def word_definition(word_def):
    new_line = "\n"
    wikipedia.set_lang("ru")
    return f"{new_line}{wikipedia.summary(word_def, sentences=5)}"


@dp.message_handler(commands=['Начало'])
async def send_start(message: types.Message):
    await message.reply(start_game())


@dp.message_handler(commands=['сдаюсь'])
async def send_start(message: types.Message):
    await bot.send_message(CHAT_ID, f"Вы проебали, слово было такое: *{word.upper()}*_{word_definition(word)}_",
                           parse_mode="Markdown")
    await message.reply(start_game())


@dp.message_handler(commands=['У'])
async def send_guess(message: types.Message):
    global word, tries, dictionary, guess
    guess = message.get_args().lower()
    if guess == word:
        guess_with_spaces = ""
        for i in guess:
            guess_with_spaces += i + "__"
        await message.reply(f"🟩  🟩  🟩  🟩  🟩  \n{guess_with_spaces[:-2]}\nПИЗДЕЦ ТЫ МОЛОДЕЦ{word_definition(word)}")
        await message.reply(start_game())
    elif tries == 1:
        # await message.reply(f"Вы проебали, слово было такое: {word}{word_definition(word)}")
        await bot.send_message(CHAT_ID, f"Вы проебали, слово было такое: *{word.upper()}*_{word_definition(word)}_",
                               parse_mode="Markdown")
        await message.reply(start_game())
    elif guess not in dictionary:
        await message.reply("Такого слова нет в пяти-буквенном словаре")
    else:
        colorful_hint = ""
        green = "🟩  "
        yellow = "🟨  "
        red = "🟥  "

        pool = Counter(s for s, g in zip(word, guess) if s != g)

        for s, g in zip(word, guess):
            if s == g:
                colorful_hint += green
                dicty[g] = 2
            elif g in word and pool[g] > 0:
                colorful_hint += yellow
                dicty[g] = 1
                pool[g] -= 1
            else:
                colorful_hint += red
                dicty[g] = 0
        print(dicty)

        guesses.append(guess)
        tries -= 1
        await message.reply(f"{colorful_hint}\nосталось {str(tries)} {declension(tries)}")

        send_picture(draw_grid(guess, guesses), keyboard)
        with open('canvas.png', "rb") as photo:
            await bot.send_photo(chat_id=message.chat.id, photo=photo)


if __name__ == '__main__':
    with open("five_letter_nouns.txt", "r", encoding="utf-8") as fr:
        dictionary = fr.read().splitlines()
    start_game()
    executor.start_polling(dp, skip_updates=True)

"""
1. склонение слова 'ПОПЫТОК'              ✅✅✅
2. алгоритм 2 букв                        ✅✅✅
(сначала помечать зеленые , потом желтые) 
3. клавиатура 
4. подсказки в виде вариантов
5. 
"""
