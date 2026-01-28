FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV BOT_TOKEN=8482282613:AAFLe85oixqy2u4FcXtHnb4dfMbgpzqNh_w

CMD ["python", "main.py"]
