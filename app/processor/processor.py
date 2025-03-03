from abc import ABC, abstractmethod
from app.scraper.scraper import ImageData
from qdrant_client import QdrantClient
from sqlite3 import Connection
from langchain_core.embeddings.embeddings import Embeddings
from app.config_loader import ConfigLoader

class Processor(ABC):
    """
    Abstract class for Processor.
    Implement this class to create a new custom Processor.
    """
    
    def __init__(self, md_data : str, 
                 image_data : ImageData, 
                 paper_id : str, 
                 sql_conn : Connection, 
                 qdrant_client : QdrantClient,
                 embed: Embeddings):
        self.configs = ConfigLoader().get_config()
        self.md_data = md_data
        self.image_data = image_data
        self.paper_id = paper_id
        self.sql_conn = sql_conn
        self.qdrant_client = qdrant_client
        self.embed = embed
        pass

    

    @abstractmethod
    def process() -> None:
        """
        Processes markdown and image data and inserts it into the Qdrant vector store.
        """
        pass