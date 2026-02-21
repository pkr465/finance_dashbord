import json
import logging
from typing import Dict, List, Any, Tuple, Optional

# Import the centralized schema configuration
try:
    from config.schema_config import SCHEMA_CONFIG
except ImportError:
    SCHEMA_CONFIG = {}

# Import Database Utility
try:
    from utils.models.database import OpexDB
except ImportError:
    class OpexDB:
        @staticmethod
        def execute_sql_query(sql, format_as_markdown=False):
            raise ImportError("OpexDB not found")

# Import Database Session
try:
    from utils.models.database import get_db_session
except ImportError:
    def get_db_session(): yield None

# Import Agent Utils
try:
    from agents.utils.agent_utils import AgentUtils
except ImportError:
    try:
        from agent_utils import AgentUtils
    except ImportError:
        pass

try:
    from config.labeling import QuerySchemaMapper
except ImportError:
    class QuerySchemaMapper:
        def get_relevant_schema_context(self, query):
            return ""

logger = logging.getLogger(__name__)

# ==============================================================================
# RICH SCHEMA DEFINITIONS
# ==============================================================================

LABELS_CONTEXT = """
### DETAILED COLUMN DEFINITIONS & MAPPING
The table '{table_name}' contains a JSONB column named `additional_data`. 
Most business logic columns are stored INSIDE this JSON column.

1. **METRICS (Effort/Cost)**
   - "Spend", "Cost", "Resources" -> `CAST(additional_data->>'ods_mm' AS NUMERIC)`
   
2. **GEOGRAPHY**
   - "Country", "Region" -> `additional_data->>'home_dept_region_r1'`
   - "City", "Location" -> `additional_data->>'home_dept_region_r2'`

3. **PEOPLE**
   - "VP" -> `additional_data->>'dept_vp'`
   - "Lead" -> `additional_data->>'dept_lead'`
   
4. **TIME**
   - "Year" -> `additional_data->>'fiscal_year'`
   - "Quarter" -> `additional_data->>'fiscal_quarter'`
"""

SQL_QUERY_PROMPT = """
You are a PostgreSQL expert specialized in Financial data.
Your task is to generate an executable SQL query.

### CRITICAL RULES (DO NOT IGNORE):
1. **NO BIND PARAMETERS**: 
   - You **MUST NOT** use placeholders like `:value`, `?`, or `%s`. 
   - You **MUST** inject the literal values directly into the SQL string.
   - WRONG: `WHERE additional_data->>'fiscal_year' = :fiscal_year`
   - CORRECT: `WHERE additional_data->>'fiscal_year' = '2025'`

2. **JSON Extraction**: 
   - Use `additional_data->>'key_name'` for all business fields.
   - Text matching should be case-insensitive using `ILIKE` (e.g. `->>'dept_lead' ILIKE 'Jones%'`).

3. **Data Types**: 
   - `ods_mm` is text in JSON. You MUST cast it: `CAST(additional_data->>'ods_mm' AS NUMERIC)`.
   - Handle NULLs: `COALESCE(CAST(... AS NUMERIC), 0)`.

4. **UNION Sorting**:
   - If using `UNION`, the `ORDER BY` clause MUST refer to column names or indices, NOT expressions.
   - WRONG: `ORDER BY CASE WHEN...`
   - CORRECT: `ORDER BY dept_vp`

### RESPONSE FORMAT:
Return a JSON object with two keys:
{{
    "sql": "SELECT ...",
    "explanation": "Brief explanation."
}}
"""

SQL_QUERY_FIX_PROMPT = """
The previous SQL query failed.
Please fix it based on the error.

# Broken Query:
{sql}

# Error Message:
{error_msg}

# FIX INSTRUCTIONS:
1. **Bind Parameter Error?** (e.g. "value required for bind parameter")
   - You likely used `:param` or `%s`. REPLACE them with exact literal values (e.g. '2025').
2. **UNION Order Error?**
   - Simplify the ORDER BY clause. Sort by column name only.
3. **Column Error?**
   - Check if you forgot `additional_data->>`.

Return the fixed query in JSON format.
"""

class SQLQueryAgent:
    def __init__(self, tools=None):
        self.schema_config = SCHEMA_CONFIG
        self.table_name = self.schema_config.get("table_name", "opex_data_hybrid")
        self.tools = tools if tools else AgentUtils()
        self.schema_mapper = QuerySchemaMapper()

    def get_schema_context(self) -> str:
        schema_sql = self.schema_config.get("create_table_sql", "")
        labels_context = LABELS_CONTEXT.format(table_name=self.table_name)
        return f"{schema_sql}\n\n{labels_context}"

    def _llm_sql_gen(self, prompt: str) -> Tuple[str, str]:
        logger.info("Generating SQL with LLM...")
        try:
            resp = self.tools.llm_call(prompt)
            if not isinstance(resp, str):
                return "", "LLM Error: Non-string response"

            cleaned_resp = resp.strip().replace("```json", "").replace("```", "")
            resp_obj = json.loads(cleaned_resp)
            return resp_obj.get("sql", ""), resp_obj.get("explanation", "")
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {resp}")
            return "", "JSON Parsing Error"
        except Exception as e:
            logger.error(f"Error processing LLM: {e}")
            return "", f"Error: {str(e)}"

    def get_sql(self, query_text: str) -> Tuple[str, str]:
        try:
            system_prompt = SQL_QUERY_PROMPT.format(table_name=self.table_name)
        except KeyError:
            return "", "Prompt error"

        schema_context = self.get_schema_context()
        relevant_context = self.schema_mapper.get_relevant_schema_context(query_text)
        
        prompt = (
            f"{system_prompt}\n\n"
            f"### Schema:\n{schema_context}\n\n"
            f"### Context:\n{relevant_context}\n\n"
            f"### User Request:\n{query_text}\n"
        )
        
        return self._llm_sql_gen(prompt)

    def fix_sql(self, sql: str, explanation: str, error_msg: str) -> str:
        try:
            prompt = SQL_QUERY_FIX_PROMPT.format(
                sql=sql,
                error_msg=error_msg,
                explanation=explanation
            )
            sql, _ = self._llm_sql_gen(prompt)
            return sql
        except Exception as e:
            logger.error(f"Fix prompt error: {e}")
            return ""

    def execute_query(self, sql: str) -> Any:
        if not sql:
            return None
        logger.info(f"Executing SQL: {sql}")
        try:
            # We attempt execution
            results = OpexDB.execute_sql_query(sql, format_as_markdown=True)
            return results
        except Exception as e:
            # CRITICAL: Attempt to rollback session to prevent 'current transaction is aborted' errors
            try:
                session_gen = get_db_session()
                session = next(session_gen)
                if session:
                    session.rollback()
                    logger.info("Database session rolled back successfully.")
            except Exception as rollback_err:
                logger.warning(f"Failed to rollback session: {rollback_err}")
            
            logger.error(f"DB Error: {e}")
            raise e

    def run(self, user_input: str, retry_limit: int = 3) -> Dict[str, Any]:
        sql, explanation = self.get_sql(user_input)
        if not sql:
            return {"status": "error", "message": "Failed to generate SQL"}

        current_try = 0
        while current_try < retry_limit:
            try:
                results = self.execute_query(sql)
                return {
                    "status": "success",
                    "sql": sql,
                    "explanation": explanation,
                    "results": results
                }
            except Exception as e:
                logger.warning(f"Attempt {current_try+1} failed: {e}")
                sql = self.fix_sql(sql, explanation, str(e))
                current_try += 1
        
        return {
            "status": "error", 
            "message": "Exceeded retry limit", 
            "last_sql": sql
        }