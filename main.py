import chainlit as cl

@cl.on_chat_start
async def on_chat_start():

    await cl.Message(content="Hi, I'm PaperSage! Send a file to start or check from the list of processed files.").send()

@cl.on_message
async def main(message: cl.Message):
    await cl.Message(content="Temp message!").send()