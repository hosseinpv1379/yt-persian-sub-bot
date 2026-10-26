FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        fontconfig \
        wget \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/share/fonts/truetype/vazirmatn \
    && wget -q -O /usr/share/fonts/truetype/vazirmatn/Vazirmatn-Regular.ttf \
        https://cdn.jsdelivr.net/npm/vazirmatn/fonts/ttf/Vazirmatn-Regular.ttf \
    && wget -q -O /usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf \
        https://cdn.jsdelivr.net/npm/vazirmatn/fonts/ttf/Vazirmatn-Bold.ttf \
    && fc-cache -f

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV WORK_DIR=/app/downloads
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/downloads /app/public

CMD ["python", "bot.py"]
