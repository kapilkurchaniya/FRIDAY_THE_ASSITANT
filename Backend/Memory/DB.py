import os
import chromadb
from pymongo import MongoClient
from dotenv import dotenv_values

env_vars = dotenv_values('.env')
MONGO_URI = (env_vars.get("MONGO_URI") or "mongodb://localhost:27017/").strip()

# Initialize MongoDB
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
    db = mongo_client["friday_memory"]
    knowledge_graph = db["knowledge_graph"]
    decisions = db["decisions"]
except Exception as e:
    print(f"[ERROR] DB: MongoDB connection failed: {e}")
    db, knowledge_graph, decisions = None, None, None

from chromadb.utils.embedding_functions import CohereEmbeddingFunction, DefaultEmbeddingFunction

# Setup embedding function
CohereAPIKey = (env_vars.get("CohereAPIKey") or "").strip()
if CohereAPIKey and CohereAPIKey != "your_cohere_key_here":
    embed_fn = CohereEmbeddingFunction(api_key=CohereAPIKey, model_name="embed-english-v3.0")
else:
    embed_fn = DefaultEmbeddingFunction()

# Initialize ChromaDB for vector embeddings
try:
    chroma_client = chromadb.PersistentClient(path=os.path.join(os.getcwd(), 'Data', 'chroma_db'))
    memories_collection = chroma_client.get_or_create_collection(name="memories", embedding_function=embed_fn)
except Exception as e:
    print(f"[ERROR] DB: ChromaDB initialization failed. (If 'database is locked', ensure no other instances of Main.py are running): {e}")
    memories_collection = None
