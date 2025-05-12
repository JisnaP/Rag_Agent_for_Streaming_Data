import os
from dotenv import load_dotenv

from langchain_community.vectorstores import Chroma
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
import asyncio
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]
async def initialize_agent():
    # Load environment variables
    load_dotenv()
    OPENAI_KEY = os.getenv("OPENAI_KEY")
    os.environ['OPENAI_API_KEY']=OPENAI_KEY
    
    

    # Initialize LLM and embeddings
    llm = ChatOpenAI(model="gpt-3.5-turbo",api_key=OPENAI_KEY)
    #embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # Define tools
    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query."""
        vector_store = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
        retrieved_docs = vector_store.similarity_search(query, k=2)
        print(f"Retrieved docs: {retrieved_docs}")
        serialized = "\n\n".join(
            f"Source: {doc.metadata}\nContent: {doc.page_content}"
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    

    # Define graph builder
    graph_builder = StateGraph(MessagesState)

    # Define query_or_respond function
    async def query_or_respond(state: MessagesState):
        """Generate tool call for retrieval or respond."""
        llm_with_tools = llm.bind_tools([retrieve])
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    # Define generate function
    async def generate(state: MessagesState):
        """Generate answer."""
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        f"{docs_content}"
        )
        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system") or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + conversation_messages
        response = await llm.ainvoke(prompt)
        return {"messages": [response]}

    # Build the graph
    graph_builder.add_node("query_or_respond", query_or_respond)
    graph_builder.add_node("tools", ToolNode([retrieve]))
    graph_builder.add_node("generate", generate)
    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", END)

    # Compile the graph with memory
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

   
    return graph

    

import asyncio

if __name__ == '__main__':
    async def main():
        config = {"configurable": {"thread_id": "def234"}}
        graph = await initialize_agent()

        input_message = (
            "What recent notices mention ‘corrosion-resistant steel’? summarize them for me?\n\n"
            "What did the Securities and Exchange Commission publish this week"
        )

       
        async for step in graph.astream(
            {"messages": [{"role": "user", "content": input_message}]},
            stream_mode="values",
            config=config,
        ):
            step["messages"][-1].pretty_print()

    asyncio.run(main())
