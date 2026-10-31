# OLX Price Watcher

A Python-based OLX listings parser with a Telegram bot and SQLite database.

## Features

- Scrapes OLX listings using Playwright and BeautifulSoup
- Extracts listing titles, prices and URLs
- Stores listing data in SQLite
- Provides access to collected listings through a Telegram bot
- Uses Docker Compose to run the bot and parser
- Persists database data using Docker volumes

## Tech Stack

- **Python** — application logic
- **aiogram** — Telegram bot
- **Playwright** — browser automation
- **BeautifulSoup** — HTML parsing
- **SQLite** — database
- **Docker & Docker Compose** — containerization

## Project Structure

```text
olx-price-watcher/
├── bot.py
├── main.py
├── database.py
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
└── .dockerignore
```

## Installation

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd olx-price-watcher
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Add your Telegram bot token to `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
```

### 3. Create storage directory

```bash
mkdir -p storage
```

### 4. Build Docker image

```bash
docker compose build
```

### 5. Run the parser

```bash
docker compose --profile parser run --rm parser
```

### 6. Start the Telegram bot

```bash
docker compose up -d bot
```

## Useful Commands

View bot logs:

```bash
docker compose logs -f bot
```

Stop the bot:

```bash
docker compose stop bot
```

Restart the bot:

```bash
docker compose restart bot
```

Rebuild and restart:

```bash
docker compose up -d --build bot
```

## Database

SQLite database is stored in the `storage/` directory and persisted through a Docker volume mapping.

## Disclaimer

This project is intended for educational purposes. Use responsibly and respect OLX terms of service and applicable website access policies.

## Author

Developed as a personal Python and DevOps learning project.