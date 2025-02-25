import chainlit as cl
from app.scraper.papermage_scraper import PapermageScraper
from app.scraper.scraper import Scraper, ImageData
from app.scripts.utils import calculate_hash, does_file_exist, save_file_to_db
from typing import Tuple
import asyncio
from functools import partial
import sqlite3

@cl.step(type="tool")
async def scrape_pdf(scraper : Scraper, file_path : str) -> Tuple[str, ImageData]:
    return scraper.process_document(document_path=file_path)

@cl.on_chat_start
async def on_chat_start():
    conn = sqlite3.connect("app/storage/sqlite/contents.db")
    cl.user_session.set("db_conn", conn)
    cl.user_session.set("scraper", PapermageScraper())
    await cl.Message(content="Hi, I'm PaperSage! Send a file to start or check from the list of processed files.").send()

@cl.on_message
async def main(message: cl.Message):
    if len(message.elements) > 0:
        for element in message.elements:
            file_path = element.path
            if file_path is not None:
                try:
                    processing_msg = cl.Message(content=f"Processing document \"{element.name}\"...")
                    await processing_msg.send()

                    # step 1. add file to sqlite db if not processed
                    conn = cl.user_session.get("db_conn")
                    cursor = conn.cursor()
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                    file_id = await calculate_hash(file_content)
                    if await does_file_exist(cursor, file_id):
                        await cl.Message(content="This file has already been processed!").send()
                        return
                    await save_file_to_db(cursor, conn, file_id, element.name)
                    

                    # step 2. convert pdf to markdown, extract figures and captions
                    scraper = cl.user_session.get("scraper")
                    md, img_data = await scrape_pdf(scraper, file_path)

                    # step 3. process md, img_data
                    # TODO
                    
                    # Update processing message to show completion
                    processing_msg.content = f"Document \"{element.name}\" processed!"
                    await processing_msg.update()
                    
                except Exception as e:
                    await cl.Message(content=f"Error processing document: {str(e)}").send()