FROM python:3.10-slim

# 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    fonts-liberation \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libnss3 libxss1 libxcomposite1 libxrandr2 \
    libgbm1 libxdamage1 libxshmfence1 libxkbcommon0 \
    libpangocairo-1.0-0 libpango-1.0-0 \
    libgtk-3-0 libgdk-pixbuf2.0-0 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ▒ Chrome 설치 ▒
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# ▒ ChromeDriver 설치 (Chrome 버전에 자동 맞게) ▒
RUN CHROME_VERSION=$(google-chrome --version | sed 's/[^0-9.]//g') && \
    DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%.*}") && \
    wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver_linux64.zip

ENV CHROME_BIN="/usr/bin/google-chrome"
ENV CHROMEDRIVER_PATH="/usr/bin/chromedriver"

# Python 작업 디렉토리
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# FastAPI 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
