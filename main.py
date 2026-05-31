import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
from openai import OpenAI
from gtts import gTTS
import pygame
import os
import time

# --- Configuration ---
# Replace with your actual API keys
NEWS_API_KEY = "db39658b0c324781853e4c5ad3de29b7"  # Your News API key
OPENAI_API_KEY = "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" # Your OpenAI API key

# --- Music Library (Example) ---
# You can expand this dictionary with more songs and their URLs
musicLibrary = {
    "goat": "https://youtu.be/M8vDwlHigJA?si=juvnlYPxjqoH2UUW",
    "khatole2": "https://youtu.be/obgMGM6I2rE?si=6QOuJgwINLjZ4-J5"  ,   
}

# --- Initialize Components ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()
pygame.mixer.init()

# --- Speaking Functions ---
def speak_old(text):
    """
    Uses pyttsx3 for offline text-to-speech.
    This can be useful for local feedback or when an internet connection isn't stable.
    """
    if not text.strip():
        print("Warning: Empty text passed to speak_old(). Skipping.")
        return
    engine.say(text)
    engine.runAndWait()

def speak(text):
    """
    Uses Google Text-to-Speech (gTTS) for more natural-sounding speech.
    Requires an internet connection.
    """
    if not text.strip():
        print("Warning: Empty text passed to speak(). Skipping.")
        return

    temp_audio_file = "temp_speech.mp3" 

    try:
        tts = gTTS(text=text, lang='en')
        tts.save(temp_audio_file)
        
        # Unload any currently playing music before loading new speech
        pygame.mixer.music.unload() 
        
        pygame.mixer.music.load(temp_audio_file)
        pygame.mixer.music.play()
        
        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10) # Control CPU usage
            
    except Exception as e:
        print(f"Error in speak(): {e}")
        # Fallback to offline speak if gTTS fails
        speak_old(f"I encountered an error trying to say that: {text}")
    finally:
        # Crucial: Stop and unload the music before attempting to remove the file
        if pygame.mixer.music.get_busy(): # Ensure music is actually playing before stopping
            pygame.mixer.music.stop()
        pygame.mixer.music.unload() # Unload the file from memory
        
        # Clean up the temporary audio file
        if os.path.exists(temp_audio_file):
            try:
                os.remove(temp_audio_file)
            except PermissionError as e:
                print(f"Permission error removing {temp_audio_file}: {e}")
                print("The file might still be in use. You may need to manually delete it or restart the program.")
            except Exception as e:
                print(f"Error removing {temp_audio_file}: {e}")


# --- AI Command Processing ---
def aiprocess(command):
    """
    Processes commands using OpenAI's GPT-3.5-turbo model.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Jarvis, a helpful assistant. Keep answers concise and to the point. Do not ask follow-up questions."}, # Added system message for better control
                {"role": "user", "content": command}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error communicating with OpenAI API: {e}")
        return "I'm sorry, I'm having trouble connecting to my AI brain right now."

# --- Command Handling ---
def processcommand(c): 
    """
    Processes recognized voice commands.
    """
    c = c.lower() # Convert command to lowercase for consistent matching

    if "open google" in c:
        speak("Opening Google.")
        webbrowser.open("https://google.com")
    elif "open facebook" in c:
        speak("Opening Facebook.")
        webbrowser.open("https://facebook.com")
    elif "open youtube" in c:
        speak("Opening YouTube.")
        webbrowser.open("https://www.youtube.com") 
    elif "open linkedin" in c:
        speak("Opening LinkedIn.")
        webbrowser.open("https://linkedin.com")
    elif "open instagram" in c:
        speak("Opening Instagram.")
        webbrowser.open("https://instagram.com")
    elif "open spotify" in c:
        speak("Opening Spotify.")
        webbrowser.open("https://open.spotify.com/")
    elif c.startswith("play "):
        song = c.replace("play ", "").strip() # Extract song name correctly
        if song in musicLibrary:
            speak(f"Playing {song}.")
            webbrowser.open(musicLibrary[song])
        else:
            speak(f"Sorry, I couldn't find the song {song} in my library.")
    elif "news" in c:
        speak("Fetching the latest news headlines.")
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}")
            r.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            articles = r.json().get("articles", [])
            if articles:
                speak("Here are the top 5 headlines:")
                for i, article in enumerate(articles[:5]):
                    speak(f"Headline {i+1}: {article.get('title', 'No title available')}")
                    time.sleep(0.5) # Small pause between headlines
            else:
                speak("Sorry, I couldn't find any news articles at the moment.")
        except requests.exceptions.RequestException as e:
            speak(f"Sorry, I couldn't fetch the news due to a network error: {e}")
        except Exception as e:
            speak(f"An unexpected error occurred while fetching news: {e}")
    elif "what time is it" in c:
        current_time = time.strftime("%I:%M %p")
        speak(f"The current time is {current_time}.")
    elif "thank you" in c or "thanks" in c:
        speak("You're welcome!")
    elif "stop" in c or "exit" in c or "quit" in c:
        speak("Goodbye!")
        return "exit" # Signal to the main loop to exit
    else:
        # If no specific command is matched, use AI to process the request
        speak("Let me think about that.")
        response = aiprocess(c)
        speak(response)

# --- Main Loop ---
if __name__ == "__main__":
    speak("Initializing Jarvis. Please wait a moment.") # Initial greeting
    
    # Check if API keys are set (basic check)
    if not NEWS_API_KEY or not OPENAI_API_KEY:
        speak_old("Warning: API keys for News or OpenAI are missing. Some features may not work.") # Use speak_old here as speak might fail if this is the first error
        print("Please ensure NEWS_API_KEY and OPENAI_API_KEY are set.")

    while True:
        try:
            print("\nListening for wake word 'Jarvis'...")
            with sr.Microphone() as source:
                # Adjust for ambient noise for better recognition
                recognizer.adjust_for_ambient_noise(source, duration=1) 
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5) 
                
            word = recognizer.recognize_google(audio)
            print(f"Heard: {word}")

            if "jarvis" in word.lower(): 
                speak("Yes?")
                print("Listening for command...")
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = recognizer.listen(source, timeout=7, phrase_time_limit=10)
                    
                command = recognizer.recognize_google(audio)
                print(f"Command: {command}")
                
                action = processcommand(command)
                if action == "exit":
                    break 

        except sr.UnknownValueError:
            pass 
        except sr.RequestError as e:
            print(f"Speech recognition service error; {e}")
            speak_old("I'm having trouble connecting to the speech recognition service.")
            time.sleep(2) 
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            speak_old("An unexpected error occurred. Please try again.")
            time.sleep(2) 

    pygame.mixer.quit() 
    print("Jarvis has shut down.")