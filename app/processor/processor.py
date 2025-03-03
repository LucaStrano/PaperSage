from abc import ABC, abstractmethod
from app.scraper.scraper import ImageData
from langchain_core.vectorstores import VectorStore
from sqlite3 import Connection
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
                 vector_store : VectorStore):
        self.configs = ConfigLoader().get_config()
        self.md_data = md_data
        self.image_data = image_data
        self.paper_id = paper_id
        self.sql_conn = sql_conn
        self.vector_store = vector_store
        pass
    

    @abstractmethod
    def process() -> None:
        """
        Processes markdown and (optionally) image data and inserts it into the Vector Store.
        """
        pass