# AlphaPulse System Architecture

Version: 1.0

Status: Approved Draft

---

# Purpose

This document describes the technical architecture of AlphaPulse MVP and its evolution path toward a scalable production platform.

---

# Architectural Principles

## Simplicity First

Prefer simple solutions over complex systems.

Avoid premature microservices.

---

## Reliability

Users should always receive insights even if individual data sources fail.

---

## Scalability

Architecture should scale from:

```text
100 users
```

to

```text
100,000 users
```

without full redesign.

---

## Cost Efficiency

Initial infrastructure budget:

```text
€100–300/month
```

---

# MVP Architecture

```text
Users
  │
  ▼

Frontend (Next.js)

  │

Backend API (FastAPI)

  │

 ┌─────────────┬─────────────┐
 │             │
 ▼             ▼

PostgreSQL    Redis

 │
 ▼

Workers

 ├── GitHub Worker
 ├── Reddit Worker
 └── HackerNews Worker
```

---

# Technology Stack

## Frontend

Framework:

```text
Next.js
```

Language:

```text
TypeScript
```

UI:

```text
Tailwind CSS
```

---

## Backend

Framework:

```text
FastAPI
```

Language:

```text
Python 3.12
```

---

## Database

Primary:

```text
PostgreSQL
```

---

## Cache

```text
Redis
```

Used for:

- API caching
- Session caching
- Rate limiting

---

## Background Jobs

```text
Celery
```

Broker:

```text
Redis
```

---

# Logical Components

## API Layer

Responsibilities:

- Authentication
- Dashboard data
- Project retrieval
- Watchlists

---

Endpoints:

```http
GET /projects
GET /projects/{id}
GET /signals
POST /watchlist
```

---

## Data Collection Layer

Purpose:

Collect market signals.

---

### GitHub Worker

Collects:

- Stars
- Forks
- Contributors
- Releases

Frequency:

```text
60 minutes
```

---

### Reddit Worker

Collects:

- Mentions
- Upvotes
- Comments

Frequency:

```text
60 minutes
```

---

### Hacker News Worker

Collects:

- Points
- Rank
- Comments

Frequency:

```text
30 minutes
```

---

# Scoring Engine

Purpose:

Calculate project confidence.

---

Input:

```text
GitHub metrics
Reddit metrics
HN metrics
```

---

Formula:

```text
GitHub Growth     50%
Reddit Momentum   30%
HN Momentum       20%
```

---

Output:

```json
{
  "confidence": "high",
  "score": 87
}
```

---

# AI Summary Service

Purpose:

Generate human-readable project summaries.

---

Input:

Project metrics.

---

Output:

- What it does
- Why it matters
- Risks
- Potential

---

Provider:

```text
OpenAI API
```

MVP only.

---

# Database Architecture

Primary storage:

```text
PostgreSQL
```

Stores:

- Users
- Projects
- Metrics
- Signals
- Watchlists

---

# Security

Authentication:

```text
JWT
```

---

Password Storage:

```text
Argon2
```

---

Transport:

```text
HTTPS
```

---

# Deployment

## MVP

Infrastructure:

```text
Hetzner VPS
```

Components:

- Docker
- PostgreSQL
- Redis
- FastAPI
- Next.js

---

# Monitoring

Logs:

```text
Grafana Loki
```

Metrics:

```text
Prometheus
```

Dashboards:

```text
Grafana
```

---

# Backup Strategy

Database:

Daily backup.

Retention:

```text
30 days
```

---

# Scaling Plan

## Stage 1

0–1,000 users

Single server.

---

## Stage 2

1,000–10,000 users

Separate database.

Separate workers.

---

## Stage 3

10,000–100,000 users

Introduce:

- Kafka
- ClickHouse
- Qdrant

---

# Failure Handling

If Reddit fails:

Continue processing GitHub and HN.

If AI summaries fail:

Serve latest cached summary.

If worker fails:

Retry automatically.

---

# Architecture Review Checklist

✅ Single source of truth (PostgreSQL)

✅ No unnecessary microservices

✅ Fits MVP scope

✅ Scales incrementally

✅ Infrastructure cost controlled

✅ Security baseline defined

✅ Monitoring included

✅ Backup strategy included

---

# Architecture Status

Approved for MVP implementation.

---

# Amendment A — Engineering Standards

# Global Data Standards

## Time Standard

Все даты и время хранятся исключительно в UTC.

Тип:

```sql
TIMESTAMP WITH TIME ZONE
```

Пример:

```text
2026-07-17T08:15:00Z
```

Запрещено:

```text
Local Time
Server Time
Timezone Offsets
```

---

## Primary Key Standard

Для всех новых сущностей:

```text
UUIDv7
```

Причины:

- сортируются по времени;
- лучше для индексов;
- лучше для масштабирования;
- проще будущая миграция на распределённые системы.

Пример:

```text
01981258-1ec7-7c2d-bc8d-e11f9f75e91f
```

---

## Naming Convention

Таблицы:

```text
snake_case
plural
```

Пример:

```text
users
projects
project_metrics
```

---

Поля:

```text
snake_case
```

Пример:

```text
created_at
updated_at
github_stars
```

---

## Audit Fields

Каждая основная таблица обязана содержать:

```sql
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

---

## Soft Delete Policy

Используем только там, где есть пользовательские данные.

Добавляем:

```sql
deleted_at TIMESTAMPTZ NULL
```

Для:

```text
users
projects
```

Не использовать для:

```text
project_metrics
scores
signals
```

Исторические данные никогда не удаляются.

---

## API Standard

Все ответы:

```json
{
  "success": true,
  "data": {}
}
```

Ошибки:

```json
{
  "success": false,
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project not found"
  }
}
```

---

## Confidence Levels

Во всех сервисах используется единый enum.

```text
HIGH
MEDIUM
LOW
```

Запрещено:

```text
high
High
very_high
```

---

## Signal Types

Единый enum:

```text
HIGH_CONFIDENCE
WORTH_WATCHING
EARLY_SIGNAL
```

---

## Project Status

Единый enum:

```text
ACTIVE
INACTIVE
ARCHIVED
```

---

---

# Amendment B — Data Reliability Layer

Status: Approved

# Data Coverage Score

## Purpose

Measure data completeness for every project.

---

## Formula

Каждый источник имеет вес.

```text
GitHub       50%
Reddit       30%
Hacker News  20%
```

---

Пример.

Есть данные только GitHub.

```text
Coverage = 50
```

Есть GitHub + Reddit.

```text
Coverage = 80
```

Все источники доступны.

```text
Coverage = 100
```

---

## Coverage Categories

| Score | Status |
|---------|---------|
| 80–100 | COMPLETE |
| 50–79 | PARTIAL |
| 0–49 | LIMITED |

---

## Confidence Update

Старое правило:

```text
Score >= 80
```

Недостаточно.

Новое правило:

HIGH:

```text
Opportunity Score >= 80

AND

Coverage >= 80
```

---

MEDIUM:

```text
Opportunity Score >= 50
```

---

LOW:

```text
Everything else
```

---

Результат:

Проект не сможет получить HIGH Confidence только из-за всплеска GitHub.

---

# Data Source Reliability

Каждый источник получает Reliability Weight.

---

GitHub

```text
1.0
```

---

Hacker News

```text
0.8
```

---

Reddit

```text
0.7
```

---

Используется при расчёте будущих моделей.

---

# API Rate Limit Protection

Добавляется в Architecture.

---

# Collection Strategy

Не запрашивать API по каждому проекту.

Использовать батчи.

---

GitHub

Каждые:

```text
60 минут
```

---

Reddit

Каждые:

```text
60 минут
```

---

HN

Каждые:

```text
30 минут
```

---

# Cache Layer

Redis хранит:

```text
Latest Metrics

Top Signals

Project Summaries
```

TTL:

```text
15 минут
```

---

# Retry Policy

Worker Failure:

```text
3 retries
```

---

Backoff:

```text
1 min
5 min
15 min
```

---

# Fallback Logic

Если Reddit недоступен:

```text
Coverage decreases

System continues
```

---

Если HN недоступен:

```text
Coverage decreases

System continues
```

---

Если GitHub недоступен:

```text
Signal generation paused
```

Причина:

GitHub — основной источник MVP.

---
