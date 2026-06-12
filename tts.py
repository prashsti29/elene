from gtts import gTTS
import os


os.makedirs("audio", exist_ok=True)

def text_to_speech(text: str, call_sid: str) -> str:
    """
    Converts agent's text response to an MP3 file.
    Saves it as audio/{call_sid}_response.mp3
    Returns the file path.
    
    We use call_sid as filename so multiple simultaneous 
    calls don't overwrite each other's audio files.
    """
    
    output_path = f"audio/{call_sid}_response.mp3"
    
    tts = gTTS(
        text=text,
        lang="en",
        tld="co.in",
        slow=False
    )
    
    tts.save(output_path)
    return output_path


def cleanup_audio(call_sid: str):
    """
    Delete audio file after call ends — keeps disk clean.
    Call this when hangup is detected.
    """
    path = f"audio/{call_sid}_response.mp3"
    if os.path.exists(path):
        os.remove(path)