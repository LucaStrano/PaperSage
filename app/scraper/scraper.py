from abc import ABC, abstractmethod
from typing import List, Tuple

image_data = List[bytes, dict]

class Scraper(ABC):
    """
    Abstract class for Scraper.
    Implement this class to create a new custom Scraper.
    """
    
    @abstractmethod
    def process_document(self, document_path: str) -> Tuple[str, image_data]:
        """
        Process the document and returns markdown-formatted text and Image data.
        Args:
            document_path (str): Path to the document to be processed.
        Returns:
            Tuple[str, image_data]: Tuple containing markdown-formatted text and Image data.
        """
        pass