import whisper
from pydub import AudioSegment
import random

MODEL = whisper.load_model("base")

def transcribe(file):
    temp_file_path = f"/tmp/voice_{random.randint(0, 1000)}.ogg"
    file.download(temp_file_path)
    sound = AudioSegment.from_file(file_path)
    temp_output = f"/tmp/audio_{random.randint(0, 1000)}.wav"
    sound.export(temp_output, format="wav")
    os.remove(file_path)
    os.remove(output)
    try:
        data = MODEL.transcribe(output)
        msg = data["text"]
    except:
        msg = "HAPRENDE A ABLAR OMVBRE!!"
    
    return msg