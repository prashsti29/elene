import whisper
import os

model = whisper.load_model("base")

def transcribe_audio(audio_path: str) -> str:
    """
    Takes path to an audio file, returns transcribed text.
    Whisper runs completely locally — no API calls, no cost.
    """
    if not os.path.exists(audio_path):
        return ""
    
    result = model.transcribe(audio_path)
    return result["text"].strip()