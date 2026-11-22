# Alchemy Crafter — API Reference

**Base URL:** `http://localhost:8000`  
**Format:** JSON  
**Auth:** None (MVP)

---

## Endpoints

### `GET /health`

Liveness probe.

**Response `200`**

```json
{ "status": "ok" }
```

---

### `POST /combine`

Combine two elements. Runs full pipeline: Redis → Postgres → Ollama.

#### Request

```json
{
  "a": "fire",
  "b": "water"
}
```

| Field | Type   | Rules                                               |
| ----- | ------ | --------------------------------------------------- |
| `a`   | string | Non-empty, ≤30 chars, alphanumeric, spaces, hyphens |
| `b`   | string | Non-empty, ≤30 chars, alphanumeric, spaces, hyphens |

Order-independent — `fire + water` == `water + fire`.

Names are trimmed and lowercased.

**Response `200`**

```json
{
  "result": "steam",
  "is_new": true,
  "source": "ai",
  "elapsed_ms": 843.2
}
```

| Field        | Type    | Description                                     |
| ------------ | ------- | ----------------------------------------------- |
| `result`     | string  | Resulting element name                          |
| `is_new`     | boolean | `true` if first time this recipe was discovered |
| `source`     | string  | `"cache"` · `"db"` · `"ai"`                     |
| `elapsed_ms` | float   | Total pipeline time in milliseconds             |

**Response `422`** — invalid input (schema errors return FastAPI's list-shaped `detail`)

```json
{ "detail": "Elements cannot be the same" }
```

**Response `404`** — unknown element

```json
{ "detail": "Unknown element(s): steam. Discover them first." }
```

An input element is not discovered yet. `combine()` raises it, so the CLI refuses too.

**Response `503`** — another request held this pair's lock for over 5 s

```json
{ "detail": "Recipe generation in progress, try again shortly" }
```

**Response `500`** — pipeline failure (DB down, Ollama timeout, etc.)

```json
{ "detail": "Combine failed: connection refused" }
```

#### Performance targets

| Source  | Target   |
| ------- | -------- |
| `cache` | < 50ms   |
| `db`    | < 150ms  |
| `ai`    | < 2000ms |

---

### `GET /elements`

All known elements.

**Response `200`**

```json
[
  { "name": "air" },
  { "name": "earth" },
  { "name": "fire" },
  { "name": "steam" },
  { "name": "water" }
]
```

Includes base elements (fire, water, earth, air) + all discovered elements.

**Response `500`** — DB unreachable

```json
{ "detail": "db down" }
```

---

### `GET /recipes`

All known recipes.

**Response `200`**

```json
[
  { "element_a": "air", "element_b": "fire", "result": "smoke" },
  { "element_a": "earth", "element_b": "water", "result": "mud" },
  { "element_a": "fire", "element_b": "water", "result": "steam" }
]
```

`element_a` is always alphabetically ≤ `element_b` (inputs are sorted before storage).

**Response `500`** — DB unreachable

```json
{ "detail": "db down" }
```

---

## Interactive Docs

Swagger UI auto-generated at runtime:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

## Quick Start

```bash
# Start services
make up

# Start API server
make serve

# Combine elements
curl -s -X POST http://localhost:8000/combine \
  -H "Content-Type: application/json" \
  -d '{"a": "fire", "b": "water"}' | jq

# List all elements
curl -s http://localhost:8000/elements | jq

# List all recipes
curl -s http://localhost:8000/recipes | jq
```

---

## Error Reference

| Status | Cause                                                          |
| ------ | -------------------------------------------------------------- |
| `422`  | Invalid input — empty, too long, same element twice, bad chars |
| `404`  | Element not discovered yet                                     |
| `503`  | Pair lock held over 5 s by another request                     |
| `500`  | DB unreachable, Ollama timeout, unexpected pipeline failure    |
