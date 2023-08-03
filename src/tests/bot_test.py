import telegram
from telegram import Update
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    Updater
    # ContextTypes,
    # Application
)

import whisper
from pydub import AudioSegment
import random
import os

MODEL = whisper.load_model("base")

def comando_audio(update: Update, context):
    """Transcribe an audio"""
    reply_to_message = update.message.reply_to_message
    if reply_to_message is not None and reply_to_message.voice is not None:
        print("Audio detectado")
        new_file = context.bot.get_file(reply_to_message.voice.file_id)
        file_path = f"voice_{random.randint(0, 1000)}.ogg"
        new_file.download(file_path)
        output = f"audio_{random.randint(0, 1000)}.ogg"
        sound = AudioSegment.from_file(file_path)
        sound.export(f"{output}.wav", format="wav")
        print("Audio convertido")
        try:
            data = MODEL.transcribe(f"{output}.wav")
            print(data["text"])
            reply_to_message.reply_text(data["text"])
            os.remove(file_path)
            os.remove(f"{output}.wav")
        except:
            reply_to_message.reply_text(error_message)
            os.remove(file_path)
            os.remove(f"{output}.wav")
    else:
        response = "T K IAS"
        update.message.reply_text(response)


def main():
    ''' MAIN '''
    print("Starting...")
    TOKEN = os.environ.get("TG_BOT_TEST")
    updater=Updater(TOKEN, use_context=True)
    dp=updater.dispatcher
    print('Dispatcher')
    # Eventos que activarán nuestro bot.
    dp.add_handler(CommandHandler("kdise", comando_audio))
    print("Start polling")
    # Comienza el bot
    updater.start_polling()
    print("Listening")
    # Lo deja a la escucha. Evita que se detenga.
    updater.idle()
    print("FInish")

if __name__ == '__main__':
    main()