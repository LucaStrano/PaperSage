import chainlit as cl
from papermage.recipes import CoreRecipe
import psycopg2 as pg
import os

@cl.on_chat_start
async def on_chat_start():

    recipe = CoreRecipe()

    db_name = os.environ.get("POSTGRES_DB")
    db_user = os.environ.get("POSTGRES_USER")
    db_password = os.environ.get("POSTGRES_PASSWORD")

    # Ensure environment variables are set
    if not db_name or not db_user or not db_password:
        raise ValueError("Database environment variables are not set")
    
    connection = pg.connect(
        database=db_name,
        user=db_user,
        password=db_password,
        host="localhost",
        port="5432"
    )
    cursor = connection.cursor()

    cl.user_session.set("recipe", recipe)
    cl.user_session.set("connection", connection)
    cl.user_session.set("cursor", cursor)