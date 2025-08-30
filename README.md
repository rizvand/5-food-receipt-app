# Food Receipt Application

Platform with UI, for

- Upload food online receipt
- Extract with computer vision
- Get the insight on the receipt, and store it to DB.
- Design and implement the AI tools to make sure whenever user asking,
  - “What food did i buy yesterday”
  - “Give me total expenses for food on 20 June”
  - “Where did i buy hamburger from last 7 day”
    The LLM can answer it.
- Wrap the application into a container image using docker, and run it in local.
- CI/CD to wrap the application into the container. You can use github-actions or gitlab-ci.

## Quick Start

Build and run the application using Docker Compose:

```bash
docker-compose up --build
```

## Available Applications

The application consists of **4 services**:

- **OCR & LLM Backend** - http://localhost:8000 - FastAPI backend for OCR & LLM
- **Streamlit Frontend** - http://localhost:8501 - Web interface for uploading receipts
- **PostgreSQL Database** - Port 5432 (internal) - Database for storing receipt data
- **pgAdmin** - http://localhost:5050 - Database management interface

## Database Access

- **pgAdmin Login**:
  - Email: `admin@admin.com`
  - Password: `admin`
- **Database Connection**:
  - Host: `db`
  - Username: `postgres`
  - Password: `example`
  - Database: `postgres`

## Environment Setup

Make sure you have a `.env` file in the root directory with required environment variables before running the application.
