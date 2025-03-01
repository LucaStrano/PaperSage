from app.processor.processor import Processor
from app.scraper.scraper import ImageData
from qdrant_client import QdrantClient
from typing import List, Tuple
from PIL.Image import Image
from typing import Dict, Any
import yaml
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast

class LangchainProcessor(Processor):
    """
    Processor for Langchain.
    """    
    
    def __init__(self):
        super().__init__()
        self.configs = self.read_config()
        self.tokenizer = self.load_tokenizer_model(self.configs['tokenizer'])
        if self.configs['use_emb_model_max_seq_length']:
            self.chunk_size = self.configs['max_seq_length']
        else:
            self.chunk_size = self.configs['chunk_size']
        self.chunk_overlap = int(self.chunk_size * self.configs['chunk_overlap_percent'])
        self.markdown_splitter = MarkdownHeaderTextSplitter([("##", "chapter")])
        self.token_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            self.tokenizer, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )

    def load_tokenizer_model(self, model_name : str) -> PreTrainedTokenizer|PreTrainedTokenizerFast:
        """Loads the tokenizer of the Embedding Model used by the Embedding Server."""
        token = AutoTokenizer.from_pretrained(model_name)
        return token

    def read_config(self) -> Dict[str, Any]:

        config_path = 'config.yaml'
        
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Extract specific configurations
        embedding_config = config['configs'][2]['embedding_config']
        chunking_config = config['configs'][3]['chunking_config']
        
        # Create a flat dictionary with direct access to needed configs
        return {
            'tokenizer': embedding_config[1]['tokenizer'],
            'max_seq_length': embedding_config[2]['max_seq_length'],
            'use_emb_model_max_seq_length': chunking_config[0]['use_emb_model_max_seq_length'],
            'chunk_size': chunking_config[1]['chunk_size'],
            'chunk_overlap_percent': chunking_config[2]['chunk_overlap_percent']
        }

    def process(self, md_data: str, image_data : ImageData, client : QdrantClient) -> None:
        """
        Processes markdown and image data and inserts it into the Qdrant vector store.
        Args:
            md_data (str): Markdown formatted text.
            image_data (ImageData): Image data.
            client: Qdrant Vector Store client.
        """
        pass