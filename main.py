import chainlit as cl
from chainlit.input_widget import Select
from app.scraper.papermage_scraper import PapermageScraper
from app.scraper.scraper import Scraper, ImageData
from app.scripts.utils import calculate_hash, does_file_exist, save_file_to_db
from typing import Tuple
import asyncio
from functools import partial
import sqlite3
from typing import List

## -- UTILITY FUNCTIONS -- ##

async def get_avaliable_papers(connection: sqlite3.Connection) -> List[Tuple[str, str]]:
    cursor = connection.cursor()
    cursor.execute("SELECT id, name FROM papers")
    papers = cursor.fetchall()
    return papers

async def generate_settings(papers: List[Tuple[str, str]]) -> cl.ChatSettings:
    proc_papers_list = [f"{paper[0]} - {paper[1]}" for paper in papers]
    settings = await cl.ChatSettings(
        [
            Select(
                id="paper",
                label="Select a paper",
                values=proc_papers_list,
                initial_index=0
            )
        ]
    ).send()
    return settings

## -- CHAINLIT TOOLS -- ##

@cl.step(type="tool")
async def process_pdf(scraper : Scraper, file_path : str) -> Tuple[str, ImageData]:
    return scraper.process_document(document_path=file_path)

## -- CHAINLIT MAIN FUNCITONS -- ##

@cl.on_chat_start
async def on_chat_start():

    conn = sqlite3.connect("app/storage/sqlite/contents.db")
    cl.user_session.set("db_conn", conn)
    cl.user_session.set("scraper", PapermageScraper())

    await cl.Message(content="Hi, I'm PaperSage! Send a file to start or select one from the list of processed files.").send()

    papers = await get_avaliable_papers(conn)
    if len(papers) > 0:
        papers = await get_avaliable_papers(conn)
        settings = await generate_settings(papers)
        cl.user_session.set("paper_settings", settings)
        proc_papers_str = "\n".join(f"{i+1}. {paper[0]} - {paper[1]}" for i, paper in enumerate(papers))
        await cl.Message(content=f"Here are the files you have processed:\n {proc_papers_str}").send()

@cl.on_message
async def main(message: cl.Message):
    if message.elements:
        for element in message.elements:
            if element.mime == 'pdf':
                file_path = element.path
                try:

                    await cl.Message(content=f"Processing document \"{element.name}\"...").send()
                    
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
                    md, img_data = await process_pdf(scraper, file_path)

                    # step 3. process md, img_data
                    # TODO

                    # step 4. add new paper to settings
                    papers = await get_avaliable_papers(conn)
                    new_settings = await generate_settings(papers)
                    cl.user_session.set("paper_settings", new_settings)

                    await cl.Message(content=f"Document \"{element.name}\" processed!").send()
                    
                except Exception as e:
                    await cl.Message(content=f"Error processing document: {str(e)}").send()
    else:
        await cl.Message(content=f"Textual Message Received!").send()