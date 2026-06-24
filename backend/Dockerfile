FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by Chromium
RUN apt-get update && apt-get install -y \
    wget curl gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium and its deps via Playwright
RUN playwright install --with-deps chromium

COPY . .

RUN mkdir -p sessions

EXPOSE 8096

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8096"]
