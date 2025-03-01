from abc import ABC, abstractmethod
from app.scraper.scraper import ImageData
from qdrant_client import QdrantClient

class Processor(ABC):
    """
    Abstract class for Processor.
    Implement this class to create a new custom Processor.
    """
    
    def __init__(self):
        pass

    @abstractmethod
    def process(self, md_data: str, image_data : ImageData, client : QdrantClient) -> None:
        """
        Processes markdown and image data and inserts it into the Qdrant vector store.
        Args:
            md_data (str): Markdown formatted text.
            image_data (ImageData): Image data.
            client: Qdrant Vector Store client.
        """
        pass