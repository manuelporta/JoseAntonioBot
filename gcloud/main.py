import datetime
import json
import requests
import threading
import asyncio
import os

from bs4 import BeautifulSoup
import telegram
from telegram import Update
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    # ContextTypes,
    # Application
)

import whisper
from pydub import AudioSegment
import random

TOKEN = os.environ.get("TG_BOT")

VOCALES = ("a", "e", "o", "u")

URL = "https://maisqueauga.deporsite.net/ajax/TInnova_v2/ReservaRecursos_Selector_v2_2/llamadaAjax/solicitaDisponibilidad"

FORM_DATA = {
    "fechaInicio": "06/03/2023",
    "fechaFin": "06/03/2023",
    "IdCentro": 2,
    "IdDeporte": 19,
    "IdTipoRecurso": 0,
    "IdModalidad": 0,
    "RecursoHumano": 0,
    "IdPersona": 0,
    "UtilizarIdUsuarioParaObtenerDisponibilidad": 0,
}

HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8,fr;q=0.7,gl;q=0.6,pt;q=0.5",
    "Connection": "keep-alive",
    "Content-Length": "177",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Host": "maisqueauga.deporsite.net",
    "Origin": "https://maisqueauga.deporsite.net",
    "Referer": "https://maisqueauga.deporsite.net/reserva-recursos-navia?IdCentro=2&IdDeporte=19",
    "sec-ch-ua": r'" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36",
    "X-CSRF-TOKEN": "2wrM61soCNR1mSCL6MbKGx7bVGPnCG5VaSdyHp8q",
    "X-Requested-With": "XMLHttpRequest",
}

MIN_WEEK = datetime.datetime.strptime("18:00:00", "%H:%M:%S")
MAX_WEEK = datetime.datetime.strptime("20:30:00", "%H:%M:%S")

CENTROS = {"Navia": 2, "Barreiro": 3}
IDS = {"Navia": 19, "Barreiro": 18}


DIAS_SEMANA = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

def get_pistas_day(day, pistas):
    form = FORM_DATA.copy()
    form["fechaInicio"] = day.strftime("%d/%m/%Y")
    form["fechaFin"] = form["fechaInicio"]
    pistas_dia = {}
    for centro in CENTROS.keys():
        form["IdCentro"] = CENTROS[centro]
        form["IdDeporte"] = IDS[centro]
        get_pistas_centro(CENTROS[centro], day, pistas_dia, form)
    if pistas_dia:
        pistas[day] = pistas_dia



def get_pistas_centro(centro, date, pistas_dia, form):
    with requests.Session() as session:
        headers = get_token(session, centro)
        get_pistas(session, date, pistas_dia, form, headers)


def get_token(session, centro):
    aux_url = f"https://maisqueauga.deporsite.net/reserva-recursos-mqa?IdCentro={centro}&IdDeporte=18"
    r = session.get(aux_url)
    if not r.ok:
        # TODO
        return
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.select_one('meta[name="csrf-token"]')["content"]
    headers = HEADERS.copy()
    headers["Cookie"] = "; ".join([x.name + "=" + x.value for x in r.cookies])
    headers["X-CSRF-TOKEN"] = token
    return headers


def filtrar_horas(horas):
    new_horas = []
    for hora in horas:
        if hora < MIN_WEEK or hora > MAX_WEEK:
            continue
        new_horas.append(hora)
    return new_horas


def get_hora(inicio, lapso, i):
    hora = inicio + datetime.timedelta(hours=i / 2 * lapso)
    return hora


def get_disponibilidad(pista):
    values = []
    disponibilidad = pista["disponibilidad"]
    for i in range(0, len(disponibilidad), pista["lapsosIntervalo"]):
        values.append(int(max(disponibilidad[i : i + pista["lapsosIntervalo"]])))
    return values


def get_pistas(session, date, pistas_dia, form, headers):
    response = session.post(URL, headers=headers, data=form, timeout=10)
    if not response.ok:
        return
    data = json.loads(response.text)
    pistas = data["pistas"]
    inicio = data["Recursos"][0]["HoraInicio"]
    inicio = datetime.datetime.strptime(inicio, "%H:%M:%S")
    for pista in pistas:
        name = pista["DescripcionBasica"]
        if "individual" in name.lower():
            continue
        disponibilidad = get_disponibilidad(pista)
        horas_libres = [
            get_hora(inicio, pista["lapsosIntervalo"], i)
            for i, v in enumerate(disponibilidad)
            if v == 0
        ]
        if date.weekday() < 5:
            horas_libres = filtrar_horas(horas_libres)
        if horas_libres:
            for hora in horas_libres:
                pistas_dia.setdefault(hora.strftime('%H:%M'), []).append(name)

def procesar_pistas(pistas):
    msg = ""
    for dia in sorted(pistas.keys()):
        pistas_dia = pistas[dia]
        dia_semana = DIAS_SEMANA[dia.weekday()]
        dia_str = dia.strftime("%d/%m/%Y")
        msg += f"{dia_str} ({dia_semana})\n"
        for hora in sorted(pistas_dia.keys()):
            lista_pistas = pistas_dia[hora]
            msg += f"{hora}: "
            for pista in lista_pistas:
                msg += pista[:6].strip()
                msg += ", "
            msg = msg[:-2]
            msg += "\n"
        msg += "\n"
    return msg

def error(update: Update, context):
    print(f"Update {update} caused error {context.error}")


def comando_pistas_semana(update: Update, context):
    date = datetime.date.today()
    threads = []
    pistas = {}
    for _ in range(16):
        if date.weekday() >= 5:
            date += datetime.timedelta(days=1)
            continue

        thread = threading.Thread(target=get_pistas_day, args=(date, pistas))
        thread.start()
        threads.append(thread)

        date += datetime.timedelta(days=1)

    for thread in threads:
        thread.join()

    if pistas:
        msg = procesar_pistas(pistas)
        update.message.reply_text(msg)

def comando_pistas_finde(update: Update, context):
    date = datetime.date.today()
    threads = []
    pistas = {}
    for _ in range(16):
        if date.weekday() < 5:
            date += datetime.timedelta(days=1)
            continue
        thread = threading.Thread(target=get_pistas_day, args=(date, pistas))
        thread.start()
        threads.append(thread)

        date += datetime.timedelta(days=1)

    for thread in threads:
        thread.join()

    if pistas:
        # Maximum length 4096?
        msg = procesar_pistas(pistas)
        update.message.reply_text(msg)
        
def comando_audio(update: Update, context):
    """Transcribe an audio"""
    model = whisper.load_model("base")
    reply_to_message = update.message.reply_to_message
    if reply_to_message is not None and reply_to_message.voice is not None:
        new_file = context.bot.get_file(reply_to_message.voice.file_id)
        file_path = f"/tmp/voice_{random.randint(0, 1000)}.ogg"
        new_file.download(file_path)
        sound = AudioSegment.from_file(file_path)
        output = f"/tmp/audio_{random.randint(0, 1000)}.wav"
        sound.export(output, format="wav")
        try:
            data = model.transcribe(output)
            reply_to_message.reply_text(data["text"])
            os.remove(file_path)
            os.remove(output)
        except:
            reply_to_message.reply_text(error_message)
            os.remove(file_path)
            os.remove(output)
    else:
        response = "T K IAS"
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


def joseantonio_bot(request):


    if request.method == "POST":
        bot = telegram.Bot(token=TOKEN)
        dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)        
        # app = Application.builder().token(TOKEN).build()
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.add_handler(CommandHandler("hola", comando_hola))
        dispatcher.add_handler(CommandHandler("mimimi", comando_mimimi))
        dispatcher.add_handler(CommandHandler("pistas_finde", comando_pistas_finde))
        dispatcher.add_handler(CommandHandler("pistas_semana", comando_pistas_semana))
        dispatcher.add_handler(CommandHandler("kdise", comando_audio))
        # dispatcher.add_handler(MessageHandler(Filters.text, respuesta_rima))
        dispatcher.add_error_handler(error)

        dispatcher.process_update(update)

    return "Los máquinas están bien"        


# if __name__ == "__main__":
#     print("Primero que nada: Cómo están los máquinas?")

#     app = Application.builder().token(TOKEN).build()

#     app.add_handler(CommandHandler("hola", comando_hola))
#     app.add_handler(CommandHandler("mimimi", comando_mimimi))
#     app.add_handler(CommandHandler("pistas_finde", comando_pistas_finde))
#     app.add_handler(CommandHandler("pistas_semana", comando_pistas_semana))

#     app.add_handler(MessageHandler(filters.TEXT, respuesta_rima))

#     app.add_error_handler(error)

#     print("Polling...")
#     app.run_polling(poll_interval=5)

# import telegram

# TOKEN = "5547486353:AAF9ifGIhLpqYI6HdOFtrKBCsicNLSMqs-I"


# def joseantonio_bot(request):
#     bot = telegram.Bot(token=TOKEN)
#     if request.method == "POST":
#         update = telegram.Update.de_json(request.get_json(force=True), bot)
#         chat_id = update.message.chat.id
#         # Reply with the same message
#         bot.sendMessage(chat_id=chat_id, text=update.message.text)
        
#     return "okay"