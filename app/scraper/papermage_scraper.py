from app.scraper.scraper import Scraper, image_data

from typing import List, Tuple
from papermage.magelib import Entity, Box, Document
from PIL import Image

class PapermageScraper(Scraper):

    def __init__(self):
        super().__init__()
    
    def process_document(self, document_path: str) -> Tuple[str, image_data]:
        print("Processing document using PapermageScraper")
        return None