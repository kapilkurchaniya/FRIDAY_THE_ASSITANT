import json
import uuid
import datetime
from groq import Groq
from dotenv import dotenv_values
from Backend.Memory.DB import memories_collection, knowledge_graph, decisions

env_vars = dotenv_values('.env')
GroqAPIKey = (env_vars.get("GroqAPIKey") or "").strip()
client = Groq(api_key=GroqAPIKey, timeout=20, max_retries=0) if GroqAPIKey else None

def extract_memory(user_msg: str, assistant_reply: str):
    """
    Extracts facts and knowledge graph triples from a conversation turn
    and stores them in MongoDB and ChromaDB.
    """
    if not client: return
    
    prompt = f"""
    Analyze the following conversation turn between a User and their Personal AI Companion (FRIDAY).
    Extract important facts, preferences, decisions, and knowledge graph relationships.
    Format your response EXACTLY as a JSON object with the following keys:
    - "facts": [List of string facts about the user or their current context]
    - "knowledge_graph": [List of triples in the format [Subject, Predicate, Object]]
    - "decisions": [List of explicit decisions or preferences stated by the user]
    
    If there is nothing important to remember, return empty lists.
    
    User: {user_msg}
    FRIDAY: {assistant_reply}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(completion.choices[0].message.content)
        
        # 1. Store Facts in ChromaDB (semantic memory)
        facts = result.get("facts", [])
        if facts and memories_collection is not None:
            ids = [str(uuid.uuid4()) for _ in facts]
            metadatas = [{"timestamp": str(datetime.datetime.now())} for _ in facts]
            memories_collection.add(documents=facts, metadatas=metadatas, ids=ids)
            print(f"[Memory] Saved {len(facts)} facts to ChromaDB")
            
        # 2. Store KG in MongoDB
        kg = result.get("knowledge_graph", [])
        if kg and knowledge_graph is not None:
            for triple in kg:
                if len(triple) == 3:
                    knowledge_graph.update_one(
                        {"subject": triple[0], "predicate": triple[1], "object": triple[2]},
                        {"$set": {"timestamp": datetime.datetime.now()}},
                        upsert=True
                    )
            print(f"[Memory] Saved {len(kg)} relationships to MongoDB")
                    
        # 3. Store Decisions in MongoDB
        decs = result.get("decisions", [])
        if decs and decisions is not None:
            for dec in decs:
                decisions.insert_one({"decision": dec, "timestamp": datetime.datetime.now()})
            print(f"[Memory] Saved {len(decs)} decisions to MongoDB")
                
    except Exception as e:
        print(f"Memory extraction failed: {e}")
