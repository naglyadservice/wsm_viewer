FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Определение переменных окружения
ENV FLASK_APP=app.py
ENV FLASK_PORT=5000
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 5000

# Запуск приложения
CMD ["python", "app.py"]