# AlphaPulse Risks & Assumptions

Version: 1.0

Status: Approved Draft

---

# Purpose

Document critical assumptions and risks.

---

# Assumption A1

Users care about discovering AI companies early.

Confidence:

```text
Medium
```

Validation Method:

- Interviews
- Waitlist
- Retention

---

# Assumption A2

Telegram is a viable delivery channel.

Confidence:

```text
Medium
```

Validation Method:

```text
Open Rate > 60%
```

---

# Assumption A3

Users will pay for curated intelligence.

Confidence:

```text
Low-Medium
```

Validation Method:

```text
Conversion > 5%
```

---

# Assumption A4

GitHub activity correlates with opportunity.

Confidence:

```text
Medium
```

Validation Method:

Historical tracking.

---

# Assumption A5

Three public data sources are enough for MVP.

Confidence:

```text
High
```

Sources:

- GitHub
- Reddit
- Hacker News

---

# Technical Risks

---

## R1

GitHub API Limits

Impact:

```text
High
```

Probability:

```text
Medium
```

Mitigation:

- Redis cache
- Scheduled collection
- Batch requests

---

## R2

Reddit API Changes

Impact:

```text
Medium
```

Probability:

```text
Medium
```

Mitigation:

- Coverage Score
- Replaceable source architecture

---

## R3

Poor Signal Quality

Impact:

```text
High
```

Probability:

```text
Medium
```

Mitigation:

- User feedback
- Signal audits
- Confidence scoring

---

# Product Risks

---

## R4

Users Do Not Return

Impact:

```text
Critical
```

Probability:

```text
Medium
```

Mitigation:

- Daily Brief
- Better onboarding
- User interviews

---

## R5

Information Overload

Impact:

```text
High
```

Probability:

```text
High
```

Mitigation:

- Max 5 signals
- Calm Intelligence design
- Daily digest

---

## R6

No Willingness To Pay

Impact:

```text
Critical
```

Probability:

```text
Medium
```

Mitigation:

- Early pricing tests
- Concierge interviews
- Premium previews

---

# Business Risks

---

## R7

Strong Competitor Appears

Impact:

```text
High
```

Probability:

```text
Medium
```

Mitigation:

- Move faster
- Focus on trust
- Build distribution

---

## R8

AI Market Slows

Impact:

```text
Medium
```

Probability:

```text
Low
```

Mitigation:

Platform can expand beyond AI.

---

# Security Risks

---

## R9

User Data Exposure

Impact:

```text
Critical
```

Probability:

```text
Low
```

Mitigation:

- Encryption
- JWT
- Least privilege

---

# Operational Risks

---

## R10

Founder Burnout

Impact:

```text
High
```

Probability:

```text
Medium
```

Mitigation:

- Strict MVP
- Weekly planning
- Automation

---

# Kill Criteria

Project should be reconsidered if:

### Condition 1

```text
Retention < 15%
after 100 users
```

---

### Condition 2

```text
Conversion < 1%
after 1000 users
```

---

### Condition 3

```text
Signal usefulness consistently rated low
```

---

# Success Indicators

Strong signs of PMF:

### Indicator 1

```text
Users request more signals
```

---

### Indicator 2

```text
Users ask for premium access
```

---

### Indicator 3

```text
Users share briefs
```

---

### Indicator 4

```text
Users create watchlists
```

---

# Risk Review Frequency

Monthly.

---

# Status

Approved.
