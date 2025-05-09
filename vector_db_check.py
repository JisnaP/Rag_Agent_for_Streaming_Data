from langchain_chroma import Chroma
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings

embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Load persisted vector store
vector_db = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

query = "corrosion-resistant steel"
docs = vector_db.similarity_search(query, k=3)

for i, doc in enumerate(docs, 1):
    print(f"\nResult {i}")
    print("Content:", doc.page_content)
    print("Metadata:", doc.metadata)
