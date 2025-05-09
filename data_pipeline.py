import os
import aiohttp
import asyncio
import logging

from datetime import datetime, timedelta
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma





logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_documents(api_url, from_date=None, to_date=None, per_page=100, **params):
    try:
        if not from_date:
            from_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")

        documents = []
        page = 1
        has_more = True

        while has_more:
            if "federalregister.gov" in api_url:
                query_params = {
                    "per_page": per_page,
                    "order": "newest",
                    "page": page,
                    "conditions[publication_date][gte]": from_date,
                    "conditions[publication_date][lte]": to_date
                }
            else:
                query_params = {
                    "from_date": from_date,
                    "to_date": to_date,
                    "limit": per_page,
                    "page": page
                }

            query_params.update(params)

            logger.info(f"Fetching page {page} from {api_url} ({from_date} to {to_date})")

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=query_params) as response:
                    

                    if response.status != 200:
                        logger.error(f"Error fetching from {api_url}: Status {response.status}")
                        
                        return documents

                    data = await response.json()
                    page_docs = data.get("results", [])

                    documents.extend(page_docs)
                    logger.info(f"Fetched {len(page_docs)} documents on page {page}")
                    import json
                    print(json.dumps(documents[0], indent=2))
                    has_more = len(page_docs) == per_page
                    page += 1

        return documents

    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        
        return []
    


async def process_document(doc, source_id="federal_register"):
    # Use title as fallback if abstract is null
    content = doc.get("abstract") or doc.get("title") or "No content available"
    
    metadata = {
        "source": source_id,
        "doc_id": doc.get("document_number"),
        "title": doc.get("title"),
        "type": doc.get("type"),
        "url": doc.get("html_url"),
        "pdf_url": doc.get("pdf_url"),
        "publication_date": doc.get("publication_date"),
        "agency": doc.get("agencies", [{}])[0].get("name", "Unknown")
    }

    return Document(page_content=content, metadata=metadata)





async def ingest_pipeline(API_URL):
    logger.info("Running ingestion pipeline...")
    raw_docs = await fetch_documents(API_URL)

    processed_docs = [await process_document(doc) for doc in raw_docs]

    for doc in processed_docs:
     print(f"Page content: {doc.page_content}")
     print(f"Metadata: {doc.metadata}")
   

    # Filter out Nones
    
    
    logger.info(f"Total documents processed: {len(processed_docs)}")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(processed_docs)
    print(f"Length of all_splits :{len(all_splits)}")
    # Embed and store using LangChain
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
   
    vector_db = Chroma.from_documents(all_splits,persist_directory="chroma_db",embedding=embeddings
                                      )
   
    
    
    
    logger.info("Ingestion complete and vector store persisted.")
if __name__ == "__main__":
    API_URL='https://www.federalregister.gov/api/v1/documents.json'
    asyncio.run(ingest_pipeline(API_URL))