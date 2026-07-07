# Data Types: Structured, Semi-Structured & Unstructured

## Learning Objectives

- Define structured, semi-structured, and unstructured data and give real examples of each
- Explain schema-on-write vs. schema-on-read and why it matters
- Compare the three types on storage, query approach, flexibility, and cost
- Choose the right data type category for a given scenario

## Why This Matters

Everything you touch this week fits somewhere on the structured ↔ unstructured spectrum, and the *type* dictates the tools:

- **Structured** data (tables) drives BigQuery and the dimensional models you'll build on Days 4–5.
- **Semi-structured** data (JSON) is what your FastAPI endpoints emit and consume (Day 1, and note 204 today).
- **Unstructured** data (docs, images) is why data lakes and object storage exist.

Roughly **80–90% of the world's data is semi- or unstructured**, yet analytics still wants tabular structure. A huge part of the data engineer's job is *moving data leftward* on this spectrum — turning messy JSON and documents into clean tables. Knowing the categories tells you how much work that will be.

## Concept Explanation

### The spectrum

```
   STRUCTURED           SEMI-STRUCTURED         UNSTRUCTURED
       |                       |                      |
+------+------+         +------+------+        +------+------+
|   Tables    |         |    JSON     |        |   Images    |
|  Fixed      |         |    XML      |        |   Video     |
|  schema     |         |    YAML     |        |   Free text |
| (CSV, RDBMS)|         | (Parquet*)  |        |   Audio     |
+-------------+         +-------------+        +-------------+
       |                       |                      |
   ~10-20%                 ~10-15%                ~70-80%
   of data                 of data                of data
  schema-on-write        self-describing         no schema
```
\* Parquet is a *file format* that stores structured/tabular data efficiently — see note 203.

### Structured data

Data that conforms to a **fixed, predefined schema**: every record has the same fields, each field has a declared type, and it maps cleanly into rows and columns.

- **Examples:** relational tables (PostgreSQL, MySQL), CSV exports, spreadsheets, BigQuery tables.
- **Schema-on-write:** the schema is enforced *when you insert*. A bad row is rejected up front.

```sql
CREATE TABLE customers (
    customer_id   INT PRIMARY KEY,
    email         VARCHAR(100) UNIQUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Strengths:** trivial to query (SQL), strong consistency, great compression, mature tooling.
**Weaknesses:** rigid — changing the schema means a migration; can't natively represent nesting/hierarchy.

### Semi-structured data

Data that has **organizational markers (keys, tags, nesting) but no rigid table schema**. Records can vary field-to-field and can nest arbitrarily. It is **self-describing** — the keys travel with the values.

- **Examples:** JSON (API payloads), XML, YAML (config), log lines, NoSQL documents.
- **Schema-on-read:** you store it as-is and apply structure *when you read it*. Ingestion is fast; validation moves to the consumer.

```json
{
  "customer_id": 12345,
  "name": { "first": "Ada", "last": "Lovelace" },
  "emails": ["ada@example.com", "ada@work.com"],
  "orders": [ { "id": "O1", "amount": 99.99 } ]
}
```

Notice what a table *can't* easily do: `name` is nested, `emails` is a list, and `orders` is a list of objects. Two records can have different keys and both be valid.

**Strengths:** flexible, evolves without migrations, handles nesting/variety, native to the web.
**Weaknesses:** no structural guarantees — the consumer must handle missing/extra fields; verbose (keys repeat every record); slower to scan for analytics.

### Unstructured data

Data with **no predefined model at all** — you can't slot it into rows and columns without heavy processing.

- **Examples:** free-text documents, emails, PDFs, images, audio, video, sensor blobs.
- Typically stored as **files/blobs** in object storage (S3, GCS, Azure Blob).

**Strengths:** preserves the original artifact; cheap bulk storage; the richest raw information.
**Weaknesses:** you can't SQL-query it directly. Extracting value needs specialized processing — NLP for text, computer vision/OCR for images, speech-to-text for audio — often producing *structured metadata* that you then load into a table.

```
Raw PDF  --OCR/NLP-->  { "vendor": "Acme", "total": 5000, "date": "2026-01-15" }  --load-->  invoices table
unstructured                        semi-structured                                          structured
```

### Comparison table

| Aspect | Structured | Semi-Structured | Unstructured |
|--------|------------|-----------------|--------------|
| Schema | Fixed, predefined | Flexible, self-describing | None |
| When schema applies | On **write** | On **read** | N/A (extract later) |
| Shape | Rows & columns | Nested / hierarchical | Files / blobs |
| Examples | CSV, RDBMS, Parquet tables | JSON, XML, YAML, logs | Images, video, PDFs, text |
| Query with | SQL | JSON/XPath functions, parse then SQL | Full-text / AI-ML |
| Storage | RDBMS, data warehouse | Doc store, object store + query engine | Object store |
| Flexibility | Low (migrations) | High | N/A |
| Analytics-ready | Yes | After flattening | Only after extraction |
| Share of enterprise data | ~10-20% | ~10-15% | ~70-80% |

### Choosing a category

| Choose… | When… |
|---------|-------|
| **Structured** | schema is stable, you need SQL + strong consistency, transactional integrity matters |
| **Semi-structured** | schema evolves often, data is nested/varied, you're integrating APIs or diverse sources |
| **Unstructured** | the data *is* inherently a document/media file, or you must preserve the original artifact |

Real pipelines mix all three — the modern **lakehouse** pattern lands raw (unstructured/semi) data in a lake, enriches it into semi-structured records, and curates clean structured tables for analytics.

## Code Example

Programmatically sensing which category a payload falls into:

```python
import json

def classify(value, source_hint: str = "") -> str:
    """Rough heuristic: structured / semi-structured / unstructured."""
    hint = source_hint.lower()
    if any(k in hint for k in ("csv", "sql", "table", "parquet")):
        return "structured"
    if any(k in hint for k in ("json", "xml", "yaml")):
        return "semi-structured"
    if any(k in hint for k in ("pdf", "jpg", "png", "mp4", "wav", "txt")):
        return "unstructured"

    # No hint: inspect the value itself.
    if isinstance(value, list) and value and all(isinstance(r, dict) for r in value):
        keys = set(value[0])
        same_keys = all(set(r) == keys for r in value)
        flat = all(not isinstance(v, (dict, list)) for r in value for v in r.values())
        return "structured" if (same_keys and flat) else "semi-structured"
    if isinstance(value, (dict, list)):
        return "semi-structured"
    if isinstance(value, (bytes, str)):
        try:
            json.loads(value)            # a JSON string is semi-structured
            return "semi-structured"
        except (ValueError, TypeError):
            return "unstructured"        # raw text / bytes
    return "unstructured"


# Structured: list of flat dicts, identical keys
print(classify([{"id": 1, "amt": 9.9}, {"id": 2, "amt": 5.0}]))   # structured

# Semi-structured: nested
print(classify({"id": 1, "name": {"first": "Ada"}, "tags": ["x"]}))  # semi-structured

# Unstructured: free text
print(classify("The invoice total is about five thousand dollars."))  # unstructured
```

## Key Takeaways

- **Structured** = fixed schema, rows/columns, schema-on-write, query with SQL (~10-20% of data).
- **Semi-structured** = self-describing keys + nesting, flexible, schema-on-read, JSON is king (~10-15%).
- **Unstructured** = no schema, files/blobs, needs AI/ML extraction, the majority of all data (~70-80%).
- **Schema-on-write** rejects bad data early; **schema-on-read** ingests fast but pushes validation to the consumer.
- Much of data engineering is **shifting data leftward** — turning messy semi/unstructured input into clean structured tables.
- Real architectures (lakehouse) deliberately use all three at different stages.

## Resources

- Structured vs. unstructured data (IBM): <https://www.ibm.com/think/topics/structured-vs-unstructured-data>
- JSON specification: <https://www.json.org/>
- Schema-on-read vs schema-on-write: <https://www.snowflake.com/guides/schema-read-vs-schema-write/>
- Cross-reference: `notes/203-file-formats-csv-json-parquet.md` (how these types are stored on disk)
