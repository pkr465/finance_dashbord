import os
import logging
from typing import List, Optional, Any
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the QGenie Embeddings class
try:
    from qgenie.integrations.langchain import QGenieEmbeddings
except ImportError:
    # Fallback for environments where qgenie is not installed
    logger.error("QGenie SDK not found. Install it via: pip install qgenie-sdk")
    QGenieEmbeddings = None

class EmbeddingClient:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.client = None
        self.model_name = None 
        self.api_key = None
        
        # Load config and initialize the client immediately
        self._initialize_client(config_path)

    def _initialize_client(self, config_path: str):
        """Loads configuration and initializes the QGenieEmbeddings client."""
        if not QGenieEmbeddings:
            logger.error("Cannot initialize client: QGenieEmbeddings class is missing.")
            return

        try:
            # 1. Load Config File
            if not os.path.exists(config_path):
                logger.warning(f"Config file not found at {config_path}. Attempting to run with defaults/env vars.")
                self.client = QGenieEmbeddings()
                return

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # 2. Extract Configuration
            qgenie_config = config.get('Qgenie', {})
            self.api_key = qgenie_config.get('api_key')
            self.model_name = qgenie_config.get('embedding_model')

            # 3. Prepare Initialization Arguments
            init_kwargs = {}
            
            if self.api_key:
                # UPDATED: Use 'api_key' instead of 'auth_token' based on error message
                init_kwargs['api_key'] = self.api_key
                
                # Also set ENV var as a backup since some underlying SDK calls might look for it directly
                os.environ["QGENIE_API_KEY"] = self.api_key
                
            if self.model_name:
                init_kwargs['model'] = self.model_name

            logger.info(f"Initializing QGenieEmbeddings with model: {self.model_name or 'Default'}")
            
            # 4. Initialize Client
            self.client = QGenieEmbeddings(**init_kwargs)
            
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingClient: {e}", exc_info=True)
            self.client = None

    def get_embedding_function(self) -> Any:
        """
        Returns the initialized LangChain embedding object.
        Used by VectorStores to embed documents automatically.
        """
        if not self.client:
            raise ValueError("QGenie Client is not initialized. Check logs for setup errors.")
        return self.client
        
    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for a single text string.
        """
        if not self.client:
            raise ValueError("QGenie Client is not initialized. Check logs for setup errors.")
            
        # Clean text
        text = text.replace("\n", " ")
        
        try:
            # Use embed_query for a single string
            embedding = self.client.embed_query(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding via QGenie: {e}")
            raise