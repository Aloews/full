# AlphaPulse Telegram Bot Specification

Version: 1.0

Status: Approved Draft

---

# Purpose

The Telegram Bot serves as the first intelligence delivery channel for AlphaPulse.

Its primary role is not interaction.

Its primary role is delivery.

Users should receive valuable insights without opening the web application.

---

# Product Philosophy

The bot should feel like:

```text
A trusted analyst.
```

Not:

```text
A notification machine.
```

---

# Core Objectives

## Objective 1

Deliver daily intelligence.

---

## Objective 2

Increase retention.

---

## Objective 3

Create habit formation.

---

## Objective 4

Provide value before dashboard visits.

---

# MVP Scope

Included:

✅ Daily Brief

✅ Signals

✅ Watchlist Updates

✅ Account Linking

✅ Basic Commands

---

Excluded:

❌ AI Chat

❌ Conversational Assistant

❌ Complex Queries

❌ Voice Features

---

# Bot Architecture

```text
User

↓

Telegram Bot API

↓

Bot Service

↓

AlphaPulse API

↓

Database
```

---

# Authentication

Users authenticate via:

```text
Magic Link
```

or

```text
Telegram Deep Link
```

---

# User States

## Anonymous

Can:

- View welcome message
- Join waitlist

Cannot:

- Access personal watchlists

---

## Registered

Can:

- Receive briefs
- Manage watchlists
- Receive alerts

---

# Commands

## /start

Purpose:

Initial onboarding.

---

Response:

```text
Welcome to AlphaPulse.

We scan the market,
so you don't have to.

Receive daily AI market intelligence
in under 5 minutes.

Available commands:

/brief
/trending
/watchlist
/help
```

---

## /brief

Purpose:

Show latest Morning Brief.

---

Example:

```text
☕ Morning Brief

Signals analyzed:
12,486

Signals selected:
4

Estimated reading time:
3 minutes
```

---

Then show top signals.

---

## /trending

Purpose:

Show current top projects.

---

Example:

```text
🔥 Trending Projects

1. AgentFlow
Confidence: HIGH

2. PromptOps
Confidence: HIGH

3. AutoCoder
Confidence: MEDIUM
```

---

## /watchlist

Purpose:

Display personal watchlist.

---

Example:

```text
📌 Watchlist

AgentFlow

PromptOps

LegalMind
```

---

## /help

Purpose:

Show available actions.

---

# Daily Brief Delivery

Schedule:

```text
08:00 user local time
```

---

Important:

Only one brief per day.

Never more.

---

# Brief Structure

Section 1

```text
☕ Good Morning
```

---

Section 2

```text
Signals analyzed:
12,486
```

---

Section 3

```text
Signals worth attention:
4
```

---

Section 4

Top Insight.

---

Section 5

Additional Signals.

---

# Top Insight Format

```text
💡 High Confidence

AgentFlow

Developer adoption accelerating.

Why it matters:

Growing developer activity
and increasing discussion volume.

Confidence:
HIGH
```

---

# Watchlist Alerts

Trigger only when:

```text
Confidence changes
```

or

```text
New signal generated
```

---

Example:

```text
📈 Watchlist Update

AgentFlow

Confidence changed:

MEDIUM → HIGH
```

---

# Alert Rules

Maximum alerts:

```text
3 per day
```

---

Preferred:

```text
0–1 per day
```

---

Reason:

Protect user attention.

---

# Notification Policy

Default:

```text
Daily Brief ON

Watchlist Alerts OFF
```

---

User can enable:

```text
Watchlist Alerts
```

---

User can disable:

```text
Everything
```

except account messages.

---

# Message Formatting

Use:

```text
Plain text

Short paragraphs

Bullet points
```

---

Avoid:

```text
Large blocks

Emoji overload

Marketing language
```

---

# Approved Emojis

```text
☕
💡
📈
📌
🔥
```

---

Maximum:

```text
2 emojis per message
```

---

# Telegram Menu

Persistent Menu:

```text
Morning Brief

Trending Projects

Watchlist

Settings
```

---

# Settings

Users can configure:

## Brief Time

Options:

```text
07:00

08:00

09:00
```

---

## Alerts

```text
ON

OFF
```

---

## Timezone

Auto-detected.

Editable.

---

# Growth Features

## Referral Link

Each user receives:

```text
https://alphapulse.ai/r/{code}
```

---

Reward Example

```text
Invite 3 users

↓

Get 30 days Premium
```

---

Status:

Not MVP.

Version:

```text
1.1
```

---

# Analytics Events

Track:

```text
brief_opened

signal_clicked

watchlist_viewed

settings_updated
```

---

# Success Metrics

Daily Brief Open Rate

Target:

```text
> 60%
```

---

Watchlist Usage

Target:

```text
> 20%
```

---

Daily Active Telegram Users

Target:

```text
> 40%
```

of registered users.

---

# Failure Handling

If Brief Generation Fails

Send:

```text
We're still processing today's market data.

Your briefing will arrive shortly.
```

---

If API Unavailable

Retry:

```text
3 times
```

before failure state.

---

# Security

Store:

```text
Telegram User ID
```

Never store:

```text
Chat history
```

for MVP.

---

# Bot Review Checklist

✅ Consistent with Calm Intelligence

✅ Minimal Notifications

✅ Supports Habit Formation

✅ Works Before Dashboard Launch

✅ Supports First Paying Users

---

# Status

Approved for MVP.
