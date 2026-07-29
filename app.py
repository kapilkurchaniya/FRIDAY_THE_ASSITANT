import os
import sys
import json
import concurrent.futures
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from asyncio import run
import asyncio
from Backend.env import load_env, speech_path

app = Flask(__name__, template_folder='Frontend/templates', static_folder='Frontend')
CORS(app)

env_vars = load_env()
Username = env_vars.get('Username', 'User')
Assistantname = env_vars.get('Assistantname', 'Friday')

REQUEST_TIMEOUT_SECONDS = 45
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def run_with_timeout(func, *args, timeout=REQUEST_TIMEOUT_SECONDS):
    future = executor.submit(func, *args)
    return future.result(timeout=timeout)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    if not query_words:
        return "."
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

import time

last_query_text = ""
last_query_time = 0.0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_query():
    global last_query_text, last_query_time
    try:
        data = request.get_json(silent=True)
        if not data or 'query' not in data:
            return jsonify({"status": "error", "error": "No query provided"}), 400
        
        Query = str(data['query']).strip()
        now = time.time()
        if Query.lower() == last_query_text.lower() and (now - last_query_time) < 4.0:
            print(f"[WARNING] Duplicate query received within 4s ('{Query}'). Short-circuiting duplicate request.")
            return jsonify({
                "status": "success",
                "answer": "",
                "search_data": [],
                "decision": ["general"],
                "audio_available": False,
                "duplicate_ignored": True
            }), 200

        last_query_text = Query
        last_query_time = now

        # Check for Shutdown command
        shutdown_triggers = ['shutdown', 'shut down', 'exit', 'quit', 'turn off', 'stop server', 'goodbye friday', 'bye friday', 'system shutdown']
        clean_q = Query.lower().strip().replace(".", "").replace("!", "").replace("?", "")
        if any(trigger in clean_q for trigger in shutdown_triggers) or clean_q in ['shutdown', 'exit', 'quit']:
            print("[INFO] Shutdown command received. Terminating Flask server and terminal process in 2.5s...")
            
            def delayed_shutdown():
                time.sleep(2.5)
                print("[INFO] Server and terminal shutdown complete.")
                os._exit(0)

            executor.submit(delayed_shutdown)

            return jsonify({
                "status": "success",
                "answer": "Shutting down all neural networks and terminating server. Goodbye Kapil Boss!",
                "search_data": [],
                "decision": ["shutdown"],
                "audio_available": False,
                "shutdown": True
            }), 200

        if not Query or len(Query.replace(".", "").strip()) < 2:
            print(f"[INFO] Query too short ('{Query}'). Short-circuiting request.")
            return jsonify({
                "status": "success",
                "answer": "It seems like you didn't type enough information. Please ask a complete question!",
                "search_data": [],
                "decision": ["general"],
                "audio_available": False
            }), 200

        from Backend.Automation import Automation
        from Backend.Chatbot import ChatBot
        from Backend.Model import FirstLayerDMM
        from Backend.RealtimeSearchEngine import RealtimeSearchEngine
        from Backend.TextToSpeech import TextToAudioFile

        try:
            print(f"[INFO] Routing query to FirstLayerDMM: '{Query}'")
            Decision = run_with_timeout(FirstLayerDMM, Query, timeout=20)
        except concurrent.futures.TimeoutError:
            print("[WARNING] Decision model timed out. Falling back to general chat.")
            Decision = [f"general {Query}"]
        except Exception as e:
            print(f"[ERROR] Decision model failed: {e}. Falling back to general chat.")
            Decision = [f"general {Query}"]
        
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
                    run_with_timeout(lambda: run(Automation(list(Decision))), timeout=20)
                    TaskExecution = True
                    Answer = "Task execution started."
        
        if G and R or R:
            print(f"[INFO] Executing RealtimeSearchEngine...")
            try:
                Answer, raw_results = run_with_timeout(RealtimeSearchEngine, QueryModifier(merged_query), timeout=REQUEST_TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                print("[ERROR] RealtimeSearchEngine timed out!")
                raise
            except Exception as e:
                print(f"[ERROR] RealtimeSearchEngine failed: {e}")
                Answer = "I encountered an error while searching the web."
        elif not TaskExecution:
            for Queries in Decision:
                if 'general' in Queries:
                    QueryFinal = Queries.replace('general',"")
                    print(f"[INFO] Executing ChatBot...")
                    try:
                        Answer = run_with_timeout(ChatBot, QueryModifier(QueryFinal), timeout=REQUEST_TIMEOUT_SECONDS)
                    except concurrent.futures.TimeoutError:
                        print("[ERROR] ChatBot timed out!")
                        raise
                    except Exception as e:
                        print(f"[ERROR] ChatBot failed: {e}")
                        Answer = "I encountered an error while generating a response."
                    break
                elif 'realtime' in Queries:
                    QueryFinal = Queries.replace('realtime',"")
                    print(f"[INFO] Executing RealtimeSearchEngine...")
                    try:
                        Answer, raw_results = run_with_timeout(RealtimeSearchEngine, QueryModifier(QueryFinal), timeout=REQUEST_TIMEOUT_SECONDS)
                    except concurrent.futures.TimeoutError:
                        print("[ERROR] RealtimeSearchEngine timed out!")
                        raise
                    except Exception as e:
                        print(f"[ERROR] RealtimeSearchEngine failed: {e}")
                        Answer = "I encountered an error while searching the web."
                    break
                elif 'exit' in Queries:
                    QueryFinal = "Okay, Bye!"
                    Answer = run_with_timeout(ChatBot, QueryModifier(QueryFinal), timeout=REQUEST_TIMEOUT_SECONDS)
                    break

        # Generate Audio for the answer
        audio_path = speech_path()
        try:
            run_with_timeout(lambda: asyncio.run(TextToAudioFile(Answer)), timeout=15)
        except Exception as e:
            print(f"TTS Error: {e}")
            
        return jsonify({
            "status": "success",
            "answer": Answer,
            "search_data": raw_results,
            "decision": Decision,
            "audio_available": os.path.exists(audio_path)
        })
    except concurrent.futures.TimeoutError:
        return jsonify({
            "status": "error",
            "error": "The assistant backend timed out while contacting an external service. Please try again."
        }), 504
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/audio')
def get_audio():
    audio_path = speech_path()
    if os.path.exists(audio_path):
        # send_file requires cache invalidation if it changes, we add anti-cache headers in response
        response = send_file(audio_path, mimetype="audio/mpeg")
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    else:
        return ('', 204)

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    try:
        from Backend.Memory.Reflection import start_reflection_job
        start_reflection_job()
    except Exception as e:
        print(f"Could not start reflection job: {e}")
        
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
