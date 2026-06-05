import os
import sys
import json
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from dotenv import dotenv_values
from asyncio import run
import asyncio

# Import existing backend modules
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToAudioFile

app = Flask(__name__, template_folder='Frontend/templates', static_folder='Frontend')
CORS(app)

env_vars = dotenv_values('.env')
Username = env_vars.get('Username', 'User')
Assistantname = env_vars.get('Assistantname', 'Friday')

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ['how','what','who','where','when','why','which','whose','whom','can you',"what's","where's","how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.','?','!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in [".","!","?"]:
            new_query = new_query[:-1] + "." 
        else:
            new_query += "."
    
    return new_query.capitalize()

Functions = ['open', 'close', 'play', 'system', 'content','google search','youtube search']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_query():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    Query = data['query']
    Decision = FirstLayerDMM(Query)
    
    print(f"Decision: {Decision}")
    
    G = any([i for i in Decision if i.startswith('general')])
    R = any([i for i in Decision if i.startswith('realtime')])
    
    merged_query = "and".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )
    
    TaskExecution = False
    Answer = "I'm sorry, I couldn't process that."
    raw_results = []
    
    # Handle Automations
    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True
                Answer = "Task execution started."
    
    if G and R or R:
        Answer, raw_results = RealtimeSearchEngine(QueryModifier(merged_query))
    elif not TaskExecution:
        for Queries in Decision:
            if 'general' in Queries:
                QueryFinal = Queries.replace('general',"")
                Answer = ChatBot(QueryModifier(QueryFinal))
                break
            elif 'realtime' in Queries:
                QueryFinal = Queries.replace('realtime',"")
                Answer, raw_results = RealtimeSearchEngine(QueryModifier(QueryFinal))
                break
            elif 'exit' in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                break

    # Generate Audio for the answer
    try:
        asyncio.run(TextToAudioFile(Answer))
    except Exception as e:
        print(f"TTS Error: {e}")
        
    return jsonify({
        "status": "success",
        "answer": Answer,
        "search_data": raw_results,
        "decision": Decision
    })

@app.route('/api/audio')
def get_audio():
    audio_path = os.path.join(os.getcwd(), 'Data', 'speech.mp3')
    if os.path.exists(audio_path):
        # send_file requires cache invalidation if it changes, we add anti-cache headers in response
        response = send_file(audio_path, mimetype="audio/mpeg")
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    else:
        return jsonify({"error": "Audio file not found"}), 404

if __name__ == '__main__':
    try:
        from Backend.Memory.Reflection import start_reflection_job
        start_reflection_job()
    except Exception as e:
        print(f"Could not start reflection job: {e}")
        
    app.run(host='0.0.0.0', port=5000, debug=True)
