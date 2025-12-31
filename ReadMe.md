# Votes Information System - Legislative Data Analytics

Author: Igor Simões.

Hi! This is a quick code challenge for Quorum

Repository: [igoorsimoess/legislative-analytics](https://github.com/igoorsimoess/legislative-analytics)

Table of contents

- [App Planning](#app-planning)
  - [Functional Requirements](#functional-requirements)
  - [Non Functional Requirements](#non-functional-requirements)
  - [Data Model & Relationships](#data-model--relationships)
  - [Output Contracts](#output-contracts)
- [Tools/Frameworks](#toolsframeworks)
- [AI Use](#ai-use)
  - [Where AI was used?](#where-ai-was-used)
  - [Where AI was not used?](#where-ai-was-not-used)
- [App Walkthrough](#app-walkthrough)
  - [Run the Project](#run-the-project)
  - [Run the Tests](#run-the-tests)
  - [Observability](#observability)
  - [App architecture](#app-architecture)
  - [Future Enhancements](#future-enhancements)
  - [Security Concerns](#security-concerns)
  - [Challenges Encountered](#challenges-encountered)
  - [Principles](#principles)
  - [Time needed for project assemble (Average)](#time-needed-for-project-assemble-average)

---

## App Planning

### Functional Requirements

- **two reports** from four input datasets:
  - **Legislator Support/Opposition**: for every legislator, count how many bills they supported and opposed.
  - **Bill Support/Opposition**: for every bill, count how many legislators supported and opposed it, and include the sponsor's name.

- Voting rules (from the dataset):
  - `vote_type = 1` → **Supported**
  - `vote_type = 2` → **Opposed**
  - Any other vote_type is ignored  - This strategy accounts for future type of votes, like abstains

- A few edge cases -> explicitly supported and tested:
  - Missing `sponsor_id` ⇒ sponsor name = `"Unknown"`.
  - Sponsor id exists but not found in `legislators.csv` ⇒ sponsor name = `"Unknown"`.
  - Legislators with **0 votes** must still appear with 0 counts.
  - Bills with **no votes** must still appear with 0 counts.

### Non Functional Requirements

- **Architecture (layering)**:
  - Domain: model entities only here, no logic of voting
  - Repository: abstract interfaces + CSV implementations
  - Service: business logic -> O(N) because the aggregation is performed via dicts (Hashmaps)
  - Application: wiring + file IO

- **Performance Concerns**:
  - O(N) time where N is the number of `vote_results` rows
  - No nested loops. All joins done via hash maps:
    - `vote_id -> bill_id`
    - `legislator_id -> name`
    - `bill_id -> title/sponsor_id/counts`

- **Testing**:
  - Unit tests: service layer, repositories mocked/stubbed.
  - Integration tests: CSV repositories reading real files.
  - Edge tests: separately marked and executed explicitly by `run.sh`.

### Data Model & Relationships

Input files live in `data/`:

- `legislators.csv`
  - `id`, `name`
- `bills.csv`
  - `id`, `title`, `sponsor_id` (nullable)
- `votes.csv`
  - `id`, `bill_id`
- `vote_results.csv`
  - `id`, `legislator_id`, `vote_id`, `vote_type`

Relationships (joins):

- `vote_results.vote_id` → `votes.id`
- `votes.bill_id` → `bills.id`
- `bills.sponsor_id` → `legislators.id`

### Output Contracts

Outputs are written to `output/` by default:

1) `output/legislators_support_oppose.csv`

- columns:
  - `id`
  - `name`
  - `num_supported_bills`
  - `num_opposed_bills`

2) `output/bills_support_oppose.csv`

- columns:
  - `id`
  - `title`
  - `supporter_count`
  - `opposer_count`
  - `primary_sponsor` (**"Unknown"** if missing)

---

## 3. Security Layer - Defensive Data Ingestion -> Strict Schema Validation

I wanted to showcase concerns with security and reliability of the voting process and data so I spent a few more minutes planning a strategy of making sure the system could be trsuted.

So, in the scenario of an "Injection", where malformed data crashes the parser or skews results, we:

Fail fast and loud if the data violates the business rules (e.g., a duplicate vote ID or a vote from a non-existent legislator).
The system checks for two constraints:
- 1. Does vote.legislator_id exist in the legislators map?
- 2. Has this legislator_id already voted on this bill_id?

### Logging strategy (auditability without crashing)
A mature system will always allow us to debug without pain. That's why I took the route of logging every step. On production, we would link this to a reliable logging system so we could leverage all the capabilities (AI insights, better visualization, etc)

- All ingestion steps are logged for auditability:
  - **Entry**
  - **Validation Start**
  - **Validation Result** (OK / failure reason)
  - **Persistence** (emitting the record downstream)
  - **Exit** (summary counts)
- If a record fails validation, the pipeline **does not crash**; it logs a warning/error and **skips** the record.
- Implementation lives in `src/legislative_analytics/repositories/validating_vote_results.py` and is wired in the application entrypoint.

## Tools/Frameworks

- `uv` → dependency management + virtual env + task runner. I like uv over pip since I heard of it (: 
- `pytest` → testing
- `ruff` → linting 
- `mypy` → strict typing 

---

## AI Use

### Where AI was used?

→ Scaffolding and accelerating boilerplate writing (file structure + initial implementation).
→ Tests and edge cases were written to enforce the contractual behavior (0 count entities and unknown sponsors)

### Where AI was not used?

→ Any core decisions like: architecture, data relationships and algorithmic choices. All of them were done intentionally and reviewed manually.


---

## App Walkthrough

### Run the Project

#### Automatic - One command 

```bash
chmod +x ./run.sh
```


```bash
./run.sh
```

What this does:

1. Installs dependencies via `uv` (`uv sync --dev`)
2. Runs the app to generate output CSVs
3. Runs test suite (excluding edge tests)
4. Runs edge-case tests

- I ignored the `output/` folder is **intentionally ignored by git** (`.gitignore`) sothe repo keeps clean
- If `uv` is not installed, `run.sh` will detect it and prompt:
  - **The current project setup requires uv which is not installed. Install? Yes or No**

#### Manual

Install deps:

```bash
uv sync --dev
```

Run the app:

```bash
uv run python src/main.py --data-dir ./data --out-dir ./output
```

Optional:

- If you want to see all defensive ingestion steps (per-record validation logs), use:

```bash
uv run python src/main.py --data-dir ./data --out-dir ./output --log-level DEBUG
```

### Run the Tests

Run everything:

```bash
uv run pytest -v
```

Run only integration tests:

```bash
uv run pytest -m integration -v
```

Run only edge tests:

```bash
uv run pytest -m edge -v
```

### Observability

We would add in a prod environment:
- Structured logs (JSON) with input/output file paths and row counts processed
- Simple metrics:
  - number of vote_results rows processed
  - number of unknown sponsors encountered
  - processing duration

### App architecture

**Architecture layout**:

- `src/legislative_analytics/domain/`
  - dataclasses only (entities)
- `src/legislative_analytics/repositories/`
  - `interfaces.py` (Protocols)
  - `csv_repositories.py` 
- `src/legislative_analytics/services/`
  - `analytics_service.py` -> The actual logic
- `src/legislative_analytics/application/`
  - `main.py` dependency wiring + output writing

### Future Enhancements

- streaming support for extremely large CSVs:
  - chunked reading + incremental write
  - optional memory-bounded mode
- validation layer:
  - detect duplicated IDs
  - detect vote_results referencing missing votes/bills
- richer reporting:
  - counts per party / region (if present in expanded datasets)
  - bill pass/fail status

### Security Concerns

- In a prod env, we should treat CSVs as untrusted:
  - validate schema and numeric ranges
  - handle malformed rows with a dead-letter output

### Challenges Encountered

- Keeping the architecture clean (strict layering) while still making the pipeline production-minded (tests + defensive ingestion + audit logs) without over-engineering.

### Principles

- **Modularity**: IO (repositories) separated from business logic (services).
- **Determinism**: outputs sorted by entity id.
- **Scalability**: single-pass O(N) aggregation over the largest dataset.
- **Testability**: repository interfaces allow pure unit tests for aggregation logic.

### Time needed for project assemble (Average)

- Planning the architecture + interfaces: ~30–45min
- Implementation and review: ~60–90min
- Tests + edge cases: ~45–60min
- Documentation: ~30–45min

---

## Questions

### 1) Time complexity and Tradeoffs.

- **Time complexity**: \(O(L + B + V + R)\), where:
  - \(L\) = legislators
  - \(B\) = bills
  - \(V\) = votes
  - \(R\) = vote_results (the dominant var)
- **Why**:
  - Build hash maps once (`vote_id -> bill_id`, `legislator_id -> name`, `bill_id -> (counts, sponsor_id, title)`).
  - Single pass over `vote_results.csv` to aggregate counts (no nested loops).
- **Tradeoffs**:
  - Uses extra memory for hash maps (O(L + B + V)) to guarantee O(R) joins. This way we ensure the output is correct instead of micro optimizing it

### 2) Future columns that might be requested

- We would just need to add a new **domain entities/fields** as dataclasses as needed
- Then extend the repositories to parse new columns
- Add new service methods (or new DTOs) for any additional report types
An enhancement:
- If many outputs are requested, I would introduce a small **CSV writer abstraction** in the application layer. It would keep the service layer returning typed DTOs and let writers map DTOs to CSV schemas.

### 3) How would you change your solution if instead of receiving CSVs of data, you were given a list of legislators or bills that you should generate a CSV for?

Basically I would keep the same service logic, but introduce a **filter set** (IDs) so we only compute/write the requested subset. That is:
  I would implement a **filtered repositories** wrappers logic so the service only ever sees the requested subset. This would keep the pipeline closer to O(N) over the relevant data

### 4) How long did you spend working on the assignment?

Basically I spent more time planning and reviewing then implementing. We're on AI Era, yes, but we should take care of the code being generated. Following good patterns is the key for a productive but still reliable Software Engineering Process.
- **Architecture**: ~`~45min` -> First, after reviewing and deep understanding the problem, I've defined the design pattern suited for the challenge requirement, read a quick article to confirm my choice and thought about the security additional feature.
- **Implementation**: `~30 min` Created a few prompts, validated the code and made a few corrections
- **Test Suite**: ~`~30 min` Tests are how Software Engineers goes to bed peacefully. I've tried to cover the happy paths and also some edge cases that could appear.
- **Documentation**: ~`~30 min` Tests are how Software Engineers goes to bed peacefully. I've tried to cover the happy paths and also some edge cases that could appear.
