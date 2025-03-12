import chainlit as cl
from chainlit.input_widget import Select, Switch
from chainlit.element import Element

from app.scraper.papermage_scraper import PapermageScraper
from app.processor.langchain_processor import LangchainProcessor
from app.scraper.scraper import Scraper, ImageData
from app.scripts.utils import (
    calculate_hash, does_file_exist, save_file_to_db, delete_file_from_db, get_avaliable_papers
)
from app.prompts import (
    rewrite_chat_prompt, rewrite_parser, rag_chat_prompt, multimodal_rag_chat_prompt
)
from app.config_loader import ConfigLoader

from typing import List, Tuple
import base64

import sqlite3
from qdrant_client import QdrantClient, models
from langchain_community.chat_models import ChatLiteLLM
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser

from transformers import AutoModel, AutoImageProcessor

async def rewrite_query(user_query: str, chat_history: List[BaseMessage]) -> str:
    """Rewrite the user query based on the chat history."""

    def generate_history_str(chat_history : List[BaseMessage]) -> str:
        """Generate history string based on the chat history."""
        history_str = ""
        for i, msg in enumerate(chat_history):
            if isinstance(msg, HumanMessage):
                history_str += f"USER: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                history_str += f"ASSISTANT: {msg.content}\n"
        return history_str

    rewrite_chain = cl.user_session.get("rewrite_chain")
    msg_num = cl.user_session.get("configs")['agent_config']['msg_history_len']
    relevant_history = chat_history if len(chat_history) <= msg_num else chat_history[-msg_num:]
    message_history_str = generate_history_str(relevant_history)
    rewrite_res = rewrite_chain.invoke(
        {'user_query': user_query, 'user_assistant_conversation': message_history_str}
    )
    return rewrite_res['rewritten_query']

async def generate_context_str(vector_store: QdrantVectorStore, 
                               query: str, 
                               k : int, 
                               paper_id : str, 
                               include_paper_info : bool) -> str:
    """Generate context string based on the query."""

    def get_paper_info(paper_id: str) -> str:
        """Get paper info based on the paper_id."""
        conn = cl.user_session.get("db_conn")
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM paper_info WHERE id=?", (paper_id,))
        result = cursor.fetchone()
        if result: return result[0]
        print("ERROR: PAPER INFO NOT FOUND!")
        return ""
    
    context_str = ""
    if include_paper_info:
        paper_info = get_paper_info(paper_id)
        context_str += f"PAPER INFO:\n{paper_info}\n{'='*25}\n"
    docs = await retrieve_context(vector_store, query, k, paper_id)
    for i, doc in enumerate(docs):
        context_str += f"CHUNK {i} - FROM CHAPTER {doc.metadata.get('chapter', 'UNKNOWN')}\n{doc.page_content}\n{'='*25}\n"
    return context_str

async def handle_pdf(file_id : str, element: Element) -> bool:
    """Full pipeline of PDF processing."""
    conn = cl.user_session.get("db_conn")
    await cl.Message(content=f"Processing document \"{element.name}\"...").send()
    
    try:
        # step 1. add file to sqlite db if not processed
        if await does_file_exist(conn, file_id):
            await cl.Message(content="This file has already been processed!").send()
            return False
        await save_file_to_db(conn, file_id, element.name)
        
        # step 2. convert pdf to markdown, extract figures and captions
        scraper = cl.user_session.get("scraper")
        md, img_data = await process_pdf(scraper, element.path)

        # step 3. process md, img_data
        processor = LangchainProcessor(
            md,
            img_data,
            file_id,
            conn,
            cl.user_session.get("text_vs"),
            cl.user_session.get("img_emb"),
            cl.user_session.get("img_proc")
        )
        res = await send_file(processor)
        if not res:
            raise Exception("Something went wrong while processing the document!")

        # step 4. add new paper to settings
        papers = await get_avaliable_papers(conn)
        new_settings = await generate_settings(papers)
        cl.user_session.set("paper_settings", new_settings)

        await cl.Message(content=f"Document \"{element.name}\" processed!").send()
        return True
    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()
        await delete_file_from_db(conn, file_id)
        return False

async def generate_settings(papers: List[Tuple[str, str]]) -> cl.ChatSettings:
    proc_papers_list = [f"{paper[0]} - {paper[1]}" for paper in papers]
    settings = await cl.ChatSettings(
        [
            Select(
                id="paper",
                label="Select a paper",
                values=proc_papers_list,
                initial_index=0
            ),
            Switch(id="img_search", label="Use chapter-wide Image search", initial=True),
            Switch(id="paper_info", label="Add paper info to context", initial=True)
        ]
    ).send()
    return settings

## -- CHAINLIT TOOLS -- ##

@cl.step(type="tool")
async def retrieve_context(vector_store : QdrantVectorStore, query : str, k : int, paper_id : str) -> str:
    docs = await cl.make_async(vector_store.similarity_search)(
        query=query,
        k=k,
        filter=models.Filter(
            must=[
                models.FieldCondition(key="metadata.paper_id", match=models.MatchValue(value=paper_id))
            ]
        )
    )
    return docs

@cl.step(type="tool")
async def process_pdf(scraper : Scraper, file_path : str) -> Tuple[str, ImageData]:
    return await cl.make_async(scraper.process_document)(file_path)

@cl.step(type="tool")
async def send_file(processor : LangchainProcessor) -> bool:
    try:
        # Process directly without cl.make_async since LangchainProcessor
        # contains sqlite3.Connection which cannot be pickled
        processor.process()
        return True
    except Exception as e:
        print(e)
        return False

## -- CHAINLIT MAIN FUNCITONS -- ##

@cl.on_chat_start
async def on_chat_start():

    conn = sqlite3.connect("app/storage/sqlite/contents.db")
    cl.user_session.set("db_conn", conn)
    configs = ConfigLoader().get_config()
    cl.user_session.set("configs", configs)
    cl.user_session.set("scraper", PapermageScraper())


    text_embed = OllamaEmbeddings(model=configs['embedding_config']['model'])
    cl.user_session.set("text_embed", text_embed)
    qdrant_client = QdrantClient(path='app/storage/qdrant/vectorstore')
    text_vs : VectorStore = QdrantVectorStore(
        client=qdrant_client,
        collection_name=configs['qdrant_config']['text_collection_name'],
        embedding=text_embed
    )
    image_vs : VectorStore = QdrantVectorStore(
        client=qdrant_client,
        collection_name=configs['qdrant_config']['image_collection_name'],
        embedding=text_embed
    )
    cl.user_session.set("text_vs", text_vs)
    cl.user_session.set("image_vs", image_vs)
    img_proc = AutoImageProcessor.from_pretrained("nomic-ai/nomic-embed-vision-v1.5")
    img_emb = AutoModel.from_pretrained("nomic-ai/nomic-embed-vision-v1.5", trust_remote_code=True)
    cl.user_session.set("img_proc", img_proc)
    cl.user_session.set("img_emb", img_emb)

    cl.user_session.set("chat_history", [])

    chat_llm = ChatLiteLLM(
        model=configs['agent_config']['model_name'], 
        temperature=configs['agent_config']['temperature'],
    )
    cl.user_session.set("chat_llm", chat_llm)

    rewrite_chain = rewrite_chat_prompt | chat_llm | rewrite_parser
    cl.user_session.set("rewrite_chain", rewrite_chain)

    rag_chain = rag_chat_prompt | chat_llm | StrOutputParser()
    cl.user_session.set("rag_chain", rag_chain)

    multimodal_rag_chain = multimodal_rag_chat_prompt | chat_llm | StrOutputParser()
    cl.user_session.set("multimodal_rag_chain", multimodal_rag_chain)

    papers = await get_avaliable_papers(conn)
    if len(papers) == 0:
        while True:
            files = await cl.AskFileMessage(
                content="Please upload a PDF file to begin!", 
                accept=["application/pdf"],
                max_size_mb=50
            ).send()
            if files: break
        # process the file
        await main(cl.Message(content='',elements=[Element(mime='pdf', name=files[0].name, path=files[0].path)]))
    else:
        papers = await get_avaliable_papers(conn)
        settings = await generate_settings(papers)
        cl.user_session.set("paper_settings", settings)
        await cl.Message(content=f"Hi! Select a paper from the list to start asking questions.").send()

@cl.on_message
async def main(message: cl.Message):
    
    img_data = None
    img_element = None

    if message.elements:
        for element in message.elements:
            if element.mime == 'pdf':
                file_id = await calculate_hash(open(element.path, "rb").read())
                res = await handle_pdf(file_id, element)
                return
            elif element.mime == 'image':
                with open(element.path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode("utf-8")

    # handle message
    paper_id = cl.user_session.get("paper_settings")['paper'].split(" - ")[0]
    user_msg = message.content
    chat_history = cl.user_session.get("chat_history")
    if len(chat_history) > 1:
        user_msg = rewrite_query(user_msg, chat_history)
        print(f"User query rewritten: {user_msg}")

    if img_data is None:
        img_docs = await retrieve_context(
            cl.user_session.get("image_vs"), 
            user_msg, 
            1, # TODO add k
            paper_id
        )
        if img_docs:
            # TODO choose relevant image
            img_doc = img_docs[0]
            with open(img_doc.metadata['path'], "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            image_element = cl.Image(path=img_doc.metadata['path'], name="Retrieved Image", display="inline")
    
    context_str = await generate_context_str(
        cl.user_session.get("text_vs"), 
        user_msg, 
        cl.user_session.get("configs")['agent_config']['k'], 
        paper_id,
        cl.user_session.get("paper_settings")['paper_info']
    )

    response = ''
    if img_data:
        multimodal_rag_chain = cl.user_session.get("multimodal_rag_chain")
        response = multimodal_rag_chain.invoke(
            # TODO add image data (caption)
            {'context': context_str, 'user_query': user_msg, 'image_data': img_data}
        )
    await cl.Message(
        content=response, 
        elements=[image_element] if image_element else []
    ).send()

    chat_history.append(HumanMessage(content=user_msg))
    chat_history.append(AIMessage(content=response))
        