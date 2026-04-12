# Project Setup Notes

## Commands Run in This Project

### 1. Git Initialization & Commits
```bash
git init
git add .
git commit -m "Initial commit"
git commit -m "upload the project file"
git commit -m "removed spsl.zip documentation files from git"
git commit -m "added gitignore file and custom_addons folder"
git commit -m "added docker compose for redis, postgresql and pgadmin"
git commit -m "added odoo19 fresh codes. (untouched)"
```
**Why:** Project version control setup and importing Odoo 19 source code.

---

### 2. Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
**Why:** Isolate Odoo 19 dependencies from system Python. The `.venv` directory contains installed packages like `cbor2`, `chardetect`, `docutils`, `num2words`, etc.

---

### 3. Docker Compose Setup
```bash
docker-compose up -d
```
**Why:** Start infrastructure services:

| Service    | Image            | Port | Purpose               |
|------------|------------------|------|-----------------------|
| PostgreSQL | `postgres:15`    | 5432 | Odoo database (SPSL)  |
| pgAdmin 4  | `dpage/pgadmin4` | 5050 | Database management   |
| Redis 7    | `redis:7`        | 6379 | Caching/sessions      |

---

### 4. Odoo Configuration
Created `odoo.conf` with:
- Database: `SPSL` on `localhost:5432`
- User: `odoo19` / Password: `odoo19`
- HTTP Port: `8019`, Longpolling: `8079`
- Addons paths configured

---

### 5. To Run Odoo (not yet run)
```bash
source .venv/bin/activate
python odoo-bin -c odoo.conf
```

---

## Project Structure Created
```
smart_printing_service_limited/
├── .venv/          # Python virtual environment
├── addons/         # Odoo 19 core addons
├── custom_addons/  # Custom module development
├── odoo/           # Odoo 19 source code
├── docker-compose.yml
├── odoo.conf
└── requirements.txt
```
python odoo-bin -c odoo.conf -d SPSL -u spsl_core

kill server: kill $(lsof -t -i :8019)



finished upto 4.5.2
