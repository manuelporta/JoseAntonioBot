import time
import datetime
import requests
from bs4 import BeautifulSoup
import json

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


def get_pistas_day(day, msg):
    FORM_DATA["fechaInicio"] = day.strftime("%d/%m/%Y")
    FORM_DATA["fechaFin"] = FORM_DATA["fechaInicio"]
    new_msg = ""
    for centro in CENTROS.keys():
        FORM_DATA["IdCentro"] = CENTROS[centro]
        FORM_DATA["IdDeporte"] = IDS[centro]
        new_msg = get_pistas_centro(CENTROS[centro], day, new_msg)
    if new_msg:
        msg += f"{FORM_DATA['fechaInicio']}\n"
        msg += new_msg
    return msg


def get_pistas_centro(centro, date, msg):
    with requests.Session() as session:
        get_token(session, centro)
        msg = get_pistas(session, date, msg)

    return msg


def get_token(session, centro):
    aux_url = f"https://maisqueauga.deporsite.net/reserva-recursos-mqa?IdCentro={centro}&IdDeporte=18"
    r = session.get(aux_url)
    if not r.ok:
        # TODO
        return
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.select_one('meta[name="csrf-token"]')["content"]
    HEADERS["Cookie"] = "; ".join([x.name + "=" + x.value for x in r.cookies])
    HEADERS["X-CSRF-TOKEN"] = token


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


def get_pistas(session, date, msg):
    response = session.post(URL, headers=HEADERS, data=FORM_DATA, timeout=10)
    if not response.ok:
        # TODO
        return msg
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
            msg += f"· {name} a las: {', '.join([hora.strftime('%H:%M') for hora in horas_libres])}\n"
    return msg


def pistas_semana():
    date = datetime.date.today()
    msg = ""
    for _ in range(16):
        if date.weekday() >= 5:
            date += datetime.timedelta(days=1)
            continue
        msg = get_pistas_day(date, msg)
        date += datetime.timedelta(days=1)
    if msg:
        print(msg)


def pistas_finde():
    date = datetime.date.today()
    msg = ""
    for _ in range(16):
        if date.weekday() < 5:
            date += datetime.timedelta(days=1)
            continue
        msg = get_pistas_day(date, msg)
        date += datetime.timedelta(days=1)
    if msg:
        # Maximum length 4096?
        print(msg)


def main():
    """Start the bot."""
    start = time.time()
    print("Pistas semana: ")
    pistas_semana()
    elapsed = datetime.datetime.fromtimestamp(time.time() - start)
    print(f"Done in {elapsed.strftime('%M:%S.%f')}")

    start = time.time()
    print("Pistas finde: ")
    pistas_finde()
    elapsed = datetime.datetime.fromtimestamp(time.time() - start)
    print(f"Done in {elapsed.strftime('%M:%S.%f')}")


if __name__ == "__main__":
    main()
