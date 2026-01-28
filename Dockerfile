FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Token'ı hardcoded koymuyoruz, docker run -e BOT_TOKEN=... ile geçiyoruz
# EXPOSE gerek yok çünkü polling kullanıyoruz, webhook yok

CMD ["python", "main.py"]
