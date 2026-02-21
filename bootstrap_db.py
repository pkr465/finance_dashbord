import logging
import os
import yaml
from sqlalchemy import create_engine, text, inspect
from typing import Dict, Optional

# --- IMPORT SCHEMA CONFIG ---
# Kept here for default usage, but can also be passed to the class
from config.schema_config import SCHEMA_CONFIG

class DatabaseSetupManager:
    """
    Manages database connection and schema setup operations.
    """
    
    def __init__(self, config_path: str = 'config/config.yaml', schema_config: Dict = SCHEMA_CONFIG):
        """
        Initialize the manager with a configuration file path and schema configuration.
        """
        self.config_path = config_path
        self.schema_config = schema_config
        self.logger = self._configure_logger()
        self.config = self._load_config()

    def _configure_logger(self) -> logging.Logger:
        """Sets up the logger if not already configured."""
        logger = logging.getLogger(__name__)
        if not logger.hasHandlers():
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logger

    def _load_config(self) -> Dict:
        """Loads and parses the YAML configuration file."""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
                
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def _get_connection_string(self) -> str:
        """
        Constructs a SQLAlchemy connection string from the loaded configuration.
        """
        self.logger.info("Building database connection string from configuration...")
        try:
            pg_config = self.config.get('Postgres')
            if not pg_config:
                raise KeyError("Could not find 'Postgres' section in config.")

            username = pg_config.get('user') or pg_config.get('username')
            password = pg_config['password']
            host = pg_config['host']
            port = pg_config['port']
            database = pg_config.get('dbname') or pg_config.get('database')
            
            # Default to psycopg2
            driver = "postgresql+psycopg2"
            
            return f"{driver}://{username}:{password}@{host}:{port}/{database}"

        except KeyError as e:
            self.logger.error(f"Configuration is missing a required key: {e}")
            raise

    def setup_database(self) -> None:
        """
        Checks if the table exists. If it does, skips setup.
        If it does NOT exist, ensures the 'vector' extension is loaded, creates the table, and applies indexes.
        """
        connection_string = self._get_connection_string()
        if not connection_string:
            raise ValueError("Connection string cannot be None or empty.")

        table_name = self.schema_config.get("table_name", "Unknown Table")
        
        try:
            engine = create_engine(connection_string)
            
            # --- 1. Check if Table Exists ---
            inspector = inspect(engine)
            if inspector.has_table(table_name):
                self.logger.info(f"✅ Table '{table_name}' already exists. Skipping database setup.")
                return

            # --- 2. Create Table (Only if it doesn't exist) ---
            self.logger.info(f"Table '{table_name}' not found. Starting setup...")
            
            with engine.connect() as conn:
                with conn.begin():  # Transaction block
                    
                    # --- Enable Vector Extension ---
                    self.logger.info("Attempting to enable 'vector' extension...")
                    try:
                        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                        self.logger.info("Vector extension check passed.")
                    except Exception as e:
                        if "permission denied" in str(e).lower():
                            self.logger.error("❌ Permission denied enabling 'vector' extension.")
                            self.logger.error("Please run this script with a Superuser account or ask a DBA to run 'CREATE EXTENSION vector;'")
                        raise e

                    # --- Create Table ---
                    self.logger.info(f"Executing CREATE TABLE statement for '{table_name}'...")
                    conn.execute(text(self.schema_config["create_table_sql"]))
                    self.logger.info(f"Table '{table_name}' created.")

                    # --- Create Indexes ---
                    self.logger.info(f"Applying indexes for '{table_name}'...")
                    for index_sql in self.schema_config["indexes_sql"]:
                        try:
                            conn.execute(text(index_sql))
                        except Exception as idx_err:
                            # Log but don't crash if index exists (edge case)
                            self.logger.warning(f"Note during index creation: {idx_err}")
                    
                self.logger.info(f"🎉 Database setup for '{table_name}' completed successfully.")

        except Exception as e:
            self.logger.error(f"❌ An error occurred during database setup for '{table_name}': {e}", exc_info=True)
            raise

def main():
    """
    Main function to instantiate and run the DatabaseSetupManager.
    """
    logging.info("--- Running Database Setup Check ---")
    try:
        # You can pass a different config path here if needed
        db_manager = DatabaseSetupManager()
        db_manager.setup_database()
    except Exception as e:
        logging.error(f"Setup failed: {e}")

if __name__ == "__main__":
    main()