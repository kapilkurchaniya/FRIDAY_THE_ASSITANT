import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Backend.Memory.Extractor import extract_memory
from Backend.Memory.Retriever import retrieve_context

print("Testing Extractor...")
user_msg = "I'm starting a new project called Jarvis. It's a personal AI companion. My favorite color is neon blue."
ai_reply = "That's a fantastic project! I'll help you build Jarvis. And I've noted that your favorite color is neon blue."

extract_memory(user_msg, ai_reply)

time.sleep(2)

print("\nTesting Retriever...")
context = retrieve_context("What color do I like and what project am I working on?")
print("--- Retrieved Context ---")
print(context)
print("-------------------------")
