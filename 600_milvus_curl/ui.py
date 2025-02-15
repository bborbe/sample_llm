from typing import Any, Dict

from pydantic import BaseModel
from langchain_core.runnables import RunnableLambda
from langserve import add_routes
from langgraph.graph import StateGraph
from langgraph.graph.graph import END
import torch
from typing_extensions import TypedDict

from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_milvus import Milvus
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv
import os
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
print(f"Using device: {device}")


def load_and_split_documents(urls: list[str]) -> list[Document]:
    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=250, chunk_overlap=0
    )
    return text_splitter.split_documents(docs_list)


def add_documents_to_milvus(
        doc_splits: list[Document], embedding_model: Embeddings, connection_args: Any
):
    vectorstore = Milvus.from_documents(
        documents=doc_splits,
        collection_name="rag_milvus",
        embedding=embedding_model,
        connection_args=connection_args,
    )
    return vectorstore.as_retriever()


# Initialize the components
urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]

doc_splits = load_and_split_documents(urls)
embedding_model = HuggingFaceEmbeddings()
# connection_args = {"uri": "./milvus_rag.db"}
connection_args = {
    "host": "localhost",
    "port": "19530",
}
retriever = add_documents_to_milvus(
    doc_splits, embedding_model, connection_args)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

retrieval_grader_prompt = PromptTemplate(
    template="""You are a grader assessing relevance of a retrieved document to a user question. If the document contains keywords related to the user question, grade it as relevant. It does not need to be a stringent test. The goal is to filter out erroneous retrievals. 
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
    Here is the retrieved document: 
    {document}
    Here is the user question: 
    {question}""",
    input_variables=["question", "document"],
)

answer_prompt = PromptTemplate(
    template="""You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. 
    Use three sentences maximum and keep the answer concise:
    Question: {question} 
    Context: {context} 
    Answer:""",
    input_variables=["question", "context"],
)

hallucination_grader_prompt = PromptTemplate(
    template="""You are a grader assessing whether an answer is grounded in / supported by a set of facts. Give a binary score 'yes' or 'no' score to indicate whether the answer is grounded in / supported by a set of facts. Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
    Here are the facts:
    {documents} 
    Here is the answer: 
    {generation}""",
    input_variables=["generation", "documents"],
)

question_router_prompt = PromptTemplate(
    template="""You are an expert at routing a user question to a vectorstore or web search. Use the vectorstore for questions on LLM agents, prompt engineering, and adversarial attacks. You do not need to be stringent with the keywords in the question related to these topics. Otherwise, use web-search. Give a binary choice 'web_search' or 'vectorstore' based on the question. Return the a JSON with a single key 'datasource' and no preamble or explanation. 
    Question to route: 
    {question}""",
    input_variables=["question"],
)

# local_llm = "llama3"
local_llm = "gemma2:9b"
llm_json = ChatOllama(
    model=local_llm,
    format="json",
    temperature=0,
    model_kwargs={'device': str(device)},
)
llm_str = ChatOllama(
    model=local_llm,
    temperature=0,
    model_kwargs={'device': str(device)},
)

retrieval_grader = retrieval_grader_prompt | llm_json | JsonOutputParser()
hallucination_grader = hallucination_grader_prompt | llm_json | JsonOutputParser()
question_router = question_router_prompt | llm_json | JsonOutputParser()


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = answer_prompt | llm_str | StrOutputParser()


def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    print("---RETRIEVE---")
    question = state["question"]
    documents = retriever.invoke(question)
    return {"documents": [doc.page_content for doc in documents], "question": question}


def generate(state: Dict[str, Any]) -> Dict[str, Any]:
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    generation = rag_chain.invoke(
        {"context": "\n\n".join(documents), "question": question}
    )
    return {"documents": documents, "question": question, "generation": generation}


def grade_documents(state: Dict[str, Any]) -> Dict[str, Any]:
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    filtered_docs = []
    web_search = "No"
    for doc in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": doc})
        if score["score"].lower() == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(doc)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            web_search = "Yes"
    return {"documents": filtered_docs, "question": question, "web_search": web_search}


def web_search(state: Dict[str, Any]) -> Dict[str, Any]:
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state["documents"]
    docs = TavilySearchResults(k=3).invoke({"query": question})
    web_results = "\n".join([d["content"] for d in docs])
    documents.append(web_results)
    return {"documents": documents, "question": question}


def route_question(state: Dict[str, Any]) -> str:
    print("---ROUTE QUESTION---")
    question = state["question"]
    source = question_router.invoke({"question": question})
    return "websearch" if source["datasource"] == "web_search" else "vectorstore"


def decide_to_generate(state: Dict[str, Any]) -> str:
    print("---ASSESS GRADED DOCUMENTS---")
    return "websearch" if state["web_search"] == "Yes" else "generate"


def grade_generation_v_documents_and_question(state: Dict[str, Any]) -> str:
    print("---CHECK HALLUCINATIONS---")
    score = hallucination_grader.invoke(
        {"documents": state["documents"], "generation": state["generation"]}
    )
    return "useful" if score["score"] == "yes" else "not supported"


# Define Pydantic model for request body
class QuestionRequest(BaseModel):
    question: str


class GraphState(TypedDict):
    question: str
    generation: str
    web_search: str
    documents: list[str]


# Define the LangGraph workflow
workflow = StateGraph(GraphState)
workflow.add_node("websearch", web_search)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)

workflow.set_conditional_entry_point(
    route_question,
    {
        "websearch": "websearch",
        "vectorstore": "retrieve",
    },
)

workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "websearch": "websearch",
        "generate": "generate",
    },
)
workflow.add_edge("websearch", "generate")
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",
        "useful": END,
        "not useful": "websearch",
    },
)

# Compile the workflow
compiled_workflow = workflow.compile()

# app config
st.set_page_config(page_title="Streaming bot", page_icon="🤖")
st.title("Streaming bot")


def get_response(user_query, chat_history):
    state = {
        "question": user_query,
        "documents": [],
        "generation": "",
        "web_search": "",
        "chat_history": chat_history,
    }
    return compiled_workflow.stream(state)


# session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello, I am a bot. How can I help you?"),
    ]

# conversation
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)

# user input
user_query = st.chat_input("Type your message here...")
if user_query is not None and user_query != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    with st.chat_message("Human"):
        st.markdown(user_query)

    with st.chat_message("AI"):
        response = st.write_stream(get_response(user_query, st.session_state.chat_history))

    st.session_state.chat_history.append(AIMessage(content=response))
