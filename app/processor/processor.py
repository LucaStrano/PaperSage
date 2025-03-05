from abc import ABC, abstractmethod
from app.scraper.scraper import ImageData
from langchain_core.vectorstores import VectorStore
from sqlite3 import Connection
from app.config_loader import ConfigLoader
from typing import Any

class Processor(ABC):
    """
    Abstract class for Processor.
    Implement this class to create a new custom Processor.
    """
    
    def __init__(self, md_data : str, 
                 image_data : ImageData, 
                 paper_id : str, 
                 sql_conn : Connection, 
                 text_vector_store : VectorStore,
                 img_emb : Any,
                 img_proc : Any):
        self.configs = ConfigLoader().get_config()
        self.md_data = md_data
        self.image_data = image_data
        self.paper_id = paper_id
        self.sql_conn = sql_conn
        self.text_vs = text_vector_store
        self.img_emb = img_emb
        self.img_proc = img_proc
        pass
    

    @abstractmethod
    def process() -> None:
        """
        Processes markdown and (optionally) image data and inserts it into the Vector Store.
        """
        pass