# AlphaPulse AI Models

Version: 1.0

Status: Approved Draft

---

# Purpose

This document defines all intelligence and scoring systems used by AlphaPulse.

The goal is to identify meaningful market opportunities while maintaining transparency and explainability.

---

# AI Principles

## Explainability First

Every score must be explainable.

Users should understand:

- why a project received attention;
- what signals contributed;
- what risks exist.

---

## Deterministic MVP

MVP uses rule-based scoring.

No machine learning is required for initial launch.

---

## Incremental Intelligence

The platform evolves in stages:

```text
Stage 1
Rule-Based Scoring

↓

Stage 2
Statistical Models

↓

Stage 3
Machine Learning

↓

Stage 4
Agentic Intelligence
```

---

# MVP Intelligence Stack

Included:

✅ Opportunity Score Engine

✅ Confidence Engine

✅ Signal Generation Engine

✅ AI Summary Engine

Excluded:

❌ Revenue Estimator

❌ Founder Intelligence

❌ Unicorn Predictor

❌ Clone Engine

❌ Market Gap Finder

---

# Opportunity Score Engine

Purpose:

Evaluate project momentum.

---

# Inputs

GitHub Metrics

```text
Stars Growth
Fork Growth
Contributor Growth
```

Reddit Metrics

```text
Mentions
Upvotes
Discussion Activity
```

Hacker News Metrics

```text
Points
Comments
Rank Position
```

---

# Normalization

All metrics normalized to:

```text
0–100
```

scale.

---

# Weighting

```text
GitHub Growth      50%
Reddit Momentum    30%
HN Momentum        20%
```

---

# Formula

```text
Opportunity Score =
(Github × 0.50)
+
(Reddit × 0.30)
+
(HN × 0.20)
```

---

# Output

Range:

```text
0–100
```

---

# Score Categories

| Score | Category |
|---------|---------|
| 80–100 | HIGH |
| 50–79 | MEDIUM |
| 0–49 | LOW |

---

# Example

```text
GitHub Growth: 90
Reddit Momentum: 70
HN Momentum: 80
```

Result:

```text
86
```

Confidence:

```text
HIGH
```

---

# Confidence Engine

Purpose:

Determine reliability of signals.

---

# Inputs

Opportunity Score

Data Source Coverage

Historical Consistency

---

# Logic

High Confidence

Requirements:

```text
Score ≥ 80

AND

At least 2 active sources
```

---

Medium Confidence

Requirements:

```text
Score ≥ 50
```

---

Low Confidence

Requirements:

```text
Score < 50
```

---

# Output Enum

```text
HIGH
MEDIUM
LOW
```

Standardized across platform.

---

# Signal Generation Engine

Purpose:

Transform scores into user-facing insights.

---

# Trigger Conditions

Generate signal when:

```text
Opportunity Score ≥ 70
```

OR

```text
Growth Rate Spike ≥ 30%
```

within rolling 7-day window.

---

# Signal Types

## HIGH_CONFIDENCE

Requirements:

```text
Confidence = HIGH
```

---

## WORTH_WATCHING

Requirements:

```text
Confidence = MEDIUM
```

---

## EARLY_SIGNAL

Requirements:

```text
Rapid Growth

but limited validation
```

---

# Signal Structure

Every signal contains:

```text
What happened

Why it matters

Potential

Risks
```

---

# AI Summary Engine

Purpose:

Generate readable project analysis.

---

# Inputs

Project Metadata

Latest Metrics

Recent Signals

---

# Output Structure

Section 1

```text
What It Does
```

---

Section 2

```text
Why We Are Watching It
```

---

Section 3

```text
Potential
```

---

Section 4

```text
Risks
```

---

# Summary Constraints

Maximum length:

```text
200 words
```

Language:

```text
Plain English
```

No hype.

No predictions.

No investment advice.

---

# Prompt Template

System Prompt

```text
You are a market intelligence analyst.

Your task is to summarize emerging projects.

Focus on:

1. What the project does.
2. Why it is gaining attention.
3. Potential opportunities.
4. Key risks.

Remain objective.

Do not exaggerate.
```

---

# Quality Controls

Reject summary if:

```text
< 50 words
```

or

```text
> 250 words
```

---

Reject summary if:

- empty sections;
- hallucinated metrics;
- unsupported claims.

---

# Data Freshness Rules

Scores older than:

```text
24 hours
```

must be recalculated.

---

Signals older than:

```text
7 days
```

become archived.

---

Summaries older than:

```text
30 days
```

eligible for regeneration.

---

# Future Model: Revenue Estimator

Status:

Deferred.

Version:

```text
1.2
```

Reason:

No reliable MVP data source.

---

# Future Model: Founder Intelligence

Status:

Deferred.

Version:

```text
1.3
```

Reason:

Requires founder dataset.

---

# Future Model: Market Gap Finder

Status:

Deferred.

Version:

```text
2.0
```

Reason:

Requires NLP clustering.

---

# Future Model: Unicorn Predictor

Status:

Deferred.

Version:

```text
3.0
```

Reason:

Requires long-term historical training data.

---

# Validation Metrics

Opportunity Score Precision

Definition:

```text
Projects classified as HIGH
that demonstrate increased adoption
within 14–30 days.
```

---

Target:

```text
≥ 30%
```

---

Signal Engagement Rate

Definition:

```text
Signal Opens / Signal Views
```

Target:

```text
≥ 25%
```

---

Summary Read Completion

Target:

```text
≥ 60%
```

---

# AI Safety Rules

AlphaPulse must never:

- provide investment advice;
- guarantee success;
- guarantee future growth;
- claim certainty.

Allowed:

```text
Interesting

Promising

Worth Watching

High Confidence
```

Not Allowed:

```text
Guaranteed Winner

Future Unicorn

Certain Success
```

---

# AI Model Review Checklist

✅ Fully explainable

✅ Consistent with MVP

✅ No hidden ML

✅ No impossible datasets

✅ Matches Database Design

✅ Matches API Specification

✅ Matches Product Vision

---

# Status

Approved for MVP implementation.

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

