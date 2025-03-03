from app.processor.processor import Processor
from app.scraper.scraper import ImageData
from typing import List
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
from sqlite3 import Connection
import re
from uuid import uuid4

class LangchainProcessor(Processor):
    """
    Langchain Processor Implementation.
    """    
    
    def __init__(self, md_data : str, 
                 image_data : ImageData, 
                 paper_id : str, 
                 sql_conn : Connection, 
                 vector_store : QdrantVectorStore):
        super().__init__(md_data, image_data, paper_id, sql_conn, vector_store)
        self.tokenizer = self.load_tokenizer_model(self.configs['embedding_config']['tokenizer'])
        chunk_config = self.configs['chunking_config']
        self.chunk_size = \
            chunk_config['chunk_size'] if not chunk_config['use_emb_model_max_seq_length'] else self.configs['embedding_config']['tokenizer']
        self.chunk_size = self.chunk_size - chunk_config['chunk_size_penalty']
        self.chunk_overlap = int(self.chunk_size * chunk_config['chunk_overlap_percent'])
        self.markdown_splitter = MarkdownHeaderTextSplitter([("##", "chapter")])
        self.token_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            separators=['. '], # split by sentences
            keep_separator=True,
            tokenizer=self.tokenizer, 
            chunk_size= self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def load_tokenizer_model(self, model_name : str) -> PreTrainedTokenizer|PreTrainedTokenizerFast:
        """Loads the tokenizer of the Embedding Model used by the Embedding Server."""
        try:
            token = AutoTokenizer.from_pretrained(model_name)
        except Exception as e:
            print(f"Error loading tokenizer: {e}. Trying to download...")
            token = AutoTokenizer.from_pretrained(model_name, force_download=True)
        
        return token
    
    def split_md_data(self) -> List[Document]:
        """
        Splits markdown data into chunks.
        Returns:
            List[Document]: List of Document objects. First object is paper info.
        """
        texts = self.markdown_splitter.split_text(self.md_data)
        splits = self.token_splitter.split_documents(texts[1:])
        splits.insert(0, texts[0]) # Add paper info to the beginning of the list
        return splits


    def create_split_metadata(self, md_splits : List[Document]) -> None:
        """
        Creates metadata for each split. Modifies the Document object in place.
        Args:
            md_splits (List[Document]): List of Document objects.
        """
        chapter_num_regex = r'\b\d+(?:\.\d+)*\b'
        fig_ref_ids_regex = r'(?i)\b(?:Figure|Fig\.?) (\d+(?:\.\d+)*)\b'
        for i, split in enumerate(md_splits):
            split.metadata['id'] = str(uuid4())
            split.metadata['paper_id'] = self.paper_id
            # extract chapter id
            if 'chapter' in split.metadata.keys():
                chapter_id = re.findall(chapter_num_regex, split.metadata['chapter'])
                if chapter_id: split.metadata['chapter_id'] = chapter_id[0]
            # extract figure reference ids
            split.metadata['fig_ref_ids'] = re.findall(fig_ref_ids_regex, split.page_content)
            # next and previous split ids
            if i > 0:
                split.metadata['prev_id'] = md_splits[i - 1].metadata['id']
                md_splits[i-1].metadata['next_id'] = split.metadata['id']

                
    def insert_paper_info(self, paper_info: Document) -> None:
        """
        Inserts paper info into the database.
        Args:
            paper_info (Document): Document object containing paper info.
        """
        cursor = self.sql_conn.cursor()
        cursor.execute('INSERT INTO paper_info VALUES (?,?)', (self.paper_id, paper_info.page_content))
        self.sql_conn.commit()
        cursor.close()

    
    def insert_text_in_vs(self, splits : List[Document]) -> None:
        """
        Inserts text data into the Qdrant Vector Store.
        Args:
            splits (List[Document]): List of Document objects.
        """
        if self.configs['embedding_config']['use_prefix']:
            prefix = self.configs['embedding_config']['document_prefix']
            for split in splits:
                split.page_content = prefix + split.page_content

        self.vector_store.add_documents(splits)

    def process(self) -> None:

        # process markdown data
        print("Processing markdown data...")
        md_splits = self.split_md_data()
        self.insert_paper_info(md_splits[0])
        md_splits.pop(0) # Remove paper info from the list
        self.create_split_metadata(md_splits)
        if self.configs['chunking_config']['add_section_titles']:
            for split in md_splits:
                if 'chapter' in split.metadata.keys():
                    split.page_content = f"## {split.metadata['chapter']}\n" + split.page_content
        print("Inserting Documents into Vector Store...")
        self.insert_text_in_vs(md_splits)