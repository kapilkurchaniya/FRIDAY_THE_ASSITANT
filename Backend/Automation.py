from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search,playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os

env_vars = dotenv_values('.env')
GroqAPIKey = env_vars.get("GroqAPIKey")
Username = env_vars.get("Username")

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'

classes = [
    'zCubwf','hgKElc','LTKOO sYric','Z0LcW','gsrt vk_bk FzvWSb YwPhnf','pclqee','tw-Data-text tw-data-small tw-ta',
    'IZ6rdc','O5uR6d LTKOO','vlzY6d','webanswers-webanswers_table__webanswers-table','dDoNo ikb4Bb gsrt','sXLaOe',
    'LWkfKe','VQF4g','qv3Wpe','kno-rdesc','SPZz6b'
]

client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need-don't hesitate to ask"
]

messages = []

SystemChatbot = [
    {"role":"system","content":f"Hello, I am {Username}, You are a content writer you have to write content like letters, codes, applications, essays, notes, songs, poems etc."}
]

def Googlesearch(Topic):
    search(Topic)
    return True

def Content(Topic):

    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor,File])
    
    def ContentWriterAI(Prompt):
        messages.append({"role":"user","content":f"{Prompt}"})

        completion = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=SystemChatbot + messages,
            max_tokens=2048,
            temperature=0.1,
            top_p=1,
            stream=True,
            stop=None
        )
        Answer = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
        
        Answer = Answer.strip().replace("</s>","")

        messages.append({"role":"assistant","content":Answer})
        return Answer
    
    Topic: str = Topic.replace("content ",'')
    ContentByAI = ContentWriterAI(Topic)

    with open(rf"Data\\{Topic.lower().replace(' ','')}.txt",'w', encoding='utf-8') as f:
        f.write(ContentByAI)
        f.close()
    
    OpenNotepad(rf"Data\\{Topic.lower().replace(' ','')}.txt")
    return True

# Content("Write a application for a 3 days sick leave from office as a managing director of the Bhavya limited company")

def YoutubeSearch(query):
    print("Running...")
    Url4Search = f"https://www.youtube.com/results?search_query={query}"
    webopen(Url4Search)
    return True

# YoutubeSearch("Desi gamers junction")

def PlayYoutube(Query):
    playonyt(Query)
    return True

def OpenApp(app, sess=requests.session()):
    try:
        appopen(app, match_closest=True,output=True,throw_error=True)
        return True
    except:
        try:
            def extract_Links(html):
                if html is None:
                    print('\n\n\nreturning.....\n\n\n')
                    print('html')
                    return []
                soup = BeautifulSoup(html,'html.parser')
                links = soup.find_all('a', {'jsname': 'UWckNb'})
                return [link.get('href') for link in links]
            
            def search_google(query):
                url = f"https://www.google.com/search?q={query}"
                headers = {'User-Agent':user_agent}
                response = requests.get(url,headers=headers)

                if response.status_code == 200:
                    return response.text
                else:
                    print("Failed to retrive search results.")
                return None
            
            html = search_google(app)

            if html:
                link = extract_Links(html)[0]
                print(link)
                print(link)
                webopen(link)
        except Exception as e:
            print("Not Done")
        
        return True

    
def closeApps(app):

    if "chrome" in app:
        pass
    else:
        try:
            close(app,match_closest=True,output=True,throw_error=True)
            return True
        except:
            return False

def System(command):

    def mute():
        keyboard.press_and_release('volume mute')
    
    def unmute():
        keyboard.press_and_release('volume mute')
    
    def VolumeUp():
        keyboard.press_and_release('volume up')
    
    def VolumeDown():
        keyboard.press_and_release('volume down')
    
    if command == 'mute':
        mute()
    elif command == 'unmute':
        unmute()
    elif command == 'volume up':
        VolumeUp()
    elif command == 'volume down':
        VolumeDown()


async def TranslateAndExecute(commands: list[str]):

    funcs = []


    for command in commands:
        if command.startswith('open '):
            if "open it" in command:
                pass
            if "open file" == command:
                pass
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix('open '))
                funcs.append(fun)
        elif command.startswith('general '):
            pass
        elif command.startswith('realtime '):
            pass
        elif command.startswith('close '):
            fun = asyncio.to_thread(closeApps, command.removeprefix('close '))
            funcs.append(fun)
        elif command.startswith('play '):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix('play '))
            funcs.append(fun)
        elif command.startswith('content '):
            fun = asyncio.to_thread(Content, command.removeprefix('content '))
            funcs.append(fun)
        elif command.startswith('google search '):
            fun = asyncio.to_thread(Googlesearch, command.removeprefix('google search '))
            funcs.append(fun)
        elif command.startswith('youtube search '):
            fun = asyncio.to_thread(YoutubeSearch, command.removeprefix('youtube search '))
            funcs.append(fun)
        elif command.startswith('system '):
            fun = asyncio.to_thread(System, command.removeprefix('system '))
            funcs.append(fun)
        else:
            print(f"No function found for command: {command}")
        
    results = await asyncio.gather(*funcs)

    for result in results:
        if isinstance(result,str):
            yield result
        else:
            yield result

async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands=commands):
        pass
    return True

# if __name__ == '__main__':
#     asyncio.run(Automation(['open instagram','close roblox','content write a beautiful poem in hindi on dance']))
