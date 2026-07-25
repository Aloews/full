# Промпт v2: тотальное тестирование «Шерлок Скоулс»

> Вставь всё, что ниже, целиком как задание кодинг-агенту, работающему **внутри
> репозитория `Aloews/sherlock-scholes-`**. Написано от лица инженера, который
> пишет код с конца 60-х и агентскому коду не доверяет на слово.
>
> v2 сводит воедино сфокусированную версию и расширенный чек-лист, но **режет
> неприменимое к этому проекту** (см. раздел «Умышленно исключено» — читать до
> начала работы).

---

## Роль и философия

Ты — Staff Software Engineer + Principal QA + SDET с 40-летним опытом. Пиши так,
будто проект ведут NASA, Google и Stripe одновременно: цель — приложение должно
быть **практически невозможно сломать**. Существующему коду **не доверяй**;
исходи из того, что в проекте множество скрытых багов.

Я значительно старше тебя и код твой читать не буду — это единственный способ
пользоваться твоей продуктивностью. Вместо чтения я окружаю тебя экстремальными
ограничениями. Цепочка: **статанализ → юнит → property → целостность данных →
компонентные/snapshot → интеграция (на моках) → BDD/Gherkin → mutation → покрытие
→ security → CI-гейты**. Пока конвейер не зелёный — работа не сделана. «Тесты
проходят» без мутационного отчёта я за результат не считаю.

---

## Что за проект (важно для границ тестирования)

Telegram Mini App, игра-Alias про футбол: игроки объясняют футболистов. Два
принципиально разных пласта.

**1. Фронтенд `src/` — React 18 + TS + Vite + Zustand + Supabase.** Сейчас у него
**ноль тестов**; CI (`.github/workflows/ci.yml`) — только `typecheck` + `build`.
Ключевая чистая логика:
- `src/features/game/stateMachine.ts` — автомат фаз (`idle→lobby→countdown→
  round_active→round_summary→game_end`), таблица `TRANSITIONS`/`canTransition`.
- `src/features/game/cardRandomizer.ts` — graceful-degrade RPC-параметров
  (`p_continents/p_tags/p_init_data/p_difficulty/p_boost_countries/p_lang`),
  предикаты `isMissing*Param`, ретраи с бэкоффом на PGRST202.
- `src/shared/store/*` — `gameStore` (скоринг `updateCard`), `authStore`,
  `settingsStore`, `proStore`.
- `src/shared/lib/` — `tier`, `countryName`, `flag`, `cardName`, `pro`,
  `telegram`, `device`, `analytics`.
- `src/features/*` — хуки `useRoom`, `useLobby`, `useGame`, `useTimer`,
  `usePlayerStats`, `useTraining`, `useAuth`, `useProStatus`.
- `src/screens/*` — экраны Home/Lobby/Game/Training/End/Pro/Tutorial/Admin.

**2. Скрапер `football_scraper/` — Python.** Офлайн-инструмент сбора данных, в
Mini App не входит, но порождает карточки — тут и живут неточности. Уже есть 4
офлайн-теста без сети (`tests/test_dedup.py`, `test_merge.py`,
`test_pageviews.py`, `test_team_filter.py`) — образец стиля. Модули:
`scraper/dedup.py` (`canonical_key`, `find_duplicate_pairs`),
`scraper/supabase_writer.py` (`merge_player_name`), `scraper/pageviews.py`,
`scraper/team_filter.py`, `scraper/wikidata.py`, `scraper/history.py`.

**Данные:** `sherlock_cards.csv` (~2147 строк):
`category,category_ru,name,difficulty,forbidden_words`. Методология —
`football_scraper/CONTEXT.md`, `docs/players-db-methodology.md`.

**Бэкенда своего НЕТ.** Клиент ходит в Supabase напрямую (PostgREST + RPC
`pick_random_cards`). Поверхность безопасности = RLS-политики
(`supabase/migrations/rls_lockdown.sql`), edge-функция `supabase/functions/tg-pay`
и валидация Telegram `initData`. Тестируй именно это, а не выдуманные REST-ручки.

---

## Этап 1. Полный аудит (до тестов)

Просканируй весь проект и построй карту: архитектура, зависимости, RPC/RLS,
бизнес-логика, компоненты, хуки, экраны, сервисы, Telegram Mini App API, БД
(Supabase-таблицы `cards`/`players_meta`/`player_seasons`, миграции), кеш
(`scraper/cache.py`, preload фото), авторизация (Telegram `initData` → `authStore`),
роутинг (`app/Router.tsx`), состояния (zustand-сторы, `stateMachine`).

Найди и выпиши в отчёт: dead code, дубли, **race conditions** (realtime-комнаты,
таймер, ретраи рандомайзера), утечки памяти и **infinite rerender** (эффекты/
подписки zustand/framer-motion), async-баги, проглоченные исключения, неверные
типы, nullable-ошибки, **циклические зависимости** (`madge`/`dependency-cruiser`),
узкие места производительности, неоптимальные запросы к БД.

**Правило:** каждый найденный дефект → сначала падающий тест (regression-first),
потом правка, потом зелёный, потом коммит. Тест без предшествующего красного
прогона недействителен.

---

## Этап 2. Виды тестов (строить ВСЕ перечисленные)

### A. Статический анализ
ESLint (strict), **TypeScript strict-режим** (включить в `tsconfig`), `madge`/
`dependency-cruiser` на циклы, Semgrep-набор общих правил. Опционально CodeQL в
CI. SonarQube/платные SaaS — не подключать (см. «Исключено»).

### B. Юнит-тесты
**TS:** Vitest. Покрыть чистую логику, сторы, утилиты, парсеры/валидаторы, хуки
(`@testing-library/react`). **Python:** pytest, продолжая офлайн-стиль. Цель —
все функции ядра, сервисы, бизнес-логика, утилиты, hooks, store, парсеры,
валидаторы.

### C. Property-based (fast-check / Hypothesis)
Инварианты, не примеры: автомат из любой валидной фазы либо делает разрешённый
переход, либо стоит — но никогда не уходит в фазу вне `TRANSITIONS`; скоринг не
уходит в минус; `canonical_key` идемпотентна, устойчива к регистру/диакритике/
порядку «Имя Фамилия»↔«Фамилия, Имя»; `find_duplicate_pairs` симметрична; порог
<1.00 не склеивает разных людей.

### D. Целостность данных — ГЛАВНЫЙ фронт против неточностей
Прогоняй `sherlock_cards.csv` (в идеале и снапшот таблицы `cards`) через
инварианты. **Известные дефекты — начать с них, regression-first:**
- **Битая строка CSV:** есть ряд-обрубок, оканчивающийся на
  `…Вставляю Из Последней Неполной Карточки"` — незакрытая кавычка ломает
  парсинг. Тест: файл парсится строгим CSV-ридером без ошибок; в каждой строке
  ровно 5 колонок; нет «склеенных» многострочных ячеек.
- **Мёртвая `difficulty`:** тип `'easy'|'medium'|'hard'`
  (`src/shared/types/database.ts:250`), а в CSV у всех ~2145 строк — только
  `medium`. Тест: значение из множества И распределение не вырождено; для игроков
  согласовано с порогами pageviews (`CONTEXT.md`: novice>19000, fan>3000).

Инварианты дальше (отдельный тест на каждый):
- `category` ∈ реальному множеству (`player, club, club_nickname, coach,
  commentator, position, referee, stadium, term, woman`) и совпадает с
  `ALL_CATEGORIES`.
- `forbidden_words` непусто, содержит `name` и его разбор по словам, разделитель
  `|`, без пустых токенов.
- **Футбольная база (раздел под этот проект):** правдоподобие карьеры и сборной —
  игрок/клуб/сезон/трансфер/позиция/сборная согласованы (напр. позиция из
  допустимого набора; страна валидна; статус «играл на ЧМ»/клубы не
  противоречат друг другу). Это ровно та категория ошибок, что видна в UI.
- **Дубли игрока под разными именами:** тем же `canonical_key`, что и
  `scraper/dedup.py`, — один человек не встречается дважды.
- **Валидация источников:** тесты на слой сбора (`wikidata`, `pageviews`,
  `api_football`) на моках — форматы ответов, отсутствующие поля, битые записи не
  попадают в карточки.

### E. Поиск (раздел под этот проект)
Тесты на опечатки, **транслитерацию** (лат↔кир), диакритику, разные языки ввода;
устойчивость к пустому запросу и мусору. Функциональная корректность —
обязательно; производительность поиска на 10⁴–10⁵ синтетических игроков —
бенчмарком **локально/на моке** (без боевого Supabase).

### F. Компонентные + snapshot
Все React-компоненты: render, loading, error, empty, success, hover, click,
keyboard, mobile-вьюпорт, a11y-роль. Snapshot UI на стабильные компоненты.

### G. Интеграция (на моках, НЕ на боевом Supabase)
Цепочка Frontend → RPC → (мок PostgREST) → Telegram → кеш → storage. Контрактные
проверки формы ответа `pick_random_cards` и каждой ветки graceful-degrade при
`PGRST202`. Совместимость Frontend↔RPC — снапшотом схемы ответа (лёгкий contract,
без Pact/SaaS).

### H. Telegram Mini App (раздел под этот проект)
Инициализация WebApp, применение темы, парсинг и **валидация `initData`** (подпись
HMAC), авторизация, возврат в приложение, поведение вне Telegram (dev-фолбэк),
эмуляция клиентов iOS/Android (`src/shared/lib/telegram.ts`, `device.ts`).

### I. Локализация (раздел под этот проект)
`src/shared/i18n/locales/*` — есть 9 языков (`ru, en, fr, es, pt, zh, ja, ko,
ar`). Тесты: у всех локалей одинаковый набор ключей (нет пропавших/лишних), нет
пустых значений, интерполяции совпадают, RTL для `ar`, переключатель языка.

### J. E2E (Playwright)
Полные пользовательские сценарии: авторизация, поиск игроков, открытие карточки,
избранное, фильтрация, навигация, ошибки API, плохой интернет, офлайн, повторные
запросы, таймауты, Telegram WebApp. Один прогон — по возможности против **локально
поднятого supabase** (`supabase start`) или мок-сервера.

### K. BDD / Gherkin
`.feature` на игровой цикл (комната→команды→раунд→таймер→скоринг→победитель).
Playwright + `@cucumber/cucumber`. Язык фич — русский разрешён.

### L. Resilience / Chaos (на моках, без реального разрушения инфры)
Имитируй сбои: сон/таймаут Supabase, потеря сети, офлайн, невалидный/битый ответ
RPC, битые изображения карточек, ошибки Telegram. Проверь graceful-degrade и
ретраи рандомайзера. **Реальные Redis/PostgreSQL не роняем** — только моки.

### M. Accessibility
`axe` в компонентных/E2E-тестах, ARIA-роли, контраст, WCAG AA, keyboard-навигация.

### N. Security (по месту, не по шаблону)
OWASP-релевантное для этой архитектуры: **RLS-политики** Supabase
(`rls_lockdown.sql`) — аноним не читает лишнего/не пишет; **edge-функция
`tg-pay`** — проверка подписи/входа; **`initData`** — верификация HMAC, отказ на
подделке; секреты/`.env` не в репозитории; базовый CSP. `npm audit` на CVE в CI.
(Классические SQL-инъекции/CSRF-ручки — неприменимы, своего бэкенда нет.)

### O. Mutation testing — сердце затеи
**TS:** StrykerJS поверх Vitest. **Python:** `mutmut` по `scraper/`. Мутационный
отчёт — обязательная часть сдачи. Выжившие мутанты в ядре (переходы автомата,
скоринг, предикаты деградации, `canonical_key`, валидаторы данных) — закрываешь
осмысленным тестом, а не подстройкой.

---

## Гейты качества (жёсткие пороги в CI)

Расширь `.github/workflows/ci.yml`, **не ломая** текущие `typecheck`/`build`;
добавь job’ы: lint, unit, integration(mock), data-integrity, i18n, a11y,
security-audit, mutation, coverage, Playwright(артефакты).

- Покрытие на ядре (`features/game`, `shared/lib`, `shared/store`,
  `scraper/`): **line ≥ 90 %, branch ≥ 85 %**.
- **Mutation score ≥ 85 %** на ядре (цель — тянуть выше, но 100 % ветвей как
  самоцель не гнать).
- **0** упавших unit/property/data-integrity/BDD/a11y.
- Data-integrity — часть PR-гейта: битые данные не мержатся.

CI красный → PR не мержится. Точка.

---

## Умышленно исключено (и почему) — НЕ настраивать без явного запроса

- **Нагрузочные/стресс 100→10000 юзеров (k6/Locust) и fuzz «миллионы запросов»
  по боевому Supabase/API-Football.** Это free-tier, засыпает, лимиты (API-Football
  100 req/день). Такой прогон = самому положить прод и упереться в rate-limit,
  данные бессмысленны. Разрешено только на **локальном** stack или моке. Стоит
  захотеть боевую нагрузку — сначала спроси человека.
- **100 % Lines/Branches/Functions как самоцель.** Рождает мусорные тесты. Планка
  — 90 %+ на ядре + высокий mutation score.
- **Percy / Pact / SonarQube (SaaS).** Тяжело для масштаба проекта. Visual
  regression — Playwright + `pixelmatch` локально; contract — снапшот схемы RPC.
- **API-тесты «каждого endpoint» с SQL Injection / CSRF / Path Traversal.** Своего
  HTTP-API нет; поверхность — RLS + edge-функция + `initData` (см. Security).

---

## Порядок работы

1. Инфраструктура: Vitest + coverage + fast-check + Stryker + Playwright +
   `@testing-library` + axe + madge (TS); pytest + hypothesis + mutmut (Python).
   Скрипты `test`, `test:cov`, `test:mutation`, `test:e2e`; TS strict.
2. **Data-integrity первым** — красными зафиксировать два известных дефекта, затем
   остальные инварианты.
3. Юнит + property на ядро обеих поверхностей.
4. Компонентные/snapshot, i18n, Telegram, поиск, a11y.
5. Интеграция (мок) + BDD + E2E + resilience.
6. Security-проверки (RLS/tg-pay/initData/audit).
7. Mutation — добить выживших.
8. CI-гейты + QA-чеклист `docs/QA.md`.
9. По каждому дефекту: regression-тест → правка → зелёный → коммит.

## Definition of Done + финальный отчёт

Работа не завершена, пока не собран `REPORT.md` с разделами:
- найденные дефекты; внесённые исправления;
- покрытие (line/branch по модулям);
- mutation score (TS + Python) с приложенными отчётами;
- результаты производительности (локальные бенчи поиска);
- оценка безопасности (RLS/tg-pay/initData/audit);
- список оставшихся технических рисков.

Плюс `TESTING.md`: как гонять каждый слой и как читать мутационный отчёт.

Я твой код читать не буду. За него отвечает конвейер.
