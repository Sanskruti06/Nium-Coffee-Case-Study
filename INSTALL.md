# Setup & Run

Minimal instructions for **macOS** and **Windows**. Pick your OS, run the steps in order.

You need three things installed: **Python 3.12**, **PostgreSQL**, and this project's Python packages.

---

## macOS

```bash
# 1. Install Python + Postgres (Homebrew)
brew install python@3.12 postgresql@16
brew services start postgresql@16
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc

# 2. Create the database
createdb coffee_case_study

# 3. Set up the project (run from the project folder)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 4. Run it
python pipeline/run_pipeline.py
streamlit run dashboard/app.py

# 5. Make the dump for submission
pg_dump --no-owner --no-privileges coffee_case_study > dump/coffee_case_study_dump.sql
```

No Homebrew yet? Install it first:
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

---

## Windows

Install these two first (just click through the installers):

- **Python 3.12** — https://www.python.org/downloads/ — tick **"Add python.exe to PATH"** during install.
- **PostgreSQL** — https://www.postgresql.org/download/windows/ — remember the password you set for the
  `postgres` user, and let it install **pgAdmin** too. Accept the default port `5432`.

Then open **PowerShell** in the project folder:

```powershell
# 1. Create the database (enter the postgres password when asked)
& "C:\Program Files\PostgreSQL\16\bin\createdb.exe" -U postgres coffee_case_study

# 2. Set up the project
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env

# 3. Edit .env so it has your postgres user + password, e.g.:
#    DATABASE_URL=postgresql+psycopg2://postgres:YOURPASSWORD@localhost:5432/coffee_case_study

# 4. Run it
python pipeline\run_pipeline.py
streamlit run dashboard\app.py

# 5. Make the dump for submission
& "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" -U postgres --no-owner --no-privileges coffee_case_study > dump\coffee_case_study_dump.sql
```

If `createdb`/`pg_dump` aren't found, use the full path shown above (adjust `16` to your version), or add
`C:\Program Files\PostgreSQL\16\bin` to your PATH.

---

## Restoring the dump (for a reviewer)

```bash
# macOS
createdb coffee_review && psql coffee_review -f dump/coffee_case_study_dump.sql
```
```powershell
# Windows
& "C:\Program Files\PostgreSQL\16\bin\createdb.exe" -U postgres coffee_review
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres coffee_review -f dump\coffee_case_study_dump.sql
```

---

## If something breaks

| Problem | Fix |
| --- | --- |
| `psql`/`createdb` not found | Use the full path (Windows) or re-run the PATH line (macOS). |
| `could not connect to server` | Start Postgres: `brew services start postgresql@16` (Mac); check the service is running in Services (Windows). |
| `password authentication failed` | Put the right user/password in `.env`'s `DATABASE_URL`. |
| `database ... does not exist` | Run the `createdb coffee_case_study` step. |
| pip build errors | Make sure you're on **Python 3.12**, not a newer version. |
| Dashboard: "Could not read analytics tables" | Run `python pipeline/run_pipeline.py` first. |
