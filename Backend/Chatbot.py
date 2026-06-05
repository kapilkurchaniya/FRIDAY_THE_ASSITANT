from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values

env_vars = dotenv_values('.env')

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

messages = []

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatbot = [
    {"role":"system","content":System}
]

try:
    with open(r"Data\\ChatLog.json",'r') as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\\ChatLog.json",'w') as f:
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
        with open(r"Data\\ChatLog.json",'r') as f:
            messages = load(f)
        
        messages.append({"role":"user","content":f"{Query}"})

        # Retrieve context from Memory Pipeline
        from Backend.Memory.Retriever import retrieve_context
        memory_context = retrieve_context(Query)
        
        system_messages = SystemChatbot + [{"role":"system","content":RealtimeInformation()}]
        if memory_context:
            system_messages.append({"role":"system","content": f"Use the following memories about the user to personalize your response:\n{memory_context}"})

        models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
        ]

        Answer = ""
        for model in models:
            valid_messages = [msg for msg in messages if msg.get("content") and str(msg.get("content")).strip()]
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=system_messages + valid_messages,
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
                print(f"Model {model} failed with error: {e}. Trying next model...")
                Answer = ""
                continue
        
        if not Answer:
            return "All models failed to generate a response."
        
        Answer = Answer.replace("</s>","")

        messages.append({"role":"assistant","content":Answer})

        with open('Data\\ChatLog.json','w') as f:
            dump(messages, f, indent=4)
            
        # Spawn background thread to extract new memories
        import threading
        from Backend.Memory.Extractor import extract_memory
        threading.Thread(target=extract_memory, args=(Query, Answer), daemon=True).start()

        return AnswerModifier(Answer=Answer)

    except Exception as e:
        print(f"Error: {e}")

        with open('Data\\ChatLog.json','w') as f:
            dump([], f, indent=4)
        return ChatBot(Query=Query)


# if __name__ == '__main__':
#     while True:
#         user_input = input(">>>")
#         print(ChatBot(user_input))