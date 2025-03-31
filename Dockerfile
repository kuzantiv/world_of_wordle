FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем директорию для хранения аватарок пользователей, если она еще не существует
RUN mkdir -p users_logos
RUN mkdir -p last_winners

# Запускаем бота при старте контейнера
CMD ["python", "bot.py"]
