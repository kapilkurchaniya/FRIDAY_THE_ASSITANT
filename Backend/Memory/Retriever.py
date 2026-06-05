from Backend.Memory.DB import memories_collection, knowledge_graph, decisions

def retrieve_context(query: str, n_results: int = 5) -> str:
    """
    Retrieves semantic memories from ChromaDB and related Knowledge Graph triples from MongoDB.
    Formats them into a context string to be injected into the LLM prompt.
    """
    context = ""
    
    # 1. Semantic Search from ChromaDB
    if memories_collection is not None:
        try:
            results = memories_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            if results and 'documents' in results and results['documents'] and results['documents'][0]:
                facts = results['documents'][0]
                if facts:
                    context += "Relevant Facts from Memory:\n"
                    for fact in facts:
                        context += f"- {fact}\n"
        except Exception as e:
            print(f"ChromaDB retrieval error: {e}")
            
    # 2. Keyword Search in Knowledge Graph and Decisions (MongoDB)
    # A simple but effective way to trigger graph recall based on query words
    words = [w.lower() for w in query.replace('?', '').replace('.', '').replace(',', '').split() if len(w) > 3]
    
    if knowledge_graph is not None and words:
        try:
            regex_pattern = "|".join(words)
            triples = list(knowledge_graph.find({
                "$or": [
                    {"subject": {"$regex": regex_pattern, "$options": "i"}},
                    {"object": {"$regex": regex_pattern, "$options": "i"}}
                ]
            }).limit(5))
            
            if triples:
                context += "\nKnowledge Graph Relationships:\n"
                for t in triples:
                    context += f"- {t.get('subject')} -> {t.get('predicate')} -> {t.get('object')}\n"
        except Exception as e:
            print(f"MongoDB KG retrieval error: {e}")
            
    if decisions is not None and words:
        try:
            regex_pattern = "|".join(words)
            decs = list(decisions.find({"decision": {"$regex": regex_pattern, "$options": "i"}}).limit(3))
            if decs:
                context += "\nPast Decisions & Preferences:\n"
                for d in decs:
                    context += f"- {d.get('decision')}\n"
        except Exception as e:
            print(f"MongoDB Decisions retrieval error: {e}")
            
    return context.strip()
