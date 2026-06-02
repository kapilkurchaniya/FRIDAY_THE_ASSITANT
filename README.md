# FRIDAY - Advanced AI Assistant

FRIDAY (or JARVIS) is an advanced, modular AI Assistant with a modern web interface and desktop GUI. It leverages cutting-edge LLMs and APIs to perform a wide variety of tasks, from real-time web searching to system automation, image generation, and natural conversations.

## Features

- **Decision Making Model (DMM)**: Intelligently categorizes user prompts into actionable intents (e.g., general chat, real-time search, system automation) using Cohere API with a Groq fallback.
- **Real-time Web Search**: Fetches live data from the internet to answer current queries using Tavily (with a fallback to organic Google Search scraping).
- **System Automation**: Opens/closes applications, plays YouTube videos, controls system volume, and generates detailed text content.
- **Image Generation**: Creates AI images directly from text prompts using Hugging Face (with a fallback to Pollinations.ai).
- **Voice Interactions (STT & TTS)**: Listens to your commands using an unlimited Chrome Webkit-based Speech-to-Text engine and speaks back using Microsoft Edge-TTS.
- **Dual Interface**:
  - **Modern Web UI**: A beautiful, highly-responsive web interface built with TailwindCSS, featuring micro-animations, glowing states, and a research hub.
  - **Desktop GUI**: A classic desktop interface built with PyQt5 for local interactions.

## Architecture

The project is highly modular. The `Backend/` directory houses the core intelligence modules:
- `Model.py` - Core Decision Making Model (Cohere & Groq).
- `Chatbot.py` - General purpose conversational AI (Groq).
- `RealtimeSearchEngine.py` - Internet-aware AI for live querying.
- `Automation.py` - Performs system actions, application launching, and content generation.
- `ImageGeneration.py` - Image generation routines.
- `SpeechToText.py` & `TextToSpeech.py` - Voice interaction pipelines.

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- Google Chrome browser (required for Speech-to-Text)
- API Keys for the respective AI services.

### 2. Installation
Clone the repository and install the dependencies using the provided `Requirements.txt`:
```bash
pip install -r Requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory (you can use `.env.example` as a template) and add your API keys:
```env
Username=YourName
Assistantname=FRIDAY
InputLanguage=en
AssistantVoice=en-CA-LiamNeural

# API Keys
CohereAPIKey=your_cohere_key_here
GroqAPIKey=your_groq_key_here
HuggingFaceAPIKey=your_huggingface_key_here
TAVILY_API_KEY=your_tavily_key_here
```
*(Note: Thanks to built-in fallbacks, the system can gracefully failover to free alternatives for several of these keys if rate-limited!)*

## Running the Assistant

You have two ways to interact with the assistant:

### Web Interface (Recommended)
The Web UI provides a rich chat canvas and research hub.
```bash
python Main.py
# Or run python app.py directly
```
Then navigate to `http://localhost:5000` in your web browser.

### Desktop GUI
The PyQt5 desktop interface provides a local, system-level window.
```bash
python Frontend/GUI.py
```
