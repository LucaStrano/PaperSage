from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

# -- QUERY REWRITING --

class RewriteOutput(BaseModel):
    rewritten_query: str = Field(description="Rewritten query based on the user query and conversation history.")

rewrite_system_prompt = """\
# Role

You are an expert in performing query rewriting for retrieval-augmented search. Your goal is to rewrite a given user query using relevant context from past user-assistant interactions to improve search accuracy in a vector store.
Input:
 - New Query: The latest user query that needs rewriting.
 - Conversation History: A sequence of past user and assistant messages relevant to the query.

# Instructions

Rewrite the New Query so that it is clear, self-contained, and contextually enriched using the most relevant details from the Conversation History. The rewritten query should:
 1. Retain the original intent of the user's query.
 2. Incorporate necessary context from past messages to disambiguate or refine the request. Avoid adding irrelevant or excessive information. Be concise and well-formed, think about optimizing retrieval in a vector store.
 3. If the query doesn't require any rewriting, output the user query AS IS, without any modifications.
"""

rewrite_user_prompt = """\
# Inputs

Past User-Assistant Conversation:
{user_assistant_conversation}

User Query:
{user_query}

# Output Instructions

{output_instructions}
"""

rewrite_parser = JsonOutputParser(pydantic_object=RewriteOutput)

rewrite_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", rewrite_system_prompt),
    ("human", rewrite_user_prompt),
]).partial(output_instructions=rewrite_parser.get_format_instructions())