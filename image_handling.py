import numpy as np
import shutil
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot


def draw_winner_name(chat_id, user_full_name, user_id):
    img = Image.open("last_winners/winner_backgraund_tamplate.jpg")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("fonts/Jetbrainsmonobold.ttf", 350)
    first_name = user_full_name.split()[0]
    last_name = user_full_name.split()[1]

    draw.text((2500, 2000), first_name, (255, 255, 255), font=font)
    draw.text((2500, 2500), last_name, (255, 255, 255), font=font)

    photo_name = f'last_winner_pic_chat{chat_id}user{user_id}.jpg'
    img.save(f'last_winners/{photo_name}')

    return photo_name


async def download_avatar(bot: Bot, chat_id, user_id):
    path_to_avatar = f'users_logos/{user_id}.png'
    try:
        a = await bot.get_user_profile_photos(user_id)
        photo = a.photos[0][1].file_id
        await bot.download_file_by_id(photo, path_to_avatar)

    except Exception as e:
        print(f'Ошибка при получении аватара \n{e}')
        # await bot.send_message(chat_id,
        #                        '❌ Произошла ошибка при получении аватара пользователя!\n'
        #                        'Возможно это случилось из-за настроек приватности пользователя.\n'
        #                        'Либо в профиле выбранного пользователя отсутствуют фотографии.')

        # await asyncio.sleep(5)
        # await er.delete()
        shutil.copyfile(src=f'users_logos/anonymous.png', dst=path_to_avatar)

    return path_to_avatar


def resize_picture(path_to_pic):
    image = Image.open(path_to_pic)
    image.thumbnail((30, 30))
    image.save(path_to_pic)


def insert_users_logo(background_for_logo, chat_id, players):
    x = 20
    position = {1: (x, 67),
                2: (x, 103),
                3: (x, 139),
                4: (x, 175),
                5: (x, 211),
                }

    image = Image.open(background_for_logo)
    for i, player in enumerate(players, 1):
        path_to_logo = f'users_logos/{player}.png'
        logo = Image.open(path_to_logo)
        image.paste(logo, position[i], logo)
    image.save(f'result{chat_id}.png')


def crop_circle_from_avatar(src, dst):
    # Open the input image as numpy array, convert to RGB
    img = Image.open(src).convert("RGB")
    np_image = np.array(img)
    h, w = img.size

    # Create same size alpha layer with circle
    # alpha = Image.new('L', img.size, 0)
    alpha = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(alpha)
    draw.pieslice([0, 0, h, w], 0, 360, fill=255)

    # Convert alpha Image to numpy array
    np_alpha = np.array(alpha)

    # Add alpha layer to RGB
    np_image = np.dstack((np_image, np_alpha))

    # Save with alpha
    Image.fromarray(np_image).save(dst)
