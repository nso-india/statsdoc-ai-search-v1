# MOSPI

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.1-green.svg)](https://www.djangoproject.com/)
[![SvelteKit](https://img.shields.io/badge/sveltekit-2.16-orange.svg)](https://kit.svelte.dev/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](https://docs.docker.com/compose/)

**Document Processing and AI Chat Platform** — A comprehensive platform combining Django backend with SvelteKit frontend, featuring AI-powered document analysis, real-time chat, RAG (Retrieval-Augmented Generation), and natural language SQL generation.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
  - [Tech Stack](#tech-stack)
  - [Services](#services)
  - [Project Structure](#project-structure)
  - [Design Principles](#design-principles)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Deploy](#deploy)
  - [Access the Application](#access-the-application)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [LLM Configuration](#llm-configuration)
- [API Reference](#api-reference)
- [Security](#security)
- [Logs and Monitoring](#logs-and-monitoring)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview

MOSPI is a production-ready document processing and AI chat platform designed for organizations that need to **upload, process, review, and query documents** using AI. It supports multiple LLM backends (Ollama, OpenAI/Azure, Anthropic Claude) and provides:

- **Document ingestion** with OCR and table extraction via Docling
- **Semantic search** over documents using Qdrant vector database
- **RAG-powered chat** for natural language Q&A over your document corpus
- **Natural language to SQL** conversion for querying extracted tabular data
- **AI-assisted document review** with edit, remove, and merge suggestions
- **Real-time WebSocket chat** with multi-language support
- **Role-based access control** with JWT authentication

---

## Features

| Feature | Description |
|---|---|
| **Document Upload & Processing** | Drag-and-drop upload with Docling-powered OCR, table detection, and structured extraction |
| **Knowledge Bases** | Organize documents into collections, index them for vector search via Qdrant |
| **RAG Chat** | Real-time AI chat over your documents using retrieval-augmented generation |
| **SQL Generation** | Natural language to SQL via Vanna — query extracted tables without writing SQL |
| **AI Document Review** | AI suggests edits, removals, and table merges; humans accept or reject |
| **Multi-LLM Support** | Swap between Ollama (local), OpenAI/Azure, and Anthropic Claude |
| **Analytics Dashboard** | Visualize data with Plotly charts and markdown table generation |
| **User Management** | JWT auth, email verification, password reset, account lockout |
| **Real-time Communication** | WebSocket-based chat via Django Channels + Redis |
| **Async Task Processing** | Background document processing with Celery + Redis |
| **GPU Accelerated** | NVIDIA GPU support for Ollama, Docling, and Celery workers |

---

## Architecture

### Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5.1, Django REST Framework, Django Channels, Celery |
| **Frontend** | SvelteKit 2.16, Svelte 5, Tailwind CSS, Bits UI, Plotly.js |
| **Primary Database** | PostgreSQL 14 |
| **Vector Database** | Qdrant (with FastEmbed / BAAI bge-large-en-v1.5) |
| **Cache / Broker** | Redis 7 |
| **Document Processing** | Docling (with OCR and table extraction) |
| **SQL Generation** | Vanna (multi-LLM SQL builder) |
| **LLM Inference** | Ollama (local), OpenAI/Azure, Anthropic Claude |
| **Containerization** | Docker + Docker Compose (GPU-enabled) |
| **Email** | Azure Communication Services SMTP |

### Services

The platform runs as a set of Docker Compose services:

| Service | Port | Description |
|---|---|---|
| `web` | 8000 | Django backend (Daphne ASGI server) |
| `frontend` | 3000 | SvelteKit application |
| `db` | — | PostgreSQL 14 (primary database) |
| `file_data_db` | — | PostgreSQL 14 (extracted file/table data) |
| `qdrant` | 6333, 6334 | Vector database for semantic search |
| `redis` | — | Cache and Celery message broker |
| `celery` | — | Async task worker (document processing, AI ops) |
| `ollama` | 11434 | Local LLM inference server |
| `docling-serve` | 5001 | Document conversion service with OCR |

### Project Structure

```
Mospi--Ps1/
├── config/                  # Django settings & configuration
├── chat/                    # Chat API — messages, WebSocket consumers
├── uploader/                # File upload, processing, AI review
├── user_management/         # Authentication, JWT, user profiles
├── application_settings/    # Dynamic app configuration
├── vanna_adapter/           # Natural language → SQL generation
├── qdrant_adapter/          # Vector DB integration & search
├── ragpipeline.py           # RAG pipeline for external LLMs
├── prompts/                 # AI prompt templates
├── requirements.txt         # Python dependencies
├── Dockerfile               # Backend container
├── docker-compose.yml       # Service orchestration
├── .env.example             # Environment variable template
│
└── frontend/
    ├── src/
    │   ├── routes/
    │   │   ├── (app)/       # Authenticated pages
    │   │   │   ├── chat/    # Chat interface
    │   │   │   ├── knowledge/ # Knowledge base management
    │   │   │   ├── users/   # User management (admin)
    │   │   │   ├── analytics/ # Analytics dashboard
    │   │   │   └── settings/  # App settings
    │   │   ├── login/       # Login page
    │   │   ├── signup/      # Registration page
    │   │   ├── forgot-password/ # Forgot password
    │   │   ├── reset-password/  # Reset password
    │   │   └── verify-email/    # Email verification
    │   └── lib/
    │       ├── components/  # Reusable UI components
    │       ├── apis/        # API integration layer
    │       ├── stores/      # Svelte state management
    │       ├── types/       # TypeScript definitions
    │       ├── services/    # Business logic
    │       └── utils/       # Utilities
    ├── package.json
    └── svelte.config.js
```

### Design Principles

| Principle | Implementation |
|---|---|
| **Multi-LLM Flexibility** | Swap LLM providers via environment variables — no code changes needed |
| **Async-First Processing** | All heavy document processing runs in Celery workers, keeping the API responsive |
| **Semantic Search** | Qdrant vector DB with BAAI bge-large-en-v1.5 embeddings for accurate document retrieval |
| **Human-in-the-Loop** | AI suggests document edits; humans review before changes are applied |
| **Security by Default** | JWT rotation, account lockout, CSRF/XSS protection, input sanitization |
| **GPU-Native** | Docker Compose configured with NVIDIA GPU reservations for LLM and OCR workloads |

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** v2+
- **NVIDIA GPU** with drivers installed (for Ollama, Docling, and Celery GPU workers)
- **NVIDIA Container Toolkit** (`nvidia-docker2`)

### Installation

```bash
# Clone the repository
git clone https://github.com/EduBild-Git/Mospi--Ps1.git
cd Mospi--Ps1

# Copy the environment template and configure it
cp .env.example .env
# Edit .env with your database credentials, API keys, and LLM settings
```

### Deploy

```bash
# Start all services
docker compose up -d

# Pull an Ollama model (e.g., llama3, mistral, etc.)
docker exec -it ollama ollama pull <model_name>

# Verify all services are running
docker compose ps
```

### Access the Application

| Service | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **Admin Panel** | http://localhost:8000/admin |
| **Health Check** | http://localhost:8000/health/ |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |
| **Docling UI** | http://localhost:5001 |
| **Ollama** | http://localhost:11434 |

---

## Configuration

### Environment Variables

Create a `.env` file from the template. Key variables:

| Variable | Description | Default |
|---|---|---|
| `DEBUG` | Django debug mode | `0` |
| `DJANGO_SETTINGS_MODULE` | Settings module path | `config.settings` |
| `POSTGRES_DB` | Database name | `postgres` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | — |
| `DB_HOST` | Database host | `db` |
| `DB_PORT` | Database port | `5432` |
| `DOCLING_URL` | Docling service URL | — |
| `QDRANT_URL` | Qdrant server URL | `http://qdrant:6333` |
| `QDRANT_API_KEY` | Qdrant API key | — |
| `QDRANT_COLLECTION_NAME` | Qdrant collection name | `documents` |
| `QDRANT_QUERY_LIMIT` | Max results per query | `10` |
| `MAX_LLM_RETRIES` | LLM call retry limit | `5` |
| `LLM_PROMPT_FILE` | Path to prompt templates | `prompts` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | — |
| `EMAIL_HOST` | SMTP server host | — |
| `EMAIL_PORT` | SMTP server port | — |
| `EMAIL_USE_TLS` | Enable TLS for email | `1` |
| `EMAIL_HOST_USER` | SMTP username | — |
| `EMAIL_HOST_PASSWORD` | SMTP password | — |
| `DEFAULT_FROM_EMAIL` | Default sender email | — |

> See [.env.example](.env.example) for the full template.

### LLM Configuration

MOSPI supports multiple LLM providers. Configure them independently for different tasks:

**AI Document Comments (e.g., OpenAI/Azure):**

| Variable | Description |
|---|---|
| `AI_COMMENTS_LLM_TYPE` | Provider type (e.g., `openai`, `azure`) |
| `AI_COMMENTS_LLM_API_KEY` | API key |
| `AI_COMMENTS_LLM_API_URL` | API endpoint URL |
| `AI_COMMENTS_LLM_API_VERSION` | API version |
| `AI_COMMENTS_LLM_MODEL_NAME` | Model name |

**SQL Query Generation (e.g., Claude):**

| Variable | Description |
|---|---|
| `SQL_QUERY_LLM_TYPE` | Provider type (e.g., `anthropic`) |
| `SQL_QUERY_LLM_MODEL_NAME` | Model name |

**General / Legacy LLM Settings:**

| Variable | Description |
|---|---|
| `LLM_TYPE` | Provider type (`ollama`, `openai`, `azure`) |
| `LLM_API_KEY` | API key |
| `LLM_API_URL` | API endpoint URL |
| `LLM_API_VERSION` | API version |
| `LLM_NAME` | Model name |
| `LLM_VANNA_MODEL_NAME` | Vanna SQL model name |

---

## API Reference

### Chat

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/chat/chats/` | List all chats for the current user |
| `POST` | `/api/chat/chats/` | Create a new chat |
| `GET` | `/api/chat/chats/{chat_id}/messages/` | Get messages for a chat |
| `DELETE` | `/api/chat/chats/{chat_id}/delete/` | Delete a chat |
| `POST` | `/api/chat/chats/upload/` | Upload files to a chat |
| `DELETE` | `/api/chat/chats/{chat_id}/{file_id}/delete/` | Delete a chat file |
| `GET` | `/api/chat/languages/` | List supported languages |
| `GET` | `/api/chat/analytics/dashboard/` | Analytics dashboard data (staff only) |

### Files & Knowledge Bases

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/upload/` | List uploaded files |
| `POST` | `/api/upload/` | Upload a file (staff only) |
| `GET` | `/api/files/{id}/raw/` | Get raw file content |
| `GET` | `/api/files/{id}/processed/` | Get processed file (Docling JSON) |
| `GET` | `/api/files/{file_id}/docling-json/` | Get Docling JSON data |
| `POST` | `/api/files/{file_id}/approve-file/` | Approve/review a file |
| `GET` | `/api/files/{file_id}/ai-comments/` | Get AI-generated comments |
| `DELETE` | `/api/files/{file_id}/delete/` | Delete a file (staff only) |
| `GET` | `/api/knowledge-bases/` | List knowledge bases |
| `POST` | `/api/knowledge-bases/` | Create a knowledge base (staff only) |
| `GET` | `/api/knowledge-bases/{pk}/` | Get knowledge base details |
| `PUT/PATCH` | `/api/knowledge-bases/{pk}/` | Update a knowledge base (staff only) |
| `DELETE` | `/api/knowledge-bases/{pk}/` | Delete a knowledge base (staff only) |

### Authentication & User Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/signup/` | Register a new user |
| `POST` | `/api/login/` | Login and receive JWT tokens |
| `POST` | `/api/token/refresh/` | Refresh JWT access token |
| `POST` | `/api/token/verify/` | Verify a JWT token |
| `POST` | `/api/verify-email/` | Verify email address with token |
| `POST` | `/api/resend-verification/` | Resend email verification |
| `POST` | `/api/forgot-password/` | Request a password reset |
| `POST` | `/api/reset-password/` | Reset password with token |
| `GET` | `/api/users/me/role/` | Get current user's role |
| `GET` | `/api/users/` | List all users (staff only) |
| `POST` | `/api/users/` | Create a user (staff only) |
| `GET/PUT` | `/api/users/{user_id}/` | View or update user details (staff only) |
| `DELETE` | `/api/users/{user_id}/` | Delete a user (staff only) |
| `POST` | `/api/users/{user_id}/activate/` | Activate user account (staff only) |
| `POST` | `/api/users/{user_id}/deactivate/` | Deactivate user account (staff only) |
| `POST` | `/api/users/{user_id}/change-password/` | Change user password (staff only) |
| `POST` | `/api/users/bulk-create/` | Bulk create users from CSV (staff only) |
| `GET` | `/api/users/template/` | Download CSV template for bulk creation (staff only) |
| `GET` | `/api/users/stats/` | Get user statistics (staff only) |
| `GET` | `/api/profile/` | Get current user's profile |

### Query & Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/query-enhanced/` | Combined Qdrant semantic search + SQL analysis |

### Speech

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/speech/transcribe/` | Transcribe audio using Whisper |

### Application Settings

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/settings/configs/` | List all configuration namespaces (staff only) |
| `GET` | `/api/settings/configs/{namespace}/` | Get configuration for a namespace (staff only) |
| `PUT` | `/api/settings/configs/{namespace}/` | Update configuration for a namespace (staff only) |
| `POST` | `/api/settings/configs/{namespace}/reset/` | Reset a namespace to defaults (staff only) |
| `POST` | `/api/settings/configs/reset/` | Reset all namespaces to defaults (staff only) |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health/` | Application health check (DB, cache, storage, Docling, Qdrant) |
| `GET` | `/admin/` | Django admin panel |

---

## Security

MOSPI includes multiple layers of security:

- **Authentication**: JWT with token rotation; refresh tokens for seamless sessions
- **Account Protection**: Automatic lockout after repeated failed login attempts; login rate limiting
- **Transport Security**: HTTPS enforcement in production; HSTS headers
- **Input Validation**: Server-side sanitization middleware; CSRF and XSS protection
- **CORS**: Whitelist-based origin policy
- **Content Security Policy**: Strict CSP headers via security middleware
- **HTTP Method Restriction**: Only allowed methods are accepted per endpoint

### Production Checklist

- [ ] Change all default secret keys and passwords
- [ ] Set `DEBUG=0`
- [ ] Configure HTTPS with a reverse proxy (e.g., Nginx) and SSL certificates
- [ ] Set proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- [ ] Use environment-specific `.env` files
- [ ] Set up firewall rules to restrict service ports
- [ ] Enable regular security updates for all containers

---

## Logs and Monitoring

```bash
# View all service logs
docker compose logs -f

# View specific service logs
docker compose logs -f web
docker compose logs -f celery
docker compose logs -f ollama

# Monitor resource usage
docker stats
```

---

## Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is proprietary. Please contact [EduBild](https://github.com/EduBild-Git) for licensing information.

---

## Acknowledgments

Built with [Django](https://www.djangoproject.com/), [SvelteKit](https://kit.svelte.dev/), [Qdrant](https://qdrant.tech/), [Docling](https://github.com/docling-project/docling), [Vanna](https://vanna.ai/), and [Ollama](https://ollama.com/).

Developed by [EduBild](https://github.com/EduBild-Git).
