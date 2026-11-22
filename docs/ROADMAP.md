# 🧪 Roadmap and Product Requirements

## Product: Alchemy Crafter (AI-Driven Crafting Game)

---

## 1. Objective

Build a **single-player alchemy game** where users combine elements to discover new ones.

* Infinite combinations powered by **Ollama**
* Fast responses using **Redis caching**
* Persistent world using **PostgreSQL**

---

## 2. Core Concept

Users start with base elements:

```text
fire, water, earth, air
```

They combine:

```text
fire + water → steam
```

System:

* Checks cache (Redis)
* Falls back to DB (Postgres)
* Generates via Ollama if unknown
* Stores result permanently

---

## 3. Target User

* Developers / hackers (your audience)
* Casual players who like discovery games
* People who enjoy experimentation

---

## 4. Core Features

### 4.1 Element Combination

* Input: 2 elements
* Output: 1 result element
* Order-independent (`A+B == B+A`)

---

### 4.2 Discovery System

* Track discovered elements
* Show:

  * “New discovery” animation/text
* Maintain collection

---

### 4.3 AI Recipe Generation

* Use Ollama when:

  * Combination not found in Redis/Postgres
* Generate:

  * Logical OR creative result
* Must follow validation rules

---

### 4.4 Caching Layer (Redis)

* Cache recipes for instant reuse
* Store recent context for AI prompts

---

### 4.5 Persistence (Postgres)

* Store:

  * All recipes
  * All elements

---

### 4.6 Feedback System

* Success → show result
* Failure → meaningful message
* AI fallback for repeated failures

---

## 5. ⚙️ System Architecture

```text
Client (CLI / API)
        ↓
    Redis (cache + context)
        ↓
   PostgreSQL (truth)
        ↓
     Ollama (AI)
```

---

## 6. 🗄️ Data Model

### Elements Table

```sql
id SERIAL PRIMARY KEY
name TEXT UNIQUE
created_at TIMESTAMP
```

---

### Recipes Table

```sql
id SERIAL PRIMARY KEY
element_a TEXT
element_b TEXT
result TEXT
UNIQUE(element_a, element_b)
```

---

### Redis Keys

```text
recipe:<a>:<b>           → result
context:global           → recent elements list
player:<id>:discovered   → set
fail:<a>:<b>             → count
```

---

## 7. 🔄 Core Flow

### Combine Elements

```text
1. Normalize input (sort)
2. Check Redis
3. If miss → check Postgres
4. If miss → call Ollama
5. Validate result
6. Store in Postgres + Redis
7. Return result
```

---

## 8. 🤖 AI Integration

### Prompt Requirements

* Deterministic format
* Single result only
* Context-aware (via Redis)

---

### Example Prompt

```text
You are an alchemy engine.

Known elements:
{recent_elements}

Rules:
- Combine into ONE element
- Be logical or creative
- No repetition

Input:
fire + water

Output:
result: steam
```

---

## 9. 🛡️ Validation Rules

Reject if:

* Same as input
* Too long (>30 chars)
* Contains invalid characters
* Already exists (optional dedupe logic)

---

## 10. ⚡ Performance Requirements

* Response time:

  * Cached: < 50ms
  * DB: < 150ms
  * AI: < 2s
* Redis hit ratio target: > 70%

---

## 11. 🎮 Game Mechanics

## Progression

* Unlock elements gradually
* Encourage chaining

---

## Optional Features (Phase 2)

* Hint system
* Achievements
* Daily challenges
* AI personality modes 😄

---

## 12. 🧪 MVP Scope (Keep This Tight)

✅ CLI interface
✅ Combine elements
✅ Redis cache
✅ Postgres storage
✅ Ollama integration
✅ Basic validation

❌ No UI
❌ No auth
❌ No multiplayer

---

## 13. 🚀 API Design (Optional)

### POST `/combine`

```json
{
  "a": "fire",
  "b": "water"
}
```

### Response

```json
{
  "result": "steam",
  "is_new": true
}
```

---

## 14. 📊 Success Metrics

* Avg combinations per session
* % of new discoveries
* Redis cache hit rate
* AI generation frequency

---

## 15. ⚠️ Risks & Mitigation

### Risk: AI randomness

👉 Fix:

* strict prompt
* validation layer

---

### Risk: Infinite nonsense elements

👉 Fix:

* seed base recipes
* bias with context

---

### Risk: Slow responses

👉 Fix:

* Redis caching
* async calls

---

## 16. 🧬 Future Roadmap

### V0.2

* Web UI (FastAPI + HTMX)
* Drag & drop crafting

### V0.3

* Multiplayer discovery race

### V0.4

* Fully AI-generated world (elements + lore)

---

## 17. 🏗️ Tech Stack

* Python (FastAPI or CLI)
* PostgreSQL
* Redis
* Ollama (local LLM)
* Optional: SQLAlchemy

---

## 18. 🔥 Definition of Done

* User can combine any 2 elements
* New elements are generated or fetched
* Results persist across sessions
* System remains consistent and fast

---

## 19. Sprint List

| Sprint | Goal                                                       | Docs                                                 |
| ------ | ---------------------------------------------------------- | ---------------------------------------------------- |
| S1     | Core MVP and infrastructure                                | [PRD](sprints/S1/PRD.md), [TODO](sprints/S1/TODO.md) |
| S2     | Gameplay loop, reliability, quality gate                   | [PRD](sprints/S2/PRD.md), [TODO](sprints/S2/TODO.md) |
| S3     | Candidates: Web UI, auth, multiplayer, achievements, hints | not planned yet                                      |
