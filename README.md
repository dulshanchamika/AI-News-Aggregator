# 🤖 AI News Aggregator

An automated, end-to-end pipeline that replaces generic newsletters with a strictly tailored daily digest. It scrapes high-signal sources (YouTube, OpenAI, Anthropic), uses LLM-powered agents to curate content against your personal interest profile, and delivers a modern HTML report directly to your inbox.

## 🚀 Features

-   **Multi-Source Scraping**: Monitor RSS feeds and YouTube channels (automatically fetching full transcripts).
-   **Intelligent Curation**: A **Gemini-powered Curator Agent** ranks articles based on your specific technical background and interests.
-   **Personalized Summaries**: Each article includes a custom "Why this matters for you" insight block.
-   **Modern Email Delivery**: Delivers a mobile-responsive, card-based HTML digest via SMTP.
-   **Anti-Blocking**: Integrated with **Webshare proxies** to bypass YouTube transcript rate limits and IP blocking.
-   **Production Ready**: Dockerized and ready for deployment on **Render** with PostgreSQL.

## 🛠️ Tech Stack

-   **Language**: Python 3.12+
-   **Environment**: `uv` for lightning-fast dependency management.
-   **Database**: PostgreSQL with SQLAlchemy ORM.
-   **AI**: Google Gemini API (1.5 Flash / 2.0 Flash Lite).
-   **Infrastructure**: Docker, Render (Managed Postgres + Cron).

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ai-news-aggregator.git
cd ai-news-aggregator
```

### 2. Install Dependencies
Using `uv`:
```bash
uv sync
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
MY_EMAIL=your_email@gmail.com
APP_PASSWORD=your_gmail_app_password
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_news_aggregator
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Optional: YouTube Proxy (Webshare)
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
```

### 4. Run the Pipeline
```bash
uv run main.py
```

## 🏗️ Architecture

1.  **Scrapers**: Procedural scripts evolved into OO-based scraper classes for YouTube and RSS feeds.
2.  **Processors**: Clean raw data (Markdown conversion, transcript cleaning).
3.  **Agents**:
    -   **CuratorAgent**: Ranks content using listwise comparison batches to ensure only the highest signal news reaches you.
    -   **EmailAgent**: Generates personalized technical overviews and greetings.
4.  **Service Layer**: Handles SMTP dispatch and database operations.

## ☁️ Deployment

This project is configured for **Render**:
1.  Connect your GitHub repository to Render.
2.  Add a **PostgreSQL** database service.
3.  Add a **Cron Job** service:
    -   **Environment**: Docker
    -   **Schedule**: `0 9 * * *` (Daily at 9 AM)
    -   **Command**: `python main.py`
4.  Add your environment variables to the Render Dashboard.

## 📄 License
MIT