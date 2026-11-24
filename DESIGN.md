# Company Recommendation System

A pipeline that ingests company events from RabbitMQ, normalizes and embeds them, stores them in Postgres + pgvector, and serves company lookups and similar-company recommendations through a REST API with a demo page.

---

## 1. Architecture

### Ingestion flow

```
RabbitMQ (company-events)
        │
        ▼
   consumer.py ──► normalization.py ──► db.py ──► Postgres + pgvector
                   (validate,            (insert /
                    standardize,          update)
                    embed)
```

### Query flow

```
index.html ──► api.py ──► service.py ──► db.py ──► Postgres + pgvector
```

---

## 2. Components

| File | Responsibility |
|------|----------------|
| `consumer.py` | Reads one message at a time from the `company-events` queue, then validates, normalizes and embeds it, and writes it into Postgres. |
| `normalization.py` | Validates that every message follows the standard format. Also handles description embedding and description hashing (so an identical description is not embedded again). |
| `db.py` | Handles all database operations (insert, update, get). Uses `COALESCE` so that on update, any attribute that is `NULL` keeps its previous value. |
| `service.py` | The layer between the API and the database. Acts as the controller that handles all input coming from the API. |
| `api.py` | Exposes `GET /company/{id}` and `GET /company/{id}/similar`. |
| `index.html` | Demo page that calls the API. |
| `dataVerify.ipynb` | Notebook to visualize the data structure and check for missing and duplicate values. |

### Normalization rules

A message is **rejected and skipped** if any of the following is true:

- it does not contain the `data` attribute
- it has no registration number
- it has no `updateAt`

Other behaviour:

- **Embedding:** descriptions are embedded with `paraphrase-multilingual-MiniLM-L12-v2`.
- **Hashing:** each description is hashed, so a duplicate description is looked up by hash and its existing result reused instead of being embedded again.

---

## 3. Notes

- Model: `paraphrase-multilingual-MiniLM-L12-v2`, chosen to handle multilingual company descriptions.

## 4. Assumptions

1. The registration number follows the format `SYN-XXXXXX`, where `XXXXXX` is 6 digits.
2. A timestamp with no timezone is treated as UTC.

---

## 5. Remaining Work

1. **More testing** is still needed.
2. **Improve similarity search.** Matching on `natureofcompany` alone is not enough: it returns companies in the same category but in different locations. Adding **location** as a signal should give better retrieval results.

---

## 6. Scaling to 10x Volume

1. **Reduce embedding cost.** The description hash already lets duplicate descriptions be resolved with an O(1) lookup instead of re-embedding. This cuts time in the slowest stage of the pipeline.
2. **Add more consumers running in parallel.** This requires async handling and locking so that two workers never process the same company at the same time.
3. **Memory management.** Large volumes of data need careful resource allocation, so memory usage should be planned for and managed efficiently.

---

## 7. Tools Used

- **Claude Code**: coding suggestions, debugging, designing the schedule, and writing the demo page (`index.html`).
- **Jupyter + pandas**: exploring the data feed.
- **Docker, uv, just, pytest, FastAPI**: environment, task running, testing and API.

## 8. Time Spent

**6h 6m**, overtime 6 minutes because trying fixing the issue of the consumer pushing the message.

Tracked with Toggl, 22–24 November 2026 ([full report](Toggl_Summary_Report.pdf)).