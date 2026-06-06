import json
from apscheduler.schedulers.background import BackgroundScheduler
from groq import Groq
from dotenv import dotenv_values
from Backend.Memory.Extractor import extract_memory

env_vars = dotenv_values('.env')
GroqAPIKey = (env_vars.get("GroqAPIKey") or "").strip()
client = Groq(api_key=GroqAPIKey, timeout=20, max_retries=0) if GroqAPIKey else None

def nightly_reflection():
    """
    Runs nightly to analyze the entire day's chat logs and extract any missed 
    long-term goals, project states, or overarching themes.
    """
    if not client: return
    print("[Memory] Running Nightly Reflection Job...")
    try:
        with open(r"Data\ChatLog.json", 'r') as f:
            messages = json.load(f)
            
        if len(messages) < 5:
            print("[Memory] Not enough messages for reflection.")
            return
            
        conversation = ""
        for m in messages:
            conversation += f"{m['role'].upper()}: {m.get('content', '')}\n"
            
        prompt = f"""
        You are reflecting on the day's conversation between a User and FRIDAY.
        What are the top 3 most important overarching goals, projects, or interests the user discussed today?
        Summarize them into clear facts.
        Format your response EXACTLY as a JSON object:
        - "facts": [List of summarized string facts]
        
        Conversation:
        {conversation[-5000:]}
        """
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(completion.choices[0].message.content)
        facts = result.get("facts", [])
        
        if facts:
            spoofed_user = "Daily reflection summary facts to remember."
            spoofed_ai = "\n".join(facts)
            extract_memory(spoofed_user, spoofed_ai)
            print(f"[Memory] Nightly reflection complete. Extracted {len(facts)} high-level facts.")
            
    except Exception as e:
        print(f"[Memory] Nightly reflection failed: {e}")

def start_reflection_job():
    scheduler = BackgroundScheduler()
    scheduler.add_job(nightly_reflection, 'cron', hour=2, minute=0)
    scheduler.start()
    print("[Memory] Scheduled nightly reflection job for 2:00 AM.")
