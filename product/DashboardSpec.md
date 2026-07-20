# AlphaPulse Dashboard UX/UI Specification v1.0

## Главный принцип

Большинство аналитических платформ отвечают на вопрос:

> "Что происходит?"

AlphaPulse отвечает:

> "На что мне стоит обратить внимание сегодня?"

---

# Время использования

Целевое время сессии:

```text
3–5 минут утром
```

Пользователь не должен сидеть часами.

---

# Dashboard Structure

```text
Header
│
├── Morning Brief
│
├── Top Insights
│
├── Signals Today
│
├── Emerging Projects
│
├── Market Observations
│
└── Watchlist
```

---

# Header

Верхняя панель.

Слева:

```text
AlphaPulse
```

Справа:

- Search
- Notifications
- Profile

Минимализм.

Без лишних элементов.

---

# Блок 1 — Morning Brief

Первый экран.

Самый важный.

Карточка занимает почти весь первый viewport.

---

Пример:

```text
☕ Good Morning

We analyzed 12,486 market signals overnight.

Only 4 deserve your attention today.

Estimated reading time:
3 minutes.
```

Ниже кнопка:

```text
Read Brief
```

---

Психологический эффект:

Пользователь понимает:

> Кто-то уже сделал всю работу.

---

# Блок 2 — Top Insights

3 самые важные находки дня.

Карточки.

---

Карточка:

```text
💡 High Confidence

AgentFlow

Why it matters:

Developer adoption accelerating.

Commercial demand emerging.

Community activity increasing.

Confidence:
High
```

Кнопка:

```text
View Analysis
```

---

Без цифр по умолчанию.

Только смысл.

---

# Блок 3 — Signals Today

Лента сигналов.

Фильтры:

```text
All

Founders

Investors

Developers
```

---

Каждая карточка:

```text
Interesting Observation

Project Name

2 minute read

High Confidence
```

---

Цвета:

Высокая уверенность:

мягкий индиго.

Средняя:

серый.

Низкая:

не показывать в Dashboard.

---

# Блок 4 — Emerging Projects

Раздел для исследователей.

Заголовок:

```text
Projects worth watching
```

Карточка:

```text
Project

Early Signal

Potential:
Promising

Confidence:
Medium
```

---

Здесь можно показать внутренний скоринг.

Но аккуратно.

---

# Блок 5 — Market Observations

Очень сильный блок.

Не проекты.

А наблюдения.

---

Пример:

```text
Observation

AI agents continue attracting
developer attention.

Mentions increased across
multiple communities.
```

---

Или:

```text
Observation

Demand for AI-powered legal tools
appears to be increasing.
```

---

Этот блок делает AlphaPulse похожим на аналитика, а не каталог.

---

# Блок 6 — Watchlist

Персональный раздел.

---

Если пользователь следит за:

- AI Agents
- Coding Tools
- Legal AI

Показываем только изменения.

---

Пример:

```text
AgentFlow

Confidence increased

Yesterday:
Medium

Today:
High
```

---

# Project Page

При открытии проекта.

---

Секция 1

```text
What it does
```

Краткое объяснение.

---

Секция 2

```text
Why we're watching it
```

Причины интереса.

---

Секция 3

```text
Potential
```

Описание перспектив.

---

Секция 4

```text
Risks
```

Объективно.

Без хайпа.

---

Секция 5

```text
Related Projects
```

Похожие продукты.

---

# AI Analyst

Кнопка сверху:

```text
Ask AlphaPulse
```

---

Пользователь пишет:

```text
Show promising AI startups
with growing developer adoption.
```

Получает ответ как от аналитика.

---

# Dark Mode

Обязательно.

---

Светлая тема:

рабочий режим.

---

Тёмная:

вечернее чтение.

---

# Mobile Version

Главное правило:

Все важное помещается на первом экране.

---

Открываешь приложение.

Видишь:

```text
Morning Brief

Top Insights

Read in 3 minutes
```

И всё.

---

# MVP Dashboard Metrics

Показываем только:

- Confidence
- Trend Direction
- Observation Count

Не показываем:

- сложные графики;
- десятки метрик;
- технический шум.

---

# Эмоция после использования

Пользователь закрывает AlphaPulse с мыслью:

> Я ничего не упустил.
>
> Я знаю, что важно сегодня.
>
> На это ушло всего несколько минут.
