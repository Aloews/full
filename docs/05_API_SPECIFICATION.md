# AlphaPulse API Specification

Version: 1.0

Status: Approved Draft

---

# API Overview

Base URL

```text
/api/v1
```

---

Authentication:

```text
JWT Bearer Token
```

---

Content Type:

```text
application/json
```

---

# Authentication

## Register

```http
POST /auth/register
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password",
  "full_name": "John Doe"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "user_id": "uuid"
  }
}
```

---

## Login

```http
POST /auth/login
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "access_token": "jwt",
    "refresh_token": "jwt"
  }
}
```

---

# Projects

## Get Projects

```http
GET /projects
```

Query Parameters:

```text
page
limit
category
confidence
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "AgentFlow",
      "confidence": "HIGH"
    }
  ]
}
```

---

## Get Project

```http
GET /projects/{project_id}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "AgentFlow",
    "description": "...",
    "confidence": "HIGH"
  }
}
```

---

# Signals

## Latest Signals

```http
GET /signals
```

Filters:

```text
confidence
signal_type
```

---

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Interesting Observation",
      "confidence": "HIGH"
    }
  ]
}
```

---

# Watchlist

## Add Project

```http
POST /watchlist
```

Request:

```json
{
  "project_id": "uuid"
}
```

---

## Remove Project

```http
DELETE /watchlist/{project_id}
```

---

## User Watchlist

```http
GET /watchlist
```

---

# Daily Brief

## Latest Brief

```http
GET /brief/latest
```

Response:

```json
{
  "success": true,
  "data": {
    "title": "Morning Brief",
    "content": "..."
  }
}
```

---

# Search

## Search Projects

```http
GET /search
```

Query:

```text
q
```

Response:

```json
{
  "success": true,
  "data": []
}
```

---

# Admin (Internal)

Не доступно обычным пользователям.

---

## Recalculate Scores

```http
POST /admin/recalculate
```

---

## Trigger Brief Generation

```http
POST /admin/generate-brief
```

---

# Error Codes

```text
UNAUTHORIZED
FORBIDDEN
PROJECT_NOT_FOUND
VALIDATION_ERROR
INTERNAL_ERROR
RATE_LIMITED
```

---

# Rate Limits

Anonymous:

```text
60 requests/minute
```

Authenticated:

```text
300 requests/minute
```

---

# API Review Checklist

✅ Соответствует PRD

✅ Соответствует Database Design

✅ Соответствует Architecture

✅ Нет лишних endpoint'ов

✅ Поддерживает MVP

