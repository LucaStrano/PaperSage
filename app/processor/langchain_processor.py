from app.processor.processor import Processor
from app.scraper.scraper import ImageData
from app.scripts.utils import embed_image
from typing import List, Any
from qdrant_client import QdrantClient, models
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
from sqlite3 import Connection
import re
from uuid import uuid4
import os


class LangchainProcessor(Processor):
    """
    Langchain Processor Implementation.
    """    
    
    def __init__(self, md_data : str, 
                 image_data : ImageData, 
                 paper_id : str, 
                 sql_conn : Connection, 
                 text_vector_store : QdrantVectorStore,
                 img_emb : Any,
                 img_proc : Any):
        super().__init__(md_data, image_data, paper_id, sql_conn, text_vector_store, img_emb, img_proc)
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


    def create_split_metadata(self, md_splits : List[Document]) -> List[str]:
        """
        Creates metadata for each split. Modifies the Document object in place.
        Args:
            md_splits (List[Document]): List of Document objects.
        Returns:
            List[str]: List of UUIDs.
        """
        chapter_num_regex = r'\b\d+(?:\.\d+)*\b'
        fig_ref_ids_regex = r'(?i)\b(?:Figure|Fig\.?) (\d+(?:\.\d+)*)\b'
        uuids = [str(uuid4()) for _ in range(len(md_splits))]
        for i, split in enumerate(md_splits):
            split.metadata['paper_id'] = self.paper_id
            # extract chapter id
            if 'chapter' in split.metadata.keys():
                chapter_id = re.findall(chapter_num_regex, split.metadata['chapter'])
                if chapter_id: split.metadata['chapter_id'] = chapter_id[0]
            # extract figure reference ids
            split.metadata['fig_ref_ids'] = re.findall(fig_ref_ids_regex, split.page_content)
            # next and previous split ids
            if i > 0:
                split.metadata['prev_id'] = uuids[i - 1]
                md_splits[i - 1].metadata['next_id'] = uuids[i]
        return uuids

                
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

    
    def insert_texts_in_vs(self, splits : List[Document], uuids : List[str]) -> None:
        """
        Inserts text data into the Qdrant Vector Store.
        Args:
            splits (List[Document]): List of Document objects.
        """
        if self.configs['embedding_config']['use_prefix']:
            prefix = self.configs['embedding_config']['document_prefix']
            points = [
                models.PointStruct(
                    id=uuids[i],
                    payload={'metadata': split.metadata, 'page_content': split.page_content},
                    vector=self.text_vs.embeddings.embed_query(prefix+split.page_content)
                )
                for i, split in enumerate(splits)
            ]
            self.text_vs.client.upsert(
                collection_name=self.configs['qdrant_config']['text_collection_name'],
                points=points
            )
        else:
            self.text_vs.add_documents(splits, ids=uuids)

    def save_images(self) -> List[str]:
        """
        Saves images in Save path.
        Returns:
            List[str]: List of image paths.
        """
        img_paths = []
        base_path = os.path.join('app', 'storage', 'images', self.paper_id)
        os.makedirs(base_path, exist_ok=True) # Create directory with paper id
        for img, mdt in self.image_data:
            img_name = f"fig_{mdt['page_id']}_{mdt['fig_id']}.png"
            img_path = os.path.join(base_path, img_name)
            img_paths.append(img_path)
            img.save(img_path)
        return img_paths

    def create_image_metadata(self, img_paths : List[str]) -> None:
        """
        Creates metadata for each image. Modifies the ImageData object in place.
        Args:
            img_paths (List[str]): List of image paths.
        """
        for i, (img, mdt) in enumerate(self.image_data):
            mdt['paper_id'] = self.paper_id
            mdt['path'] = img_paths[i]
            if 'caption' in mdt.keys(): # add figure reference id
                ref_id = re.findall(r'(?i)\b(?:Figure|Fig\.?) (\d+(?:\.\d+)*)\b', mdt['caption'])
                if ref_id: mdt['fig_ref_id'] = ref_id[0]

    def insert_images_in_vs(self) -> None:
        """
        Inserts image data into the Qdrant Vector Store.
        """
        qdrant_client : QdrantClient = self.text_vs.client
        points = [
            models.PointStruct(
                id=str(uuid4()),
                payload={'metadata': mdt, 'page_content': mdt['caption'] if 'caption' in mdt.keys() else ''},
                vector=embed_image(img, self.img_emb, self.img_proc)
            )
            for (img, mdt) in self.image_data
        ]
        qdrant_client.upsert(
            collection_name=self.configs['qdrant_config']['image_collection_name'],
            points=points
        )
            
    def process(self) -> None:

        # process markdown data
        print("Processing markdown data...")
        md_splits = self.split_md_data()
        self.insert_paper_info(md_splits[0])
        md_splits.pop(0) # Remove paper info from the list
        print("Total Splits to insert: ", len(md_splits))
        print("Creating Split Metadata...")
        uuids = self.create_split_metadata(md_splits)
        if self.configs['chunking_config']['add_section_titles']:
            for split in md_splits:
                if 'chapter' in split.metadata.keys() and self.configs['chunking_config']['add_section_titles']:
                    split.page_content = f"## {split.metadata['chapter']}\n" + split.page_content
        print("Inserting Documents into Vector Store...")
        self.insert_texts_in_vs(md_splits, uuids)

        # process image data
        print("Processing image data...")
        print("Saving Images...")
        img_paths = self.save_images()
        print("Creating Image Metadata...")
        self.create_image_metadata(img_paths)
        self.insert_images_in_vs()