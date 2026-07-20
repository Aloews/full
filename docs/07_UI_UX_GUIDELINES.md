# AlphaPulse Design System

Version: 1.0

Status: Approved Draft

---

# Design Philosophy

AlphaPulse is not a trading terminal.

AlphaPulse is not a social network.

AlphaPulse is not a news feed.

AlphaPulse is a calm intelligence platform.

---

# Core Emotional Goal

После использования пользователь должен чувствовать:

```text
Informed

Calm

Confident
```

а не:

```text
Overwhelmed

Distracted

Anxious
```

---

# Design Principles

## Clarity

Every screen should answer one primary question.

---

## Simplicity

Remove everything that does not create value.

---

## Focus

Important information must stand out naturally.

---

## Consistency

Identical actions should look identical everywhere.

---

## Trust

Avoid hype, urgency, flashing indicators.

---

# Color System

## Primary

```css
#0F172A
```

Deep Slate

---

## Accent

```css
#6366F1
```

Indigo

---

## Secondary Accent

```css
#8B5CF6
```

Soft Purple

---

## Background

```css
#FAFAFA
```

---

## Surface

```css
#FFFFFF
```

---

## Border

```css
#E5E7EB
```

---

## Text Primary

```css
#111827
```

---

## Text Secondary

```css
#6B7280
```

---

# Status Colors

HIGH Confidence

```css
#6366F1
```

---

MEDIUM Confidence

```css
#9CA3AF
```

---

LOW Confidence

Не отображается в Dashboard MVP.

---

Важно:

Никаких красных цветов для роста или сигналов.

Красный используется только для ошибок системы.

---

# Typography

Primary Font:

```text
Inter
```

Fallback:

```text
System UI
```

---

Hero

```text
64px
```

---

H1

```text
48px
```

---

H2

```text
36px
```

---

Body

```text
18px
```

---

Caption

```text
14px
```

---

# Spacing System

Base Unit

```text
8px
```

---

Scale

```text
8
16
24
32
48
64
```

---

# Components

## Signal Card

Structure:

```text
Badge

Title

Summary

Confidence

Action
```

---

Example:

```text
HIGH CONFIDENCE

AgentFlow

Developer adoption accelerating.

Confidence: HIGH

View Analysis
```

---

# Project Card

Structure:

```text
Name

Category

Confidence

Short Summary
```

---

# Brief Card

Structure:

```text
Good Morning

Signals Analyzed

Signals Selected

Reading Time
```

---

# Dashboard Layout

```text
Header

↓

Morning Brief

↓

Top Insights

↓

Signals Feed

↓

Watchlist

↓

Market Observations
```

---

# Dashboard Rules

Maximum visible signals:

```text
5
```

---

Maximum visible insights:

```text
3
```

---

Maximum reading time:

```text
5 minutes
```

---

# Project Page

Sections:

```text
Overview

Why It Matters

Potential

Risks

Recent Signals

Related Projects
```

---

# Search UX

Instant search.

Response target:

```text
< 300ms
```

---

Results grouped by:

```text
Projects

Signals
```

---

# Empty States

Never show blank screens.

---

Example:

```text
No signals today.

We're still monitoring the market.
```

---

# Notifications

Default:

```text
OFF
```

---

Reason:

Reduce noise.

---

Available:

```text
Daily Brief

Watchlist Changes
```

---

# Telegram UX

Daily message structure:

```text
☕ Morning Brief

Signals analyzed: 12,486

Signals worth attention: 4

Estimated reading time: 3 minutes
```

---

Signal:

```text
💡 Interesting Observation

AgentFlow

Developer adoption accelerating.

Confidence: HIGH
```

---

# Mobile UX

Primary target:

```text
iPhone
```

---

First screen contains:

```text
Morning Brief

Top Insight

Read Brief
```

---

No horizontal scrolling.

---

Touch Targets

Minimum:

```text
44x44 px
```

---

# Accessibility

Minimum contrast:

```text
WCAG AA
```

---

Keyboard navigation:

Required.

---

Dark mode:

Required.

---

# Dark Theme

Background

```css
#020617
```

---

Surface

```css
#0F172A
```

---

Text

```css
#F8FAFC
```

---

# Animation Rules

Allowed:

```text
Fade

Slide

Soft Float
```

---

Forbidden:

```text
Blinking

Aggressive motion

Autoplay distractions
```

---

# UX Success Metrics

User understands dashboard:

```text
< 30 seconds
```

---

User reads brief:

```text
< 5 minutes
```

---

User returns next day:

Target:

```text
> 35%
```

---

# Design Review Checklist

✅ Consistent with Vision

✅ Consistent with Product Philosophy

✅ Supports Mobile

✅ Supports Accessibility

✅ Avoids Information Overload

✅ Reinforces Calm Intelligence

---

# Status

Approved for MVP.
