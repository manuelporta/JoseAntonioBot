import os
import json
import datetime
import asyncio
import requests
import threading
from bs4 import BeautifulSoup


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
    6: "Domingo",
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
                pistas_dia.setdefault(hora.strftime("%H:%M"), []).append(name)


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

def get_pistas_full():
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
    else:
        msg = "Tengo un amigo que te lo hace mejor y más barato"
    
    return msg

def get_pistas_week():
    date = datetime.date.today()
    threads = []
    pistas = {}
    for _ in range(16):
        if date.weekday() >= 5:
            break

        thread = threading.Thread(target=get_pistas_day, args=(date, pistas))
        thread.start()
        threads.append(thread)

        date += datetime.timedelta(days=1)

    for thread in threads:
        thread.join()

    if pistas:
        msg = procesar_pistas(pistas)
    else:
        msg = "Tengo un amigo que te lo hace mejor y más barato"
    
    return msg

def get_pistas_finde():
    date = datetime.date.today()
    threads = []
    pistas = {}
    flag = True
    for _ in range(16):
        if date.weekday() < 5:
            if flag:
                date += datetime.timedelta(days=1)
                continue
            else:
                break
        flag = False
        thread = threading.Thread(target=get_pistas_day, args=(date, pistas))
        thread.start()
        threads.append(thread)

        date += datetime.timedelta(days=1)

    for thread in threads:
        thread.join()

    if pistas:
        msg = procesar_pistas(pistas)
    else:
        msg = "Tengo un amigo que te lo hace mejor y más barato"
    
    return msg

def get_pistas_today():
    date = datetime.date.today()
    threads = []
    pistas = {}
    get_pistas_day(date, pistas)

    if pistas:
        msg = procesar_pistas(pistas)
    else:
        msg = "Tengo un amigo que te lo hace mejor y más barato"
    
    return msg

def get_pistas_mañana():
    date = datetime.date.today()
    date += datetime.timedelta(days=1)
    threads = []
    pistas = {}
    get_pistas_day(date, pistas)

    if pistas:
        msg = procesar_pistas(pistas)
    else:
        msg = "Tengo un amigo que te lo hace mejor y más barato"
    
    return msg

def get_pistas_ndias(n):
    date = datetime.date.today()
    threads = []
    pistas = {}
    for _ in range(n):
        
        thread = threading.Thread(target=get_pistas_day, args=(date, pistas))
        thread.start()
        threads.append(thread)

        date += datetime.timedelta(days=1)

    for thread in threads:
        thread.join()

    if pistas:
        msg = procesar_pistas(pistas)
    else:
        msg = "Tengo un amigo que te lo hace mejor y más barato"
    
    return msg