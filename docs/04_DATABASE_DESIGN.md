# AlphaPulse Database Design

Version: 1.0

Status: Approved Draft

---

# Purpose

This document defines the database architecture for AlphaPulse MVP.

The database must support:

- User management
- Project discovery
- Signal generation
- Watchlists
- Daily insights
- Historical metrics

while remaining simple enough for MVP implementation.

---

# Database Technology

Primary Database:

```text
PostgreSQL 16
```

Reason:

- Mature ecosystem
- Strong indexing
- JSON support
- Excellent analytical capabilities for MVP

---

# Database Principles

## Single Source of Truth

All operational data is stored in PostgreSQL.

---

## Historical Tracking

Metrics are never overwritten.

Metrics are stored as snapshots.

---

## Auditability

Signals can always be traced back to source metrics.

---

## Extensibility

Schema supports future modules:

- Founder Intelligence
- Revenue Estimator
- Market Gap Finder
- AI Analyst

without breaking changes.

---

# Entity Relationship Overview

```text
users
 │
 └── watchlists
          │
          ▼
       projects
          │
 ┌────────┼────────┐
 ▼        ▼        ▼

metrics  scores  signals
```

---

# Table: users

Purpose:

Store platform users.

---

Columns

| Column | Type | Nullable |
|----------|----------|----------|
| id | UUID | No |
| email | VARCHAR(255) | No |
| password_hash | TEXT | No |
| full_name | VARCHAR(255) | Yes |
| role | VARCHAR(50) | No |
| created_at | TIMESTAMP | No |
| updated_at | TIMESTAMP | No |

---

Constraints

```sql
PRIMARY KEY (id)
UNIQUE(email)
```

---

Indexes

```sql
CREATE UNIQUE INDEX idx_users_email
ON users(email);
```

---

# Table: projects

Purpose:

Store tracked projects.

---

Columns

| Column | Type |
|----------|----------|
| id | UUID |
| name | VARCHAR(255) |
| slug | VARCHAR(255) |
| description | TEXT |
| website_url | TEXT |
| github_url | TEXT |
| category | VARCHAR(100) |
| status | VARCHAR(50) |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

---

Constraints

```sql
PRIMARY KEY(id)
UNIQUE(slug)
```

---

Indexes

```sql
CREATE INDEX idx_projects_category
ON projects(category);
```

```sql
CREATE INDEX idx_projects_status
ON projects(status);
```

---

# Table: project_metrics

Purpose:

Store historical snapshots.

---

Important:

Never update rows.

Only insert snapshots.

---

Columns

| Column | Type |
|----------|----------|
| id | UUID |
| project_id | UUID |
| github_stars | INTEGER |
| github_forks | INTEGER |
| github_contributors | INTEGER |
| reddit_mentions | INTEGER |
| reddit_upvotes | INTEGER |
| hn_points | INTEGER |
| hn_comments | INTEGER |
| snapshot_time | TIMESTAMP |

---

Foreign Keys

```sql
FOREIGN KEY(project_id)
REFERENCES projects(id)
```

---

Indexes

```sql
CREATE INDEX idx_metrics_project
ON project_metrics(project_id);
```

```sql
CREATE INDEX idx_metrics_snapshot
ON project_metrics(snapshot_time);
```

---

Composite Index

```sql
CREATE INDEX idx_metrics_project_time
ON project_metrics(project_id, snapshot_time DESC);
```

---

# Table: scores

Purpose:

Store calculated confidence scores.

---

Columns

| Column | Type |
|----------|----------|
| id | UUID |
| project_id | UUID |
| score | INTEGER |
| confidence | VARCHAR(50) |
| calculated_at | TIMESTAMP |

---

Examples

```text
92 → High
67 → Medium
38 → Low
```

---

Indexes

```sql
CREATE INDEX idx_scores_project
ON scores(project_id);
```

```sql
CREATE INDEX idx_scores_value
ON scores(score DESC);
```

---

# Table: signals

Purpose:

Store generated insights.

---

Columns

| Column | Type |
|----------|----------|
| id | UUID |
| project_id | UUID |
| signal_type | VARCHAR(100) |
| title | VARCHAR(255) |
| summary | TEXT |
| confidence | VARCHAR(50) |
| created_at | TIMESTAMP |

---

Signal Types

```text
high_confidence
worth_watching
early_signal
```

---

Indexes

```sql
CREATE INDEX idx_signals_created
ON signals(created_at DESC);
```

```sql
CREATE INDEX idx_signals_confidence
ON signals(confidence);
```

---

# Table: watchlists

Purpose:

User tracking preferences.

---

Columns

| Column | Type |
|----------|----------|
| id | UUID |
| user_id | UUID |
| project_id | UUID |
| created_at | TIMESTAMP |

---

Constraints

```sql
UNIQUE(user_id, project_id)
```

---

Foreign Keys

```sql
FOREIGN KEY(user_id)
REFERENCES users(id)

FOREIGN KEY(project_id)
REFERENCES projects(id)
```

---

Indexes

```sql
CREATE INDEX idx_watchlists_user
ON watchlists(user_id);
```

---

# Table: ai_summaries

Purpose:

Store generated summaries.

---

Reason:

Avoid repeated LLM requests.

Reduce cost.

---

Columns

| Column | Type |
|----------|----------|
| id | UUID |
| project_id | UUID |
| summary | TEXT |
| model | VARCHAR(100) |
| generated_at | TIMESTAMP |

---

Indexes

```sql
CREATE INDEX idx_ai_project
ON ai_summaries(project_id);
```

---

# Table: daily_briefs

Purpose:

Store generated daily briefings.

---

Columns

| Column | Type |
|----------|----------|
| id | UUID |
| title | VARCHAR(255) |
| content | TEXT |
| generated_at | TIMESTAMP |

---

Purpose

Feeds:

- Dashboard
- Telegram
- Email

---

# MVP ER Diagram

```text
users
 │
 └──── watchlists
          │
          ▼
       projects
          │
 ┌────────┼────────┬─────────┐
 ▼        ▼        ▼         ▼

metrics scores signals summaries
```

---

# Retention Policy

## Metrics

Keep forever.

Historical growth is valuable.

---

## Signals

Keep forever.

Used for validation.

---

## AI Summaries

Keep forever.

Can be regenerated if needed.

---

# Query Examples

## Top Signals

```sql
SELECT *
FROM signals
ORDER BY created_at DESC
LIMIT 20;
```

---

## Project History

```sql
SELECT *
FROM project_metrics
WHERE project_id = $1
ORDER BY snapshot_time DESC;
```

---

## User Watchlist

```sql
SELECT p.*
FROM watchlists w
JOIN projects p
ON p.id = w.project_id
WHERE w.user_id = $1;
```

---

# Future Tables (Not MVP)

Reserved for:

```text
founders
founder_scores

market_gaps

revenue_estimates

traffic_metrics

analyst_queries

analyst_reports
```

These tables are intentionally excluded from MVP.

---

# Database Review Checklist

✅ Normalized schema

✅ No duplicated entities

✅ Historical data preserved

✅ Supports watchlists

✅ Supports Telegram Digest

✅ Supports Dashboard

✅ Supports AI summaries

✅ Compatible with MVP architecture

✅ Compatible with future scaling

---

# Database Status

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

# Amendment C — Signal Traceability

Status: Mandatory

# Table: signal_sources

Purpose:

Store evidence used to generate signals.

---

Reason:

Every signal must be explainable.

---

Columns

| Column | Type |
|----------|----------|
| id | UUIDv7 |
| signal_id | UUIDv7 |
| source_type | VARCHAR(50) |
| metric_name | VARCHAR(100) |
| metric_value | NUMERIC |
| previous_value | NUMERIC |
| delta_percentage | NUMERIC |
| created_at | TIMESTAMPTZ |

---

Examples

```text
signal_id: abc

source_type:
github

metric_name:
stars_growth

metric_value:
1250

previous_value:
1000

delta_percentage:
25%
```

---

Supported Sources

```text
github
reddit
hacker_news
```

---

Benefits

✅ Explainable AI

✅ Easier debugging

✅ Historical validation

✅ Investor transparency

---

# AI Model Update

Every generated signal must include:

```text
Evidence
```

New structure:

```text
What Happened

Why It Matters

Evidence

Potential

Risks
```

