# SQLGenie — AI SQL Assistant SaaS

## Project Goal

Build a production-grade SaaS application where users upload SQL schemas and ask natural language questions to generate and execute SQL safely.

Example:

User uploads:

CREATE TABLE users(
 id INT,
 age INT
);

User asks:

"What is average age?"

System returns:

Generated SQL:

SELECT AVG(age)
FROM users;

Answer:
32.4

---

# Constraints

Developer:

- Undergraduate
- Local GPU:
    GTX 1650

Deployment:

- Must be FREE

Training:

- Free Colab initially

Must prioritize:

1. Deployable product
2. Reliability
3. Testing
4. Documentation
5. Fine tuning later

NOT:

1. Chasing SOTA accuracy
2. Heavy GPU requirements

---

# Final Architecture

User

↓

Frontend (Next.js)

↓

FastAPI Backend

↓

Upload schema.sql

↓

Schema Parser

↓

Session Store

↓

Prompt Builder

↓

LLM

↓

SQL Validator

↓

Execution Engine

↓

Return SQL + Results

↓

Frontend UI

---

# Tech Stack

Frontend:

- Next.js
- Tailwind
- TypeScript

Backend:

- FastAPI
- Python 3.10+

Database:

- SQLite initially
- PostgreSQL support later

ML:

- Transformers
- PEFT
- QLoRA
- Qwen2.5-Coder 1.5B (later)

Deployment:

Frontend:

Vercel

Backend:

HF Spaces / Render

Testing:

pytest

Docs:

Markdown

---

# Folder Structure

Create:

sqlgenie/

frontend/

backend/
    api/
    services/
    validators/
    execution/
    models/

tests/

docs/

data/

notebooks/

README.md

requirements.txt

Dockerfile

---

# TASK 1

Initialize repository

Need:

Git

README

requirements

Initial commits

Expected:

Working project skeleton

---

# TASK 2

Build FastAPI server

Need:

Create:

backend/main.py

Endpoints:

GET /health

Return:

{
 "status":"ok"
}

Test:

localhost:8000/health

Expected:

200 OK

---

# TASK 3

Implement schema upload API

Create:

POST:

/upload-schema

Accept:

.sql file

Need:

Use:

UploadFile

Store:

Temporary session

Response:

{
 session_id,
 parsed_schema
}

Test:

Upload example schema

Expected:

Parsed JSON

---

# TASK 4

Implement schema parser

File:

backend/services/schema_parser.py

Need:

Parse:

CREATE TABLE

Columns

Types

Ignore:

PRIMARY KEY

FOREIGN KEY

Constraints

Output:

{
 table:
 columns:
}

Test:

Complex schemas

Expected:

Correct parsing

---

# TASK 5

Build session store

Need:

Store:

session_id

parsed_schema

Temporary memory

Expiration:

15 mins

Implement:

session_store.py

Expected:

Multiple users isolated

---

# TASK 6

Prompt builder

Input:

schema

question

Output:

LLM prompt

Rules:

Only generate:

SELECT

Reject:

DROP

DELETE

UPDATE

Expected:

Structured prompt

---

# TASK 7

Query API

Endpoint:

POST /query

Input:

{
 session,
 question
}

Pipeline:

retrieve schema

↓

build prompt

↓

return prompt

Expected:

Prompt generation works

---

# TASK 8

Integrate pretrained model

Use:

TinyLlama

OR

Qwen2.5-Coder

Need:

Generate SQL

Pipeline:

Prompt

↓

Model

↓

SQL

Expected:

Simple SQL generation

---

# TASK 9

SQL validator

Create:

validator.py

Need:

Allow:

SELECT

COUNT

AVG

GROUP BY

Reject:

DROP

DELETE

INSERT

UPDATE

Expected:

Unsafe SQL blocked

---

# TASK 10

Execution engine

Need:

Execute generated SQL

Initially:

SQLite

Input:

Generated SQL

Output:

Results

Expected:

Return answer

---

# TASK 11

Combine full backend pipeline

User Question

↓

Prompt

↓

LLM

↓

SQL

↓

Validate

↓

Execute

↓

Return

Need:

Single API:

POST /query

Response:

{
 generated_sql,
 answer
}

---

# TASK 12

Testing

Need:

pytest

Files:

test_parser.py

test_api.py

test_validator.py

test_execution.py

Target:

>70%

---

# TASK 13

Frontend

Build:

Upload schema page

Ask question page

Result display

Need:

Show:

Generated SQL

Answer

Loading states

Errors

---

# TASK 14

Connect frontend → backend

Need:

Fetch APIs

Handle sessions

Store session ids

Expected:

End-to-end flow

---

# TASK 15

Deploy backend

Use:

HF Spaces

OR

Render

Need:

Public URL

Expected:

Accessible API

---

# TASK 16

Deploy frontend

Use:

Vercel

Need:

Connect deployed backend

Expected:

Working SaaS

---

# TASK 17

Improve UI

Need:

Modern dashboard

Sidebar

History

Session management

---

# TASK 18

Add model fine tuning

ONLY AFTER PRODUCT WORKS

Use:

Spider dataset

Train:

QLoRA

Model:

Qwen2.5-Coder 1.5B

Goal:

Improve SQL quality

NOT required initially

---

# TASK 19

Documentation

Need:

README:

Architecture

Setup

Training

Deployment

Screenshots

API docs

Future work

---

# TASK 20

Final polishing

Need:

Error handling

Logging

Monitoring

Rate limiting

Session expiry

Security

---

# Coding Rules

ALWAYS:

- Type hints
- Docstrings
- Tests
- Modular code
- Environment variables
- .env usage
- Error handling

NEVER:

- Hardcode paths
- Hardcode secrets
- Skip tests
- Mix business logic into routes

---

# Success Criteria

Product deployed publicly

Users can:

1. Upload schema
2. Ask question
3. Get SQL
4. Get answer

with:

tests

docs

deployment

clean architecture
