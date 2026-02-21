**Finance Dashboard**
========


Finance Dashboard is an assistant agent that analyzes spreadsheets by following user commands. 
It breaks new ground in data analysis and interaction, opening up possibilities for enabling non-expert users to understand excel data using human language interface.

## What's New

## TODO
- Update the function call parsing code to fix the quote parsing errors
- Update API implementations
- Update the evaluation script to improve the checking accuracy

# Overview

Finance Dashboard employs a novel way of directing Large Language Models (LLMs) to analyze spreadsheets like a human expert. To achieve elegant closed-loop control, Finance Dashboard observes the spreadsheet state and polishes generated solutions according to external action documents and error feedback, thereby improving its success rate and efficiency.

# Setup

```bash
sudo su
```

```bash
# if there is already an .env
deactivate
rm -rf .venv

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate
python --version
```

### 4. Install Dependencies

```bash
pip install --upgrade pip

pip install qgenie-sdk[all] qgenie-sdk-tools -i https://devpi.qualcomm.com/qcom/dev/+simple --trusted-host devpi.qualcomm.com
pip install -r requirements.txt
```

### DB Installation 
1) Rocky Linux or
2) Windows

### Rocky linux
- Install Postgresql and create a database called powerdb

#### Enable the repo for PostgreSQL 15 (replace 15 with your preferred version if needed)
- `sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm`

#### Disable the default module to avoid conflicts
- `sudo dnf -qy module disable postgresql`

#### Install PostgreSQL 15 server and contrib packages
- `sudo dnf install -y postgresql15-server postgresql15-contrib postgresql15-pgvector`

#### Initialize the database and enable/start PostgreSQL
- `sudo /usr/pgsql-15/bin/postgresql-15-setup initdb` initializes DB cluster
    - Note: If the data directory is not empty, the DB cluster is already initialized.

- `sudo systemctl enable --now postgresql-15` (OR) `sudo systemctl start postgresql-15` this starts the server
    - Note: for windows powershell running `& "C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe" -D "C:\Users\<username>\PostgresData" -l "C:\Users\<username>\pg_log.txt" start` will get response as *server started*

- `sudo systemctl status postgresql-15`
    - Note: for windows powershell `& "C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe" -D "C:\Users\<username>\PostgresData" status`
    - Note: for windows powershell `& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d rag_dashboard_v1` to enter psql prompt

#### For windows
- Download from https://www.postgresql.org/download/windows/

#### pgvector extension
- It is advised to follow the versions of pgvector, psycopg mentioned in the requirements
- sudo dnf install -y postgresql15-pgvector 

#### For more clarifications or instructions
- Please refer Postgresql Schema Setup section under USEFUL INFORMATION below
- Or please look at tools/postgres_init.sh (which is a postgres db setup script)

# Data
Drop the excel file with the following schema into the ``<root>/data/excel_files`` folder.

## Schema:

Please make sure the schema of the excel is as shown below:

| Version  | Fiscal Year | Charged D | Project Nu | Project Desc      | Project Pri     | Exp Type R | Home Dept | Home Dept Region R1 | Home Dept Region R2 | Fiscal Quarter | Fiscal Month | Home Dept VP Rollup 2 | Home Dept VP Rollup 1 | Home Dept Number | Home Dept Desc                           | Exp Type              | TM1 (Man Months) | TM1 ($$M) | ET Roll up  | ET 2        | ET 3        | ET 4  | NRE  | Proj Rollup | Dept VP         | Dept Lead | HW/SW   | Tech | Organization | Dept Incl |
| :------- | :---------- | :-------- | :--------- | :---------------- | :-------------- | :--------- | :-------- | :------------------ | :------------------ | :------------- | :----------- | :-------------------- | :-------------------- | :--------------- | :--------------------------------------- | :-------------------- | :--------------- | :-------- | :---------- | :---------- | :---------- | :---- | :--- | :---------- | :-------------- | :-------- | :------ | :--- | :----------- | :-------- |
| FY25 Act | 2025        | L2-WIN    | 14180      | QCA Project OH-HW | CONSHARE Direct | WIN        | USA       |                     | San Diego           | Q3             | Jun          | Tech Alloc            | Tech Alloc            | 30941            | QCT Engineering Allocation Applied - WIN | Project Allocation In | 0.xxxx           | 0.xxx     | Allocations | Allocations | Allocations | Labor | N/A  | ConnShare   | Singh, Harinder | Jones, VK | IP/Tech | HWS  | NA           | Y         |

 

# ExcelQgenie Usage

## Excel data storage
The data in excel is stored in the local vector database:

Schema for the vector Database: ``<root>/config/schema.yaml`` : Update the schema if the excel has a different schema (columns)



## Project config

Config for the project resides in : ``<root>/config/config.yaml`` 

update this file to include the ``LLM API Key`` and ``LLM to USE`` , source paths, dest paths, etc.


# Vecor DB Installation
1. Update the  ``<root>/config/config.yaml``  file to include the vectorDB configuration and ``<root>/config/schema.yaml`` for the DB schema.
2. Run the below once to setup the database:
  ``python bootstrap_db.py``

3. Store the updated excel files in the ``<root>/data/excel_files`` directory.
4. Data ingestion into the vector DB: 
    ``python main.py``

5. Run streamlit web apps that opens up the browser window for interacting with the data:
    ``python -m ui.launch_streamlit``



## Delete DB usage

# How to Use

Run Interactively (Recommended): Execute the script from your terminal. It will prompt you for confirmation before doing anything.
``python clear_db.py``

You will see the warning and be asked to type y to proceed.

Run with a custom config file:
``python clear_db.py --config path/to/your/config.yaml``

Run in a Script (Forced): If you need to use this in an automated reset script, use the --force flag to skip the interactive prompt.
# Use with caution!
``python clear_db.py --force``

## List DB Usage

# How to Use

List the first 20 rows (default):
``python list_db.py``

List a specific number of rows:
``python list_db.py --limit 5``

List all rows in the table:
``python list_db.py --all``

Use a different configuration file:
``python list_db.py --config path/to/other.yaml --limit 10``


## Drop DB

How to run it
Standard Run (Safe Mode)
``python drop_db.py``

It will list the tables and ask you to type DELETE to confirm.

Force Run (For automation)
``python drop_db.py --force``

After running this: You will need to run your ``setup_db.py`` (and potentially initialize the vector store) to recreate the schema before you can store data again.

# PSQL commands
``psql -U postgres -l``
``psql -U postgres -d cnss_opex_db``
``CREATE EXTENSION IF NOT EXISTS vector;``
``\d``
``\dt``
``\d table_name``

``DROP TABLE IF EXISTS opex_data_hybrid CASCADE;``

``\dt``
``\q``


# Exampel Query in the chat bot

``For FY 25 compare Q3 vs Q4 costs associated with all the VP rollups under dept lead Jones, VK, provide analysis .``
