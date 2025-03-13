from typing import List, Any, Dict
from app.config_loader import ConfigLoader
from app.scraper.scraper import ImageData

class Processor:
    """
    Base class for content processing.
    """

    def __init__(self, md_data: str, 
                 image_data: ImageData, 
                 paper_id: str, 
                 text_vs,
                 img_emb: Any,
                 img_proc: Any):
        self.md_data = md_data
        self.image_data = image_data
        self.paper_id = paper_id
        self.text_vs = text_vs
        self.img_emb = img_emb
        self.img_proc = img_proc
        self.configs = ConfigLoader().get_config()

    def process(self) -> None:
        """Process documents."""
        raise NotImplementedError