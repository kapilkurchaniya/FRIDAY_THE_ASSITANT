import os
import chromadb
from pymongo import MongoClient
from dotenv import dotenv_values

env_vars = dotenv_values('.env')
MONGO_URI = env_vars.get("MONGO_URI", "mongodb://localhost:27017/")

# Initialize MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["friday_memory"]
    knowledge_graph = db["knowledge_graph"]
    decisions = db["decisions"]
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    db, knowledge_graph, decisions = None, None, None

from chromadb.utils.embedding_functions import CohereEmbeddingFunction, DefaultEmbeddingFunction

# Setup embedding function
CohereAPIKey = env_vars.get("CohereAPIKey")
if CohereAPIKey and CohereAPIKey != "your_cohere_key_here":
    embed_fn = CohereEmbeddingFunction(api_key=CohereAPIKey, model_name="embed-english-v3.0")
else:
    embed_fn = DefaultEmbeddingFunction()

# Initialize ChromaDB for vector embeddings
try:
    chroma_client = chromadb.PersistentClient(path=os.path.join(os.getcwd(), 'Data', 'chroma_db'))
    memories_collection = chroma_client.get_or_create_collection(name="memories", embedding_function=embed_fn)
except Exception as e:
    print(f"ChromaDB initialization failed: {e}")
    memories_collection = None
