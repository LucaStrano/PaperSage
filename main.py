import chainlit as cl
from app.scraper.papermage_scraper import PapermageScraper
import asyncio
from functools import partial

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
                    processing_msg = await cl.Message(content=f"Processing document \"{element.name}\"...").send()
                    
                    # Get scraper instance
                    scraper = cl.user_session.get("scraper")
                    
                    # Run process_document in a thread pool since it's CPU-intensive
                    loop = asyncio.get_event_loop()
                    md, img_data = await loop.run_in_executor(
                        None,
                        partial(scraper.process_document, file_path)
                    )
                    
                    # Update processing message to show completion
                    await processing_msg.update(content=f"Successfully processed document \"{element.name}\"!")
                    
                    # TODO handle markdown and image_data
                    
                except Exception as e:
                    await cl.Message(content=f"Error processing document: {str(e)}").send()