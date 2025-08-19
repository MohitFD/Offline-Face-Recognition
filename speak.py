import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")

    # Select female voice if available
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break

    engine.setProperty("rate", 175)  # Speed
    engine.setProperty("volume", 1)  # Max volume

    engine.say(text)
    engine.runAndWait()