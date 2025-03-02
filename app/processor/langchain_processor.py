from app.processor.processor import Processor
from app.scraper.scraper import ImageData
from qdrant_client import QdrantClient
from typing import List
from typing import Dict, Any
import yaml
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
from langchain_core.documents import Document
from sqlite3 import Connection
import re
from uuid import uuid4

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
            separators=['. '], # split by sentences
            keep_separator=True,
            tokenizer=self.tokenizer, 
            chunk_size= self.chunk_size - self.configs['chunk_size_penalty'],
            chunk_overlap=self.chunk_overlap
        )

    def load_tokenizer_model(self, model_name : str) -> PreTrainedTokenizer|PreTrainedTokenizerFast:
        """Loads the tokenizer of the Embedding Model used by the Embedding Server."""
        token = AutoTokenizer.from_pretrained(model_name)
        return token

    def read_config(self) -> Dict[str, Any]:

        config_path = 'config.yaml'
        
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        embedding_config = config['configs'][2]['embedding_config']
        chunking_config = config['configs'][3]['chunking_config']
        
        # Create a flat dictionary with direct access to needed configs
        return {
            'tokenizer': embedding_config[1]['tokenizer'],
            'max_seq_length': embedding_config[2]['max_seq_length'],
            'use_emb_model_max_seq_length': chunking_config[0]['use_emb_model_max_seq_length'],
            'chunk_size': chunking_config[1]['chunk_size'],
            'chunk_size_penalty': chunking_config[2]['chunk_size_penalty'],
            'chunk_overlap_percent': chunking_config[3]['chunk_overlap_percent']
        }
    
    def split_md_data(self, md_data : str) -> List[Document]:
        """
        Splits markdown data into chunks.
        Args:
            md_data (str): Markdown formatted text.
        Returns:
            List[Document]: List of Document objects. First object is paper info.
        """
        texts = self.markdown_splitter.split_text(md_data)
        splits = self.token_splitter.split_documents(texts[1:])
        splits.insert(0, texts[0]) # Add paper info to the beginning of the list
        return splits


    def create_split_metadata(self, paper_id : str, md_splits : List[Document]) -> List[Document]:
        """
        Creates metadata for each split.
        Args:
            md_splits (List[Document]): List of Document objects.
        Returns:
            List[Document]: List of Document objects containing metadata.
        """
        chapter_num_regex = r'\b\d+(?:\.\d+)*\b'
        fig_ref_ids_regex = r'(?i)\b(?:Figure|Fig\.?) (\d+(?:\.\d+)*)\b'
        for i, split in enumerate(md_splits):
            split.metadata['id'] = str(uuid4())
            split.metadata['paper_id'] = paper_id
            if 'chapter' in split.metadata.keys():
                chapter_id = re.findall(chapter_num_regex, split.metadata['chapter'])
                if chapter_id:
                    split.metadata['chapter_id'] = chapter_id[0]
            split.metadata['fig_ref_ids'] = re.findall(fig_ref_ids_regex, split.page_content)
            # next and previous split ids
            if i > 0:
                split.metadata['prev_id'] = md_splits[i - 1].metadata['id']
                md_splits[i-1].metadata['next_id'] = split.metadata['id']

                
    def insert_paper_info(self, paper_info: Document, paper_id : str, sql_conn : Connection) -> None:
        """
        Inserts paper info into the database.
        Args:
            paper_info (Document): Document object containing paper info.
            paper_id (str): Paper ID.
            sql_conn (Connection): SQLite connection object.
        """
        cursor = sql_conn.cursor()
        cursor.execute('INSERT INTO paper_info VALUES (?,?)', (paper_id, paper_info.page_content))
        sql_conn.commit()
        cursor.close()

    def process(self, md_data: str, image_data : ImageData, paper_id : str, sql_conn : Connection, qdrant_client : QdrantClient) -> None:

        md_splits = self.split_md_data(md_data)
        self.insert_paper_info(md_splits[0], paper_id, sql_conn)
        md_splits.pop(0) # Remove paper info from the list
        self.create_split_metadata(paper_id, md_splits)