import chainlit as cl
from app.scraper.papermage_scraper import PapermageScraper
from app.scraper.scraper import Scraper, ImageData
from typing import Tuple
import asyncio
from functools import partial

@cl.step(type="tool")
async def scrape_pdf(scraper : Scraper, file_path : str) -> Tuple[str, ImageData]:
    return scraper.process_document(document_path=file_path)

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("scraper", PapermageScraper())
    await cl.Message(content="Hi, I'm PaperSage! Send a file to start or check from the list of processed files.").send()

@cl.on_message
async def main(message: cl.Message):
    if len(message.elements) > 0:
        for element in message.elements:
            file_path = element.path
            if file_path is not None:
                try:
                    processing_msg = await cl.Message(content=f"Processing document \"{element.name}\"...")
                    processing_msg.send()

                    # step 1. convert pdf to markdown, extract figures and captions
                    scraper = cl.user_session.get("scraper")
                    md, img_data = await scrape_pdf(scraper, file_path)

                    # step 2. process md, img_data
                    # TODO
                    
                    # Update processing message to show completion
                    processing_msg.content = f"Document \"{element.name}\" processed!"
                    await processing_msg.update()
                    
                except Exception as e:
                    await cl.Message(content=f"Error processing document: {str(e)}").send()