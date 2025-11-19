import pyttsx3

def speak(text):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")

        # Try to select a clear, understandable voice
        # Prefer English voices that are clearer
        selected_voice = None
        for voice in voices:
            voice_name_lower = voice.name.lower()
            # Prefer Zira (clear female voice) or David (clear male voice)
            if "zira" in voice_name_lower:
                selected_voice = voice.id
                break
            elif "david" in voice_name_lower and selected_voice is None:
                selected_voice = voice.id
            elif "english" in voice_name_lower and selected_voice is None:
                selected_voice = voice.id
        
        if selected_voice:
            engine.setProperty("voice", selected_voice)

        # Slower rate for better understanding (130-150 is optimal)
        engine.setProperty("rate", 140)  # Reduced from 175 for clarity
        engine.setProperty("volume", 1.0)  # Max volume
        
        # Clear any previous speech
        engine.stop()
        
        # Speak the text
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        # Fallback: just print the text
        print(f"Speech: {text}")

