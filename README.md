# Discord Trading Scraper

Automated Discord message scraper that monitors Discord channels for trading signals and sends webhooks to the webhook handler service.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Discord tokens:

```bash
cp .env.example .env
```

Edit `.env` and add your Discord tokens, channel IDs, and webhook URL.

3. Run the scraper:

```bash
python main.py
```

## Configuration

* Discord tokens are read from `.env` file or environment variables
* Webhook URL points to the webhook handler service
* Trading configuration (ticker symbols, quantities) are in `config.py`

## Features

* Monitors Discord channels every 5 seconds
* Parses trading messages (ES orders, Long Triggered, Target Hit, Stop Loss, Trim, Stopped)
* Sends webhooks to the webhook handler service for order execution
* Tracks positions locally using JSON files
* Handles duplicate message detection

## Project Structure

* `main.py` - Application entry point with Discord scraping loop and handler functions
* `config.py` - Centralized configuration (Discord tokens, patterns, webhook URL)
* `discord_scraper.py` - Discord API interaction
* `message_parser.py` - Message parsing and pattern matching
* `order_executor.py` - Webhook sending to webhook handler service
* `position_tracker.py` - Position and order tracking

## About

Discord scraper that monitors Discord channels for trading signals and forwards them to the webhook handler service via HTTP webhooks.
