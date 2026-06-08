try:
    import pygame
except ImportError:
    pygame = None

import random
import asyncio
import edge_tts
import os
from Backend.env import load_env, speech_path

env_vars = load_env()

AssistantVoice = env_vars.get('AssistantVoice')

async def TextToAudioFile(text) -> None:
    file_path = speech_path()

    if os.path.exists(file_path):
        os.remove(file_path)

    try:
        print("[INFO] TextToSpeech: Attempting edge-tts...")
        communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
        await communicate.save(file_path)
        print("[INFO] TextToSpeech: edge-tts succeeded.")
    except Exception as e:
        print(f"[WARNING] edge-tts failed: {e}. Falling back to gTTS...")
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en')
            tts.save(file_path)
            print("[INFO] TextToSpeech: gTTS fallback succeeded.")
        except Exception as gtts_err:
            print(f"[ERROR] gTTS fallback also failed: {gtts_err}")

def TTS(Text, func=lambda r=None: True):
    retries = 0
    while retries < 3:
        try:
            asyncio.run(TextToAudioFile(Text))

            if pygame is None:
                return True

            pygame.mixer.init()

            pygame.mixer.music.load(speech_path())
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if func() == False:
                    break
                pygame.time.Clock().tick(10)
            
            return True
        
        except Exception as e:
            print(f'Errors in TTS: {e}')
            retries += 1
        
        finally:
            try:
                func(False)
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except Exception as e:
                pass
                
    return False

def TextToSpeech(Text, func=lambda r=None :True):
    Data = str(Text).split(".")

    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]

    if len(Data)>4 and len(Text)>= 250:
        TTS(" ".join(Text.split(".")[0:2]) + ". " + random.choice(responses), func)
    else:
        TTS(Text,func)


# if __name__ == "__main__":
#     while True:
#         TextToSpeech(input(">>> "))
