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
 - User Query: The latest user query that needs rewriting.
 - Conversation History: A sequence of past user and assistant messages relevant to the query.

# Instructions

Rewrite the User Query so that it is clear, self-contained, and contextually enriched using the most relevant details from the Conversation History. The rewritten query should:
 1. Rewrite the user query only if the user is referring to past messages. Do not rewrite if the query is self-contained or referring to new context. If the query doesn't require any rewriting, output the user query AS IS, without any modifications.
 2. Retain the original intent of the user's query.
 3. Incorporate necessary context from past messages to disambiguate or refine the request. Be concise and well-formed, think about optimizing retrieval in a vector store.
"""

rewrite_user_prompt = """\
# Inputs

Conversation History:
{user_assistant_conversation}

User Query:
{user_query}

# Output Instructions

{output_instructions}
"""

rewrite_parser = JsonOutputParser(pydantic_object=RewriteOutput)

rewrite_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", rewrite_system_prompt),
    ("user", rewrite_user_prompt),
]).partial(output_instructions=rewrite_parser.get_format_instructions())

# -- RAG PROMPT --

rag_system_prompt = """\
# Role 

You are an expert AI assistant tasked with answering user queries based on retrieved information from a scientific publication.
Input:
    - Context: Relevant text chunks retrieved from the scientific paper.
	- Optional Image: An image (if available) that may aid in answering the query..
	- User Query: The question that needs to be answered.

# Instructions

	1. Answer only using the provided context. If the context contains sufficient information to answer the query, provide a precise, well-structured response.
	2. If the context does not provide a clear answer, do not generate speculative or inferred responses. Instead, state that the information is not available.
	3. Cite relevant portions of the context when necessary. If the answer is derived from a specific part of the paper, reference that information concisely.
	4. If an image is provided, interpret it where applicable to support the answer, but do not make assumptions beyond what is evident.
"""

rag_user_prompt = """\
# Inputs

Context:
{context}

User Query:
{user_query}
"""

rag_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", rag_system_prompt),
    ("user", rag_user_prompt),
])

multimodal_rag_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", rag_system_prompt),
    ("user", [
        {
            "type": "image_url",
            "image_url": {"url": "data:image/png;base64,{image_data}"},
        },
        {
            "type": "text",
            "text": rag_user_prompt
        }
    ])
])