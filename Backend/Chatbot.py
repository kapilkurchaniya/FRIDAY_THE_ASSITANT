from groq import Groq
import cohere
from json import load, dump
import datetime
from Backend.env import chat_log_path, load_env

env_vars = load_env()

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
CohereAPIKey = env_vars.get("CohereAPIKey")

client = Groq(api_key=GroqAPIKey or "missing")

messages = []

def truncate_messages(messages, max_chars=9000):
    trimmed = messages.copy()
    total_chars = sum(len(str(msg.get("content", ""))) for msg in trimmed)
    while total_chars > max_chars and len(trimmed) > 1:
        for idx, msg in enumerate(trimmed):
            if msg.get("role") != "system":
                total_chars -= len(str(msg.get("content", "")))
                del trimmed[idx]
                break
        else:
            break
    return trimmed

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatbot = [
    {"role":"system","content":System}
]

try:
    with open(chat_log_path(),'r') as f:
        messages = load(f)
except FileNotFoundError:
    with open(chat_log_path(),'w') as f:
        dump([],f)

def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use the realtime data if needed,\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Hour: {hour}\nMinute: {minute}\nSecond: {second}\n"
    return data

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def ChatBot(Query):

    try:
        with open(chat_log_path(),'r') as f:
            messages = load(f)
        
        messages.append({"role":"user","content":f"{Query}"})

        # Retrieve context from Memory
        memory_context = None
        try:
            from Backend.Memory.Retriever import retrieve_context
            memory_context = retrieve_context(Query)
            if memory_context:
                print(f"[INFO] ChatBot: Retrieved memory context.")
        except Exception as e:
            print(f"[WARNING] ChatBot Memory retrieval skipped: {e}")
        
        system_messages = SystemChatbot + [{"role":"system","content":RealtimeInformation()}]
        if memory_context:
            system_messages.append({"role":"system","content": f"Use the following memories about the user to personalize your response:\n{memory_context}"})

        models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]

        Answer = ""
        for model in models:
            valid_messages = [msg for msg in messages if msg.get("content") and str(msg.get("content")).strip()]
            request_messages = truncate_messages(system_messages + valid_messages)
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=request_messages,
                    max_tokens=1024,
                    temperature=0.1,
                    top_p=1,
                    stream=True,
                    stop=None
                )

                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        Answer += chunk.choices[0].delta.content

                break
            except Exception as e:
                print(f"[WARNING] ChatBot Model {model} failed with error: {e}. Trying next model...")
                Answer = ""
                continue

        if not Answer:
            print("[WARNING] All Groq models failed. Attempting Cohere fallback...")
            try:
                if CohereAPIKey and CohereAPIKey.strip():
                    co_client = cohere.Client(api_key=CohereAPIKey)
                    chat_history = []
                    for m in system_messages:
                        chat_history.append({
                            "role": m.get("role", "system"),
                            "message": m.get("content", "")
                        })
                    for m in valid_messages:
                        chat_history.append({
                            "role": m.get("role", "user"),
                            "message": m.get("content", "")
                        })

                    stream = co_client.chat_stream(
                        model='command-a-03-2025',
                        message=Query,
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

        if not Answer:
            print("[WARNING] All Groq/Cohere models failed. Attempting HuggingFace fallback...")
            try:
                import requests
                hf_api_key = env_vars.get("HuggingFaceAPIKey", "").strip()
                if hf_api_key:
                    hf_url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
                    headers = {"Authorization": f"Bearer {hf_api_key}"}
                    hf_payload = {"inputs": f"User: {Query}\nAssistant:", "parameters": {"max_new_tokens": 512, "temperature": 0.5}}
                    res = requests.post(hf_url, headers=headers, json=hf_payload, timeout=15)
                    if res.status_code == 200:
                        out = res.json()
                        if isinstance(out, list) and len(out) > 0 and 'generated_text' in out[0]:
                            Answer = out[0]['generated_text'].split("Assistant:")[-1].strip()
                            print("[INFO] HuggingFace fallback succeeded.")
                    else:
                        print(f"[ERROR] HuggingFace API returned {res.status_code}: {res.text}")
                else:
                    print("[WARNING] No HuggingFace API key configured; skipping HuggingFace fallback.")
            except Exception as hf_err:
                print(f"[ERROR] HuggingFace fallback failed: {hf_err}")

        if not Answer:
            return "I'm having trouble connecting to my AI models right now. Please check the internet connection."
        
        Answer = Answer.replace("</s>","")

        messages.append({"role":"assistant","content":Answer})

        with open(chat_log_path(),'w') as f:
            dump(messages, f, indent=4)
            
        # Spawn background thread to extract new memories
        import threading
        from Backend.Memory.Extractor import extract_memory
        threading.Thread(target=extract_memory, args=(Query, Answer), daemon=True).start()

        return AnswerModifier(Answer=Answer)

    except Exception as e:
        print(f"Error: {e}")

        with open(chat_log_path(),'w') as f:
            dump([], f, indent=4)
        return "I'm having trouble connecting to my AI models right now. Please check the internet connection."


# if __name__ == '__main__':
#     while True:
#         user_input = input(">>>")
#         print(ChatBot(user_input))
