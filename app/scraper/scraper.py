from abc import ABC, abstractmethod
from typing import List, Tuple
from PIL.Image import Image

ImageData = List[Tuple[Image, dict]]
# dict contains the following keys:
# - 'caption' : str
# - 'page_id' : int
# - 'fig_id' : int


class Scraper(ABC):
    """
    Abstract class for Scraper.
    Implement this class to create a new custom Scraper.
    """

    def __init__(self):
        pass
    
    @abstractmethod
    def process_document(self, document_path: str) -> Tuple[str, ImageData]:
        """
        Process the document and returns markdown-formatted text and Image data.
        Args:
            document_path (str): Path to the document to be processed.
        Returns:
            Tuple[str, image_data]: Tuple containing markdown-formatted text and Image data.
        """
        pass