# SnipURL - Modern Fast URL Shortener

A lightweight, modern, self-hosted URL shortener built with FastAPI, SQLite, and Tailwind CSS. Features custom aliases, link expiration, click tracking, detailed analytics, QR code generation, and a RESTful API.

## Features

- **Clean UI**: Responsive dashboard built with Tailwind CSS and Alpine.js.
- **Custom Aliases**: Choose personalized vanity slugs or let the system generate secure Base62 codes.
- **Link Expiration**: Set optional link expiration (1 hour, 24 hours, 7 days, 30 days).
- **Detailed Analytics**: Track total clicks, referrers, user agents, and recent access activity.
- **QR Code Support**: Instant client-side QR code generation for shortened links.
- **REST API**: Programmatic URL shortening and stats endpoints.
- **Zero External Heavy DB**: Backed by Python's built-in `sqlite3` with WAL mode enabled.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Running Tests

```bash
pytest
```

## API Endpoints

- `POST /api/shorten`: JSON payload `{"url": "https://example.com", "custom_code": "custom", "expires_in_hours": 24}`
- `GET /api/links/{code}`: Fetch metadata and analytics for a short link.
- `GET /{code}`: Redirect to target long URL.
