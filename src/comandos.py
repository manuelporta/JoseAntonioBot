from telegram import Update
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
)

import padel_req
import audio_transcribe

def error(update: Update, context):
    print(f"Update {update} caused error {context.error}")


def comando_pistas(update: Update, context):
    args = context.args
    if not args:
        msg = padel_req.get_pistas_full()
    elif len(args) == 1:
        arg = args[0]
        if arg in ("hoxe", "hoy"):
            msg = padel_req.get_pistas_today()
        elif arg in ("finde", ):
            msg = padel_req.get_pistas_fide()
        elif arg in ("semana", ):
            msg = padel_req.get_pistas_week()
        elif arg in ("mañana", "mañá", "maña"):
            msg = padel_req.get_pistas_mañana()
    elif len(args) == 2:
        if args[0] in ("dias", "días"):
            if args[1].isdigit():
                msg = padel_req.get_pistas_ndias(int(args[1]))
            else:
                msg = "Tú no eres más tonto porque no practicas!"
        else:
            msg = "Si quieres más funcionalidades porque no levantas el culo?"
    else:
        msg = "Bueno, tampoco te pases flipao"

    update.message.reply_text(msg)

        
def comando_audio(update: Update, context):
    """Transcribe an audio"""
    model = whisper.load_model("base")
    reply_to_message = update.message.reply_to_message
    if reply_to_message is not None and reply_to_message.voice is not None:
        new_file = context.bot.get_file(reply_to_message.voice.file_id)
        msg = audio_transcribe.transcribe(new_file)
        update.message.reply_text(response)


def comando_hola(update: Update, context):
    update.message.reply_text(
        "Bueno, ¿cómo están los máquinas, lo primero de todo?"
    )

def comando_mimimi(update: Update, context):
    """Mimimizes a sentence"""
    reply_to_message = update.message.reply_to_message
    if reply_to_message is not None and reply_to_message.text is not None:
        response = reply_to_message.text
        for x in response.lower():
            if x in VOCALES:
                response = response.replace(x, "i")
        reply_to_message.reply_text(response)
    else:
        response = "Te falta calle, bro."
        update.message.reply_text(response)

def respuesta_rima(update: Update, context):
    text = str(update.message.text).lower()

    response = None
    if text.endswith("inco"):
        response = "Por el culo te la hinco."
    elif text.endswith("ece"):
        response = "Agárramela que me crece."
    elif text.endswith("ano"):
        response = "Me la agarras con la mano."
    elif text.endswith("uno"):
        response = "Te la mete Unamuno."
    elif text.endswith("ato"):
        response = "Pa tu culo mi aparato."
    elif text.endswith("erto"):
        response = "Te dejo el culo abierto."
    elif text.endswith("fiesta?"):
        response = "La que te va a dar esta."

    if response is not None:
        update.message.reply_text(response)

