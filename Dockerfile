FROM denoland/deno:bin-2.9.8 AS deno

FROM python:3.11-slim

COPY --from=deno /deno /usr/local/bin/deno

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN deno --version

COPY . .

ENV WORK_DIR=/app/downloads
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/downloads /app/public

CMD ["python", "bot.py"]
