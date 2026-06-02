from tavily import TavilyClient
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values


env_vars = dotenv_values('.env')

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
TavilyAPIKey = env_vars.get("TAVILY_API_KEY")

client = Groq(api_key=GroqAPIKey)
tavily_client = TavilyClient(api_key=TavilyAPIKey)
messages = []

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

try:
    with open(r"Data\\ChatLog.json",'r') as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\\ChatLog.json",'w') as f:
        dump([],f)

def GoogleSearch(Query):
    try:
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
        print(f"Tavily search failed: {e}. Falling back to googlesearch...")
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

    with open(r"Data\\ChatLog.json",'r') as f:
        messages = load(f)
        
    messages.append({"role":"user","content":f"{prompt}"})
    
    search_string, raw_results, images = GoogleSearch(prompt)
    SystemChatBot.append({"role":"system","content": f"{search_string}" })

    models = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
    ]

    Answer = ""
    for model in models:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=SystemChatBot + [{"role":"system","content":Information()}] + messages,
                max_tokens=2048,
                temperature=0.1,
                top_p=1,
                stream=True,
                stop=None
                )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    Answer += chunk.choices[0].delta.content
            
            break
        except Exception as e:
            print(f"Model {model} failed with error: {e}. Trying next model...")
            Answer = ""
            continue
    
    if not Answer:
        return "All models failed to generate a response.", raw_results
        
    Answer = Answer.strip().replace("</s>","")

    messages.append({"role":"assistant","content":Answer})

    with open('Data\\ChatLog.json','w') as f:
        dump(messages, f, indent=4)
    SystemChatBot.pop()
    
    # Combine results and images for frontend convenience
    # Some results may not have images, we can attach images to results if available
    for i, res in enumerate(raw_results):
        if i < len(images):
            res['image_url'] = images[i]
            
    return AnswerModifier(Answer=Answer), raw_results