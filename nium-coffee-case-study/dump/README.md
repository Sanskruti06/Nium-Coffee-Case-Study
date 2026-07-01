# Database dump

Generate the dump **after** running the pipeline (`python pipeline/run_pipeline.py`):

```bash
pg_dump --no-owner --no-privileges coffee_case_study > dump/coffee_case_study_dump.sql
```

Restore it against a fresh PostgreSQL instance with one command:

```bash
createdb coffee_review && psql coffee_review -f dump/coffee_case_study_dump.sql
```

The dump contains the `staging`, `core`, and `analytics` schemas and all their tables.
This file is generated on the machine that runs Postgres; it is not committed empty.
