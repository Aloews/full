# AlphaPulse — System Architecture Diagram

```text
                 User
                   │
                   ▼

          Next.js Frontend
                   │
                   ▼

             FastAPI API
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼

 Auth Service  Signal Service  Project Service
     │             │             │
     └─────────────┼─────────────┘
                   ▼

              PostgreSQL
                   │
                   ▼

                Redis

                   ▲
                   │

     ┌─────────────┼─────────────┐
     ▼             ▼             ▼

 GitHub      Reddit Worker    HN Worker
 Worker
```
