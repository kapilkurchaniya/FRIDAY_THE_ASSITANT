from tavily import TavilyClient
from groq import Groq
import cohere
from json import load, dump
import datetime
from Backend.env import chat_log_path, load_env


env_vars = load_env()

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
TavilyAPIKey = env_vars.get("TAVILY_API_KEY")
CohereAPIKey = env_vars.get("CohereAPIKey")
GoogleAPIKey = env_vars.get("GOOGLE_API_KEY")
MistralAPIKey = env_vars.get("MISTRAL_API_KEY")

client = Groq(api_key=GroqAPIKey or "missing")
tavily_client = TavilyClient(api_key=TavilyAPIKey or "missing")
messages = []

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

try:
    with open(chat_log_path(),'r') as f:
        messages = load(f)
except FileNotFoundError:
    with open(chat_log_path(),'w') as f:
        dump([],f)

def GoogleSearch(Query):
    if len(Query) < 2:
        return f"The search results for {Query} are\n [start] \nQuery too short for search.\n[end]", [], []
    try:
        print(f"[INFO] GoogleSearch: Querying Tavily for '{Query}'...")
        response = tavily_client.search(query=Query, max_results=3, include_images=True)
        results = response.get("results", [])
        images = response.get("images", [])
        Answer = f"The search results for {Query} are\n [start] \n"

        for i in results:
            title = i.get('title', 'No Title')
            content = i.get('content', 'No Description')
            Answer += f"Title: {title}\nDescription: {content}\n\n"
        
        Answer += "[end]"
        return Answer, results, images
    except Exception as e:
        print(f"[WARNING] Tavily search failed: {e}. Falling back to googlesearch-python...")
        try:
            from googlesearch import search
            results = []
            # advanced=True returns SearchResult objects with title, description, url
            for j in search(Query, num_results=3, advanced=True):
                results.append({
                    'title': j.title,
                    'content': j.description,
                    'url': j.url
                })
            
            Answer = f"The search results for {Query} are\n [start] \n"
            for i in results:
                title = i.get('title', 'No Title')
                content = i.get('content', 'No Description')
                Answer += f"Title: {title}\nDescription: {content}\n\n"
            Answer += "[end]"
            return Answer, results, []
        except Exception as fallback_e:
            return f"The search results for {Query} are\n [start] \nError during search: {e}\nFallback error: {fallback_e}\n[end]", [], []

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modifiedAnswer = '\n'.join(non_empty_lines)
    return modifiedAnswer

SystemChatBot = [
    {"role":"system","content":System},
    {"role":"user","content":"Hi"},
    {"role":"assistant","content":"Hello, how can I help you?"},
]

def Information():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Use the realtime data if needed,\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Hour: {hour}\nMinute: {minute}\nSecond: {second}\n"
    return data

def RealtimeSearchEngine(prompt):
    global SystemChatBot,messages

    with open(chat_log_path(),'r') as f:
        messages = load(f)
        
    messages.append({"role":"user","content":f"{prompt}"})
    
    search_string, raw_results, images = GoogleSearch(prompt)
    SystemChatBot.append({"role":"system","content": f"{search_string}" })

    # Retrieve context from Memory    
    try:
        from Backend.Memory.Retriever import retrieve_context
        memory_context = retrieve_context(prompt)
        if memory_context:
            print(f"[INFO] RealtimeSearchEngine: Retrieved memory context.")
    except Exception as e:
        print(f"[WARNING] RealtimeSearchEngine Memory retrieval skipped: {e}")
        memory_context = None

    system_messages = SystemChatBot
    if memory_context:
        system_messages = SystemChatBot + [{"role":"system","content": f"Use the following memories about the user to personalize your response:\n{memory_context}"}]

    models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
    ]

    Answer = ""
    for model in models:
        try:
            valid_messages = [msg for msg in messages if msg.get("content") and str(msg.get("content")).strip()]
            completion = client.chat.completions.create(
                model=model,
                messages=system_messages + [{"role":"system","content":Information()}] + valid_messages,
                temperature=0.7,
                max_tokens=2048,
                top_p=1,
                stream=True,
                stop=None
            )
            
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    Answer += chunk.choices[0].delta.content
            
            break
        except Exception as e:
            print(f"[WARNING] RealtimeSearchEngine Model {model} failed with error: {e}. Trying next model...")
            Answer = ""
            continue
    
    if not Answer:
        print("[WARNING] All Groq models failed. Attempting Cohere fallback...")
        try:
            if CohereAPIKey and CohereAPIKey.strip():
                co_client = cohere.Client(api_key=CohereAPIKey)
                # Build chat history compatible with Cohere's chat API
                chat_history = []
                for m in system_messages:
                    chat_history.append({
                        "role": m.get("role", "system"),
                        "message": m.get("content", "")
                    })
                valid_messages = [msg for msg in messages if msg.get("content") and str(msg.get("content")).strip()]
                for m in valid_messages:
                    chat_history.append({
                        "role": m.get("role", "user"),
                        "message": m.get("content", "")
                    })

                stream = co_client.chat_stream(
                    model='command-a-03-2025',
                    message=prompt,
                    temperature=0.7,
                    chat_history=chat_history,
                    preamble=System,
                )

                for event in stream:
                    if getattr(event, 'event_type', None) == 'text-generation':
                        Answer += event.text

                if Answer:
                    print("[INFO] Cohere fallback succeeded.")
                else:
                    print("[WARNING] Cohere returned no answer.")
            else:
                print("[WARNING] No Cohere API key configured; skipping Cohere fallback.")
        except Exception as coh_err:
            print(f"[ERROR] Cohere fallback failed: {coh_err}")

        # If still no answer, attempt Mistral HTTP fallback
        if not Answer:
            print("[INFO] Attempting Mistral fallback...")
            try:
                if MistralAPIKey and MistralAPIKey.strip():
                    import requests
                    mistral_url = "https://api.mistral.ai/v1/models/mistral-large/outputs"
                    headers = {"Authorization": f"Bearer {MistralAPIKey}", "Content-Type": "application/json"}
                    payload = {"input": prompt, "parameters": {"max_new_tokens": 512, "temperature": 0.7}}
                    res = requests.post(mistral_url, headers=headers, json=payload, timeout=15)
                    if res.status_code == 200:
                        data = res.json()
                        # Try several common response shapes
                        text = ""
                        if isinstance(data, dict):
                            if 'outputs' in data:
                                for o in data.get('outputs', []):
                                    text_piece = o.get('content') or o.get('text') or ''
                                    text += text_piece
                            if not text and 'result' in data:
                                text = data.get('result', '')
                            if not text and 'generated_text' in data:
                                text = data.get('generated_text', '')
                        if text:
                            Answer = text
                            print("[INFO] Mistral fallback succeeded.")
                        else:
                            print(f"[WARNING] Mistral returned no usable text. Response keys: {list(data.keys()) if isinstance(data, dict) else 'unknown'}")
                    else:
                        print(f"[ERROR] Mistral API returned {res.status_code}: {res.text}")
                else:
                    print("[WARNING] No MISTRAL_API_KEY configured; skipping Mistral fallback.")
            except Exception as mistral_err:
                print(f"[ERROR] Mistral fallback failed: {mistral_err}")

        # Final fallback: HuggingFace (if configured)
        if not Answer:
            print("[INFO] Attempting HuggingFace fallback...")
            try:
                import requests
                hf_api_key = env_vars.get("HuggingFaceAPIKey", "").strip()
                if hf_api_key:
                    hf_url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
                    headers = {"Authorization": f"Bearer {hf_api_key}"}
                    prompt_text = "System: " + "\n".join([m['content'] for m in system_messages]) + f"\nUser: {prompt}\nAssistant:"
                    hf_payload = {"inputs": prompt_text, "parameters": {"max_new_tokens": 512, "temperature": 0.5}}
                    res = requests.post(hf_url, headers=headers, json=hf_payload, timeout=15)
                    if res.status_code == 200:
                        out = res.json()
                        if isinstance(out, list) and len(out) > 0 and 'generated_text' in out[0]:
                            Answer = out[0]['generated_text'].split("Assistant:")[-1].strip()
                            print("[INFO] HuggingFace fallback succeeded.")
                    else:
                        print(f"[ERROR] HuggingFace API returned {res.status_code}: {res.text}")
            except Exception as hf_err:
                print(f"[ERROR] HuggingFace fallback failed: {hf_err}")

    if not Answer:
        return "I'm having trouble connecting to my AI models right now.", raw_results
        
    Answer = Answer.strip().replace("</s>","")
    messages.append({"role":"assistant","content":Answer})
    
    with open(chat_log_path(),'w') as f:
        dump(messages, f, indent=4)
        
    # Spawn background thread to extract new memories
    import threading
    from Backend.Memory.Extractor import extract_memory
    threading.Thread(target=extract_memory, args=(prompt, Answer), daemon=True).start()

    # Combine results and images for frontend convenience
    # Some results may not have images, we can attach images to results if available
    for i, res in enumerate(raw_results):
        if i < len(images):
            res['image_url'] = images[i]
            
    return AnswerModifier(Answer=Answer), raw_results
