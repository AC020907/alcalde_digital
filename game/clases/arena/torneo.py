"""
Torneo de Arena Civitas: Consejo Civico (rondas de reglas.py) + cinco pruebas con los minijuegos de Historia.

Python puro: lo usan el servidor TCP (LAN) y la sala online. El servidor es la unica autoridad:
- elige la semilla y los ajustes de cada prueba (iguales para todos: condiciones equivalentes);
- recibe de cada cliente las DECISIONES que tomo (no su puntuacion) y las vuelve a puntuar:
    Moderacion  -> rejuega la cola con la misma semilla y las decisiones recibidas (ColaModeracion).
    Rastreador  -> rejuega los intentos de cadena sobre el mismo puzzle (PuzzleEvidencias).
    Caza-Rumores / Gran Viralizacion -> reconstruye la simulacion (CazaRumores) para conocer la base y el
                   umbral, valida coherencia y calcula la viralidad. (El tiempo real no se puede rejugar:
                   limitacion documentada.)
    Duelo       -> recalcula precision, combo y puntos nota a nota con el chart del servidor (Ritmo).
- normaliza cada prueba a 0-1000 y el Consejo Civico a 0-2000;
- aplica consecuencias colectivas a Ciudad Nova (los mismos indicadores del Consejo, sin reiniciarlos).
"""
import json
import os
import random

from clases.ConfigMinijuegos import MODOS as MODOS_ARCADE
from clases.CazaRumores import CazaRumores
from clases import Plataformas as PL
from clases.Moderador import ColaModeracion
from clases.PuzzleEvidencias import PuzzleEvidencias
from clases.RedCivitas import crear_red_civitas, ORIGEN_RUMOR, CANDIDATOS_FOCO
from clases.Ritmo import VALOR_JUICIO, validar_chart
from clases.moderacion_datos import publicaciones_moderacion
from clases.arena.reglas import NOMBRE_INDICADOR

PRUEBAS = ("moderador", "rastreador", "contencion", "plataformas", "ritmo")   # el Duelo cierra el torneo
NOMBRE_CORTO = {"moderador": "Moderación", "contencion": "Caza-Rumores", "rastreador": "Rastreador",
                "plataformas": "Ruta", "ritmo": "Duelo"}
NOMBRE_PRUEBA = {"moderador": "Moderación Express", "contencion": "Caza-Rumores", "rastreador": "Rastreador",
                 "plataformas": "Ruta de la Verdad", "ritmo": "Duelo de Frecuencias"}
MAX_PRUEBA = 1000
MAX_CONSEJO = 2000     # 5 pruebas x 1000 + Consejo 2000 = 7000. El Consejo pesa ~29% (mas que cualquier prueba, 14%).

MODOS_TORNEO = {
    "completo": {"rondas_civicas": 5, "segundos": 25, "moderador": {"cantidad": 12},
                 "contencion": {"duracion": 40.0}, "plataformas": {"nivel": "arena"},
                 "rastreador": {"eslabones": 3, "senuelos": 3, "tiempo": 120.0},
                 "ritmo": {"modo": "historia"}},
    # Feria: 2 rondas civicas (arbol, grafo, propagacion y roles siguen presentes) y retos mas cortos.
    "feria": {"rondas_civicas": 2, "segundos": 20, "moderador": {"cantidad": 8},
              "contencion": {"duracion": 25.0}, "plataformas": {"nivel": "feria"},
              "rastreador": {"eslabones": 2, "senuelos": 2, "tiempo": 75.0},
              "ritmo": {"modo": "feria"}},
}
RITMO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ritmo")


class ResultadoInvalido(ValueError):
    pass


def cargar_chart(modo):
    """Chart competitivo: siempre dificultad Normal (mismo chart para todos)."""
    with open(os.path.join(RITMO_DIR, "duelo_%s_normal.json" % modo), encoding="utf-8") as f:
        chart = json.load(f)
    assert not validar_chart(chart)
    return chart


# ---------- preparar cada prueba (igual para todos) ----------
def preparar_prueba(clave, modo_torneo, semilla, indicadores):
    """Spec que el servidor envia a todos los clientes. El contexto sale del Consejo Civico (compartido)."""
    cfg = dict(MODOS_TORNEO[modo_torneo][clave])
    ind = indicadores
    spec = {"clave": clave, "nombre": NOMBRE_PRUEBA[clave], "semilla": semilla, "ajustes": {}, "contexto": ""}
    if clave == "moderador":
        spec["cantidad"] = cfg["cantidad"]
        extra = 2 if ind["conflictos"] >= 40 else 0
        spec["cantidad"] += extra
        spec["contexto"] = ("Los conflictos del Consejo (%d) llenaron los comentarios: llegan %d más." % (ind["conflictos"], extra)
                            if extra else "Comentarios en los perfiles de los candidatos tras el Consejo Cívico.")
    elif clave == "contencion":
        n_focos = 3 if ind["desinformacion"] >= 50 else 2
        spec["focos"] = random.Random("focos|%s" % semilla).sample(CANDIDATOS_FOCO, n_focos)
        spec["ajustes"] = {"duracion": cfg["duracion"]}
        spec["contexto"] = ("La desinformación quedó en %d: el rumor arranca en %d focos." % (ind["desinformacion"], n_focos))
    elif clave == "plataformas":
        # Misma geometria y mismo tiempo para todos: el contexto del Consejo solo cambia el relato, no la dificultad.
        nivel = PL.Nivel(cfg["nivel"])
        spec.update(nivel=cfg["nivel"], evidencias=len(nivel.evidencias), limite_s=nivel.limite_ticks // PL.TICKS_S)
        spec["contexto"] = ("La Gran Viralización: con %d rumores en circulación, NOVA lanza su ola. Entren a su sistema "
                            "y rescaten la evidencia original." % ind["rumores"])
    elif clave == "rastreador":
        spec["ajustes"] = {"eslabones": cfg["eslabones"], "senuelos": cfg["senuelos"], "tiempo": cfg["tiempo"]}
        spec["contexto"] = "Reconstruye la cadena del rumor más compartido del Consejo hasta su origen."
    elif clave == "ritmo":
        chart = cargar_chart(cfg["modo"])
        spec.update(modo=cfg["modo"], dificultad="normal", notas=len(chart["notes"]),
                    duracion_ms=chart["duration_ms"], chart_id="%s_normal_v%s" % (cfg["modo"], chart["version"]))
        spec["contexto"] = "Final: NOVA secuestra la transmisión. Misma canción y mismo chart para todos."
    return spec


def limite_segundos(spec):
    """Tiempo maximo que el servidor espera resultados de una prueba (luego cuenta como no entregada)."""
    c = spec["clave"]
    if c == "moderador":
        return 15 + spec["cantidad"] * 5
    if c == "contencion":
        return spec["ajustes"]["duracion"] + 45
    if c == "plataformas":
        return spec["limite_s"] + 45
    if c == "rastreador":
        return spec["ajustes"]["tiempo"] + 45
    return spec["duracion_ms"] / 1000.0 + 60


# ---------- puntuar en el servidor ----------
def _entero(v, lo, hi, campo):
    if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
        raise ResultadoInvalido("Campo %s fuera de rango." % campo)
    return v


def _numero(v, lo, hi, campo):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
        raise ResultadoInvalido("Campo %s fuera de rango." % campo)
    return float(v)


def puntuar_moderador(spec, datos):
    decisiones = datos.get("decisiones")
    pubs, _ = publicaciones_moderacion(spec["semilla"], spec["cantidad"])
    if not isinstance(decisiones, list) or len(decisiones) > len(pubs) or not all(isinstance(d, bool) for d in decisiones):
        raise ResultadoInvalido("Decisiones de moderación inválidas.")
    cola = ColaModeracion(pubs, cuenta_regresiva=0)
    for d in decisiones:
        if cola.terminado():
            break
        cola.decidir(d)
    while not cola.terminado():          # tarjetas sin decidir = se acabo su tiempo (lo mismo que aprobar)
        cola.decidir(False)
    censuras = sum(1 for pub, borro, _ok in cola.historial if borro and not pub.es_falsa)
    colados = sum(1 for pub, borro, _ok in cola.historial if not borro and pub.es_falsa)
    norm = 1000.0 * cola.aciertos / cola.total - 120 * censuras - 60 * colados
    return {"normalizado": int(max(0, min(MAX_PRUEBA, round(norm)))), "precision": round(cola.aciertos / float(cola.total), 3),
            "detalle": {"aciertos": cola.aciertos, "total": cola.total, "censuras": censuras, "bots_colados": colados,
                        "mejor_racha": cola.mejor_racha, "vidas": cola.vidas},
            "resumen": "%d/%d bien moderados%s" % (cola.aciertos, cola.total,
                                                    ", %d críticas legítimas borradas" % censuras if censuras else "")}


def _sim_arcade(spec):
    return CazaRumores(crear_red_civitas(), "contencion", spec["focos"], spec["semilla"], spec["ajustes"])


def puntuar_arcade(spec, datos):
    sim = _sim_arcade(spec)
    reposts = _entero(datos.get("reposts"), int(sim.reposts_base), 10 ** 7, "reposts")
    interceptados = _entero(datos.get("interceptados"), 0, 600, "interceptados")
    exito = datos.get("exito")
    if not isinstance(exito, bool):
        raise ResultadoInvalido("Falta el resultado.")
    v = min(1.0, (reposts - sim.reposts_base) / float(sim.cfg["umbral_viral"]))
    if exito and v >= 1.0:
        raise ResultadoInvalido("Resultado incoherente: superó el umbral viral y dice haber contenido el rumor.")
    norm = 650 * (1 - v) + (250 if exito else 0) + min(100, interceptados * 4)
    return {"normalizado": int(max(0, min(MAX_PRUEBA, round(norm)))), "precision": round(1 - v, 3),
            "detalle": {"viralidad": round(v, 3), "interceptados": interceptados, "contenido": exito},
            "resumen": "%s · viralidad %d%% · %d rumores interceptados" % (
                "Contenido" if exito else "Se volvió viral", int(v * 100), interceptados)}


def puntuar_rastreador(spec, datos):
    cfg = spec["ajustes"]
    p = PuzzleEvidencias(crear_red_civitas(), spec["semilla"], eslabones=cfg["eslabones"], senuelos=cfg["senuelos"],
                         tiempo=cfg["tiempo"])
    intentos = datos.get("intentos")
    pistas = _entero(datos.get("pistas", 0), 0, 20, "pistas")
    segundos = _numero(datos.get("segundos"), 2, cfg["tiempo"], "segundos")
    if not isinstance(intentos, list) or len(intentos) > p.comprobaciones:
        raise ResultadoInvalido("Intentos inválidos.")
    p.empezar()
    correctos = 0
    for intento in intentos:
        if not (isinstance(intento, list) and len(intento) == 2 and isinstance(intento[0], list)
                and len(intento[0]) == p.eslabones and all(isinstance(c, str) for c in intento[0])):
            raise ResultadoInvalido("Intento con formato inválido.")
        if not p.jugando():
            break
        for i, carta in enumerate(intento[0]):
            p.colocar(carta, i)
        p.elegir_conclusion(intento[1])
        if not p.comprobar():
            raise ResultadoInvalido("Intento incompleto.")
        correctos = max(correctos, sum(1 for r in p.revision if r))
    usados = len(intentos)
    if p.exito():
        norm = 620 + 380 * (1 - segundos / cfg["tiempo"]) - 70 * pistas - 60 * (usados - 1)
        norm = max(250, norm)
    else:
        norm = 100 * correctos
    return {"normalizado": int(max(0, min(MAX_PRUEBA, round(norm)))), "precision": round(correctos / float(p.eslabones), 3),
            "detalle": {"origen_encontrado": p.exito(), "comprobaciones": usados, "pistas": pistas, "segundos": round(segundos, 1)},
            "resumen": ("Origen encontrado en %d s (%d comprobación%s)" % (segundos, usados, "" if usados == 1 else "es"))
            if p.exito() else "%d de %d eslabones correctos" % (correctos, p.eslabones)}


def puntuar_ritmo(spec, datos, chart=None):
    chart = chart or cargar_chart(spec["modo"])
    juicios = datos.get("juicios")
    if datos.get("dificultad") != "normal":
        raise ResultadoInvalido("En el torneo el Duelo es en dificultad Normal (mismo chart para todos).")
    if not isinstance(juicios, list) or len(juicios) != len(chart["notes"]) or not all(j in VALOR_JUICIO for j in juicios):
        raise ResultadoInvalido("Juicios del Duelo inválidos: deben ser uno por nota del chart.")
    conteo = {j: juicios.count(j) for j in VALOR_JUICIO}
    combo = mejor = 0
    for j in juicios:
        combo = combo + 1 if j in ("perfect", "good") else 0
        mejor = max(mejor, combo)
    total = float(len(juicios))
    precision = sum(VALOR_JUICIO[j] for j in juicios) / total
    norm = 850 * precision + 150 * mejor / total
    return {"normalizado": int(round(norm)), "precision": round(precision, 3),
            "detalle": {"conteo": conteo, "max_combo": mejor, "notas": len(juicios)},
            "resumen": "Precisión %d%% · combo máximo x%d" % (int(precision * 100), mejor)}


def puntuar_plataformas(spec, datos):
    """El cliente envia su traza de entradas; el servidor REJUEGA la carrera con el mismo motor y puntua."""
    try:
        p = PL.rejugar(spec["nivel"], datos.get("traza"))
    except PL.TrazaInvalida as e:
        raise ResultadoInvalido(str(e))
    r = p.resumen()
    return {"normalizado": r["score_normalized"], "precision": round(r["evidence"] / float(max(1, r["evidence_total"])), 3),
            "detalle": r,
            "resumen": "%s · %d/%d evidencias · %d detecciones · %d s" % (
                "Archivo recuperado" if r["completed"] else "No llegó al archivo", r["evidence"], r["evidence_total"],
                r["deaths"], r["elapsed_ms"] // 1000)}


PUNTUAR = {"moderador": puntuar_moderador, "contencion": puntuar_arcade, "plataformas": puntuar_plataformas,
           "rastreador": puntuar_rastreador, "ritmo": puntuar_ritmo}


def puntuar(spec, datos):
    if not isinstance(datos, dict):
        raise ResultadoInvalido("Resultado inválido.")
    return PUNTUAR[spec["clave"]](spec, datos)


def no_entregado():
    return {"normalizado": 0, "precision": 0.0, "detalle": {}, "resumen": "No completó la prueba (desconexión o tiempo)."}


# ---------- consecuencias colectivas ----------
EFECTO = {   # indicador -> signo; la media del grupo (0..1) se centra en 0.5: jugar bien mejora la ciudad
    "moderador": {"convivencia": 6, "confianza": 3},
    "contencion": {"desinformacion": -8, "rumores": -4},
    "rastreador": {"info_verificada": 8, "confianza": 3},
    "plataformas": {"conflictos": -8, "rumores": -6},
    "ritmo": {"participacion": 8, "confianza": 3},
}


def consecuencias(clave, normalizados):
    media = sum(normalizados) / float(len(normalizados) * MAX_PRUEBA) if normalizados else 0.0
    delta = {k: int(round(v * (media - 0.5) * 2)) for k, v in EFECTO[clave].items()}
    return media, {k: v for k, v in delta.items() if v}


def puntos_consejo(puntos, rondas):
    """Puntos del Consejo Civico (pueden ser negativos) -> 0..2000. 1000 = neutral."""
    return int(max(0, min(MAX_CONSEJO, round(1000 + 1000.0 * puntos / (20.0 * max(1, rondas))))))


class TorneoArena(object):
    """Fase de torneo sobre una Partida ya jugada (mismos indicadores, mismos jugadores)."""

    def __init__(self, partida, modo="completo"):
        self.partida = partida
        self.modo = modo
        self.indice = -1
        self.spec = None
        self.entregas = {}           # jid -> resultado puntuado de la prueba actual
        self.puntuaciones = {}        # jid -> {prueba: resultado} (los jugadores entran despues, en el lobby)
        self.historial = []          # resumen de cada prueba (para pantallas y explicacion)
        self.terminado = False

    def abrir_siguiente(self):
        self.indice += 1
        if self.indice >= len(PRUEBAS):
            self.terminado = True
            return None
        clave = PRUEBAS[self.indice]
        semilla = random.Random("torneo|%s|%s" % (self.partida.semilla, clave)).randrange(10 ** 6)
        self.spec = preparar_prueba(clave, self.modo, semilla, self.partida.indicadores)
        self.spec.update(indice=self.indice, total=len(PRUEBAS))
        self.entregas = {}
        return self.spec

    def entregar(self, jid, datos):
        if self.spec is None or self.terminado:
            raise ResultadoInvalido("No hay ninguna prueba abierta.")
        if jid not in self.partida.jugadores:
            raise ResultadoInvalido("Jugador desconocido.")
        if jid in self.entregas:
            raise ResultadoInvalido("Ya entregaste esta prueba.")
        self.entregas[jid] = puntuar(self.spec, datos)
        return self.entregas[jid]

    def todos_entregaron(self):
        return all(jid in self.entregas or not j.conectado for jid, j in self.partida.jugadores.items())

    def cerrar_prueba(self):
        clave = self.spec["clave"]
        for jid in self.partida.jugadores:
            self.puntuaciones.setdefault(jid, {})[clave] = self.entregas.get(jid) or no_entregado()
        normalizados = [self.puntuaciones[jid][clave]["normalizado"] for jid in self.partida.jugadores]
        media, delta = consecuencias(clave, normalizados)
        for k, v in delta.items():
            self.partida.indicadores[k] = max(0, min(100, self.partida.indicadores[k] + v))
        ganador = max(self.partida.jugadores, key=lambda j: (self.puntuaciones[j][clave]["normalizado"], -int(j[1:])))
        resumen = {"indice": self.indice, "clave": clave, "nombre": NOMBRE_PRUEBA[clave],
                   "ganador": ganador, "ganador_nombre": self.partida.jugadores[ganador].nombre,
                   "media": round(media * 100), "delta_ciudad": delta, "indicadores": dict(self.partida.indicadores),
                   "resultados": {jid: self.puntuaciones[jid][clave] for jid in self.partida.jugadores},
                   "clasificacion": self.clasificacion()}
        self.historial.append(resumen)
        self.spec = None
        return resumen

    def clasificacion(self):
        filas = []
        for jid, j in self.partida.jugadores.items():
            consejo = puntos_consejo(j.puntos, self.partida.total_rondas)
            pruebas = {k: v["normalizado"] for k, v in self.puntuaciones.get(jid, {}).items()}
            filas.append({"id": jid, "nombre": j.nombre, "rol": j.rol, "consejo": consejo, "pruebas": pruebas,
                          "total": consejo + sum(pruebas.values()), "logros": list(j.logros)})
        filas.sort(key=lambda f: (-f["total"], -f["pruebas"].get("ritmo", 0), f["id"]))
        for i, f in enumerate(filas):
            f["posicion"] = i + 1
        return filas

    def final(self):
        """Eleccion con los indicadores finales (Consejo + torneo) y campeon del torneo: conceptos distintos."""
        eleccion = self.partida.elegir_alcalde()
        tabla = self.clasificacion()
        for h in self.historial:
            if h["delta_ciudad"]:
                eleccion["explicacion"].append("%s: la media del grupo fue %d/100, así que %s." % (
                    h["nombre"], h["media"], ", ".join("%s %+d" % (NOMBRE_INDICADOR[k].lower(), v)
                                                      for k, v in h["delta_ciudad"].items())))
        eleccion["torneo"] = {"campeon": tabla[0]["id"], "campeon_nombre": tabla[0]["nombre"], "clasificacion": tabla,
                              "pruebas": [{"clave": h["clave"], "nombre": h["nombre"], "ganador_nombre": h["ganador_nombre"]}
                                          for h in self.historial],
                              "mensaje": mensaje_final(tabla[0], eleccion["ciudad"])}
        return eleccion


def mensaje_final(campeon, ciudad):
    if ciudad["indice"] < 50:
        return ("%s gana el torneo, pero Ciudad Nova termina en crisis: ganar puntos no es lo mismo que cuidar "
                "una comunidad digital." % campeon["nombre"])
    return "%s gana el torneo y Ciudad Nova termina como «%s»." % (campeon["nombre"], ciudad["titulo"])


# ---------- bots: entregan DECISIONES plausibles, que el servidor puntua igual que las de una persona ----------
def payload_bot(spec, nivel, rng):
    """nivel 0..1: probabilidad de acertar cada decision."""
    c = spec["clave"]
    if c == "moderador":
        pubs, _ = publicaciones_moderacion(spec["semilla"], spec["cantidad"])
        return {"decisiones": [p.es_falsa if rng.random() < nivel else not p.es_falsa for p in pubs]}
    if c == "plataformas":
        return {"traza": PL.bot(spec["nivel"], rng, nivel).traza}
    if c == "contencion":
        sim = _sim_arcade(spec)
        umbral = sim.cfg["umbral_viral"]
        v = max(0.0, min(1.0, 1 - nivel + rng.uniform(-.15, .15)))
        exito = v < .8
        if not exito:
            v = 1.0
        return {"reposts": int(sim.reposts_base + v * umbral), "interceptados": int(nivel * 20 + rng.randint(0, 5)),
                "exito": exito}
    if c == "rastreador":
        cfg = spec["ajustes"]
        p = PuzzleEvidencias(crear_red_civitas(), spec["semilla"], eslabones=cfg["eslabones"],
                             senuelos=cfg["senuelos"], tiempo=cfg["tiempo"])
        ok = [list(p.solucion), p.tipo_origen()]
        malo = [list(reversed(p.solucion)), next(c for c in p.opciones_conclusion if c != p.tipo_origen())]
        r = rng.random()
        intentos = [malo, malo] if r > nivel else [malo, ok] if r > (1 + nivel) / 2 else [ok]
        return {"intentos": intentos, "pistas": 0 if nivel > .6 else 1,
                "segundos": round(cfg["tiempo"] * max(.1, min(.95, 1.05 - nivel + rng.uniform(-.1, .1))), 1)}
    chart = cargar_chart(spec["modo"])
    juicios = []
    for _ in chart["notes"]:
        r = rng.random()
        juicios.append("perfect" if r < nivel * .7 else "good" if r < nivel else "bad" if r < nivel + .15 else "miss")
    return {"dificultad": "normal", "juicios": juicios}
