# Greenback Finance Intelligence Platform

**CBN Resource Planner Edition** | v2.0

An enterprise-grade financial analytics platform combining interactive resource planning, AI-powered data analysis, and comprehensive OpEx intelligence — built for finance teams that demand precision.

---

## Features

- **CBN Resource Planner** — Interactive mountain chart (stacked area) with priority-based project stacking, demand vs. capacity analysis, per-country cost controls, and real-time gap detection
- **AI ChatBot** — Natural language financial queries powered by an orchestration agent pipeline (Intent → SQL/RAG/Chat), with auto-generated Plotly charts and executive-quality analysis
- **Financial Analytics** — Trend tracking, department rollups, resource allocation views, geo/org analytics, and a custom plotting sandbox
- **Data Ingestion** — CSV and XLSX parsers for BPAFG demand files and Priority Template files with automatic month normalization and wide-to-long data transformation
- **Greenback UI Theme** — Professional dollar-bill green color scheme with IBM Plex typography, designed for financial dashboard readability

---

## Prerequisites

- **Python 3.12+**
- **PostgreSQL 15+** with pgvector extension (or SQLite as fallback for local dev)
- **pip** package manager

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd finance_dashbord
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows
python --version             # Verify Python 3.12+
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install QGenie SDK (Internal)

```bash
pip install qgenie-sdk[all] qgenie-sdk-tools \
  -i https://devpi.qualcomm.com/qcom/dev/+simple \
  --trusted-host devpi.qualcomm.com
```

### 5. Configure Environment

The project uses two configuration layers:

- **`config/config.yaml`** — All application settings (paths, models, endpoints, DB host/port, agent tuning, etc.)
- **`.env`** — Only secrets and credentials (API keys, database passwords)

**Step A:** Copy the example env file and fill in your secrets:

```bash
cp env.example .env
```

Open `.env` and set your credentials:

```env
QGENIE_API_KEY=your-actual-api-key
POSTGRES_ADMIN_USER=postgres
POSTGRES_ADMIN_PWD=postgres
POSTGRES_USER=your_db_user
POSTGRES_PWD=your_db_password
```

**Step B:** Review `config/config.yaml` and adjust settings for your environment — database host/port, LLM model names, chat endpoint, file paths, agent parameters, etc. Secrets referenced via `NOTE` comments in the YAML are loaded from `.env` at runtime.

> **Note:** Never commit `.env` to version control. The `env.example` is the safe, credential-free template to share with your team.

---

## Database Setup

### PostgreSQL (Production)

#### Rocky Linux / RHEL 8

```bash
# Install PostgreSQL 15
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo dnf -qy module disable postgresql
sudo dnf install -y postgresql15-server postgresql15-contrib

# Initialize and start
sudo /usr/pgsql-15/bin/postgresql-15-setup initdb
sudo systemctl enable --now postgresql-15
sudo systemctl status postgresql-15
```

#### macOS (Homebrew)

```bash
# Install PostgreSQL 15
brew install postgresql@15

# Start the service
brew services start postgresql@15

# Add to PATH (if not already)
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Windows

Download from https://www.postgresql.org/download/windows/ and follow the installer. After installation, start the server:

```powershell
& "C:\Program Files\PostgreSQL\15\bin\pg_ctl.exe" -D "C:\Users\<username>\PostgresData" -l "C:\Users\<username>\pg_log.txt" start
```

### Install pgvector Extension

The platform uses PostgreSQL's `pgvector` extension for vector similarity search on the OpEx data. **This extension must be installed before creating the database schema.** Without it, any query on the `opex_data_hybrid` table will fail with `could not access file "$libdir/vector"`.

#### Rocky Linux / RHEL 8

```bash
# pgvector is available in the PGDG repo you already added
sudo dnf install -y pgvector_15
```

If the package is not found, install from source:

```bash
sudo dnf install -y postgresql15-devel gcc make git
cd /tmp
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make PG_CONFIG=/usr/pgsql-15/bin/pg_config
sudo make install PG_CONFIG=/usr/pgsql-15/bin/pg_config
```

#### macOS (Homebrew)

```bash
# pgvector is available as a Homebrew formula
brew install pgvector
```

If using a Homebrew-installed PostgreSQL and the extension is not found, install from source:

```bash
cd /tmp
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make PG_CONFIG=$(brew --prefix postgresql@15)/bin/pg_config
make install PG_CONFIG=$(brew --prefix postgresql@15)/bin/pg_config
```

#### Windows

Download a prebuilt pgvector release from https://github.com/pgvector/pgvector/releases matching your PostgreSQL version. Extract and copy the files:

- `vector.dll` → `C:\Program Files\PostgreSQL\15\lib\`
- `vector.control` and `vector--*.sql` → `C:\Program Files\PostgreSQL\15\share\extension\`

Alternatively, build from source using Visual Studio — see https://github.com/pgvector/pgvector#windows for instructions.

#### Verify pgvector is Installed

After installing the extension library, restart PostgreSQL and verify:

```bash
sudo systemctl restart postgresql-15    # Rocky Linux
# brew services restart postgresql@15   # macOS
```

```bash
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;" -d template1
# Should succeed without errors
```

### Create Database and Enable Extensions

```bash
psql -U postgres
```

```sql
CREATE DATABASE cnss_opex_db;
\c cnss_opex_db
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

> **Troubleshooting:** If you get `could not access file "$libdir/vector"`, the pgvector shared library is not installed correctly. Re-run the pgvector installation steps above for your OS and restart PostgreSQL.

#### Initialize Schema

```bash
python bootstrap_db.py
```

This creates the OpEx hybrid tables and vector store schema. The CBN Resource Planner tables (`bpafg_demand`, `priority_template`) are created automatically on first data ingestion.

### SQLite (Local Development Fallback)

No setup required. The CBN Resource Planner automatically falls back to SQLite when PostgreSQL is unavailable. The database file is created at `data/cbn_resource_planner.db`.

---

## Data Ingestion

### OpEx Data (Excel)

Place Excel files in `data/excel_files/` following the OpEx schema (Fiscal Year, Project, Expense Type, Man Months, costs, etc.), then run:

```bash
python main.py
```

### CBN Resource Planner Data

Place CSV or XLSX files in the `data/` directory:

- **BPAFG Demand files** — filenames containing "bpafg" (e.g., `BPAFG - Feb_05_2026.csv`)
- **Priority Template files** — filenames containing "priority" (e.g., `priority_template_rank0.csv`)

Ingest via command line:

```bash
# Using PostgreSQL
python -m utils.parsers.cbn_data_parser --db postgres --data-dir data/

# Using SQLite (local dev)
python -m utils.parsers.cbn_data_parser --db sqlite --data-dir data/
```

Or upload directly through the Resource Planner UI — the upload widget appears when no data is loaded.

---

## Running the Application

```bash
python -m ui.launch_streamlit
```

The dashboard launches at **http://localhost:8502**. Access from another device on the same network using your machine's IP address.

### Pages

| Page | Description |
|------|-------------|
| **Resource Planner** | Mountain chart, capacity/cost panels, allocation table, project reordering |
| **ChatBot** | AI-powered natural language financial analysis with auto-charting |
| **Financial Trends** | Time-series trend analysis across fiscal periods |
| **Resource Allocation** | Resource utilization and allocation views |
| **Dept Rollup** | Department-level cost aggregation and VP rollup analysis |
| **Geo & Org Analytics** | Country-level and organizational spending comparisons |
| **Plotting Sandbox** | Custom visualization builder |
| **Chat History** | Browse and review past AI chat sessions |
| **FAQ** | Searchable frequently asked questions |
| **About** | Platform overview and technology stack |

---

## Project Structure

```
finance_dashbord/
├── agents/                    # AI agent modules
│   ├── orchestration_agent.py #   Main orchestrator (routes intent)
│   ├── user_intent_agent.py   #   Intent classification
│   ├── data_sql_query_agent.py#   SQL generation and execution
│   ├── semantic_search_agent.py#  RAG-based retrieval
│   ├── chatbot_agent.py       #   Conversational fallback
│   └── ...                    #   Visualization, ingestion, report agents
├── chat/                      # Chat service layer
│   ├── chat_service.py        #   ChatService (orchestrator wrapper)
│   ├── chat_persistence.py    #   SQLAlchemy session/message persistence
│   └── prompts.py             #   LLM system prompt configuration
├── config/                    # Configuration files
│   ├── config.py              #   Unified config loader (YAML + .env)
│   ├── config.yaml            #   Main configuration (DB, LLM, paths)
│   ├── schema.yaml            #   Vector DB schema definition
│   └── ...                    #   Prompts, labels, API docs
├── data/                      # Data files
│   ├── BPAFG - Feb_05_2026.csv
│   ├── priority_template_rank0.csv
│   └── CBN_Resource_Planner_v5.2_AI_Assistant_POC.html
├── db/                        # Database layer
│   ├── cbn_tables.py          #   CBN table definitions (Postgres + SQLite DDL)
│   ├── setup_db.py            #   OpEx schema setup
│   ├── data_pipeline.py       #   Excel → DB ingestion pipeline
│   ├── vector_store.py        #   PGVector store wrapper
│   └── ...                    #   Clear, drop, list, search utilities
├── ui/                        # Streamlit frontend
│   ├── streamlit_app.py       #   Main app entry point and router
│   ├── streamlit_tools.py     #   Global CSS (greenback theme) and utilities
│   ├── launch_streamlit.py    #   CLI launcher
│   ├── .streamlit/config.toml #   Streamlit theme configuration
│   └── modules/               #   Page modules
│       ├── base.py            #     PageBase class (CSS injection, layout)
│       ├── cbn_resource_planner.py  # Resource Planner page
│       ├── chatbot.py         #     AI ChatBot page
│       ├── faq.py             #     FAQ page
│       ├── about.py           #     About page
│       └── ...                #     Metrics, history, sandbox pages
├── utils/                     # Utility modules
│   ├── parsers/
│   │   ├── cbn_data_parser.py #   BPAFG + Priority Template parser
│   │   └── excel_to_json.py   #   Legacy Excel parser
│   └── models/                #   Database models and providers
├── env.example               # Environment template (cp to .env)
├── bootstrap_db.py            # One-time DB schema initialization
├── main.py                    # Data ingestion entry point
├── requirements.txt           # Python dependencies
└── README.md
```

---

## Database Utilities

```bash
# List rows in the database
python db/list_db.py                  # Default: first 20 rows
python db/list_db.py --limit 5        # Specific count
python db/list_db.py --all            # All rows

# Clear data (interactive confirmation)
python db/clear_db.py
python db/clear_db.py --force         # Skip confirmation (automation)

# Drop tables (interactive confirmation)
python db/drop_db.py
python db/drop_db.py --force          # Skip confirmation (automation)
```

After dropping tables, re-run `bootstrap_db.py` and data ingestion to rebuild.

### Useful psql Commands

```bash
psql -U postgres -d cnss_opex_db
```

```sql
\dt                              -- List all tables
\d bpafg_demand                  -- Describe table schema
\d priority_template
SELECT COUNT(*) FROM bpafg_demand;
SELECT DISTINCT project_name FROM bpafg_demand;
```

---

## Example ChatBot Queries

- "What are the top 5 projects by total demand?"
- "Show me resource demand trends for India over the next 12 months"
- "Compare capacity vs. demand by country"
- "For FY25 compare Q3 vs Q4 costs associated with all VP rollups under dept lead Jones, VK — provide analysis"
- "Which projects have the largest demand-capacity gap?"
- "Break down total spend by expense type for FY25"

---

## Configuration Reference

All settings can be configured via `config/config.yaml` or environment variables (`.env`). Environment variables take precedence.

| Setting | YAML Path | Env Variable | Default |
|---------|-----------|-------------|---------|
| DB Connection | `Postgres.connection` | `POSTGRES_CONNECTION` | `postgresql+psycopg2://postgres:postgres@localhost/cnss_opex_db` |
| DB Host | `Postgres.host` | `POSTGRES_HOST` | `localhost` |
| DB Port | `Postgres.port` | `POSTGRES_PORT` | `5432` |
| DB Name | `Postgres.database` | `POSTGRES_DB_NAME` | `cnss_opex_db` |
| LLM API Key | `Qgenie.api_key` | `QGENIE_API_KEY` | — |
| LLM Endpoint | `Qgenie.chat_endpoint` | `QGENIE_CHAT_ENDPOINT` | — |
| Streamlit Port | — | `STREAMLIT_PORT` | `8502` |
| Log Level | — | `LOG_LEVEL` | `INFO` |

---

## License

See [LICENSE](LICENSE) for details.
