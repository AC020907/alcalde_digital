"""
Arena Online narrativa (campana): una historia compartida, cuatro perspectivas y cinco retos que juegan TODOS.
Reloj simulado y API HTTP real (TestClient):
- 2, 3 y 4 clientes completan las 5 rondas: escena -> reto -> resultado -> decision civica -> consecuencia;
- las pistas privadas llegan solo a su rol (sin filtraciones) y los roles ausentes no bloquean la historia;
- cada reto lo puntua el servidor (decisiones juzgadas, tablero en servidor, rejuego de trazas e intercepciones);
- resultados manipulados, duplicados, entregas antes de tiempo, desconexion, pausa y pantalla de espectadores.
"""
import random

import pytest

from clases import Plataformas as PL
from clases.arena import campana as CA
from clases.arena import caza_web as CW
from clases.arena import duelo_online as DO

ROLES = ["ciudadano", "periodista", "influencer", "candidato"]
ORDEN_RETOS = ["moderador", "rastreador", "contencion", "plataformas", "ritmo"]


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


@pytest.fixture
def reloj(client):
    r = Reloj()
    client.app.state.arena.reloj = r
    return r


def post(client, codigo, orden, **datos):
    return client.post("/api/arena/salas/%s/%s" % (codigo, orden), json=datos)


def vista(client, codigo, token):
    r = client.get("/api/arena/salas/%s" % codigo, params={"token": token})
    assert r.status_code == 200, r.text
    return r.json()


def preparar(client, n, bots=False, modo="feria"):
    r = client.post("/api/arena/salas", json={"nombre": "J1", "rol": ROLES[0], "modo": modo})
    assert r.status_code == 200, r.text
    codigo, tokens = r.json()["codigo"], [r.json()["token"]]
    for i, rol in enumerate(ROLES[1:n]):
        t = client.post("/api/arena/salas/%s/unir" % codigo, json={"nombre": "J%d" % (i + 2), "rol": rol}).json()["token"]
        tokens.append(t)
        assert post(client, codigo, "listo", token=t, listo=True).status_code == 200
    if bots:
        assert post(client, codigo, "bots", token=tokens[0]).status_code == 200
    assert post(client, codigo, "empezar", token=tokens[0]).status_code == 200
    return codigo, tokens


def avanzar(client, reloj, codigo, tokens, segundos):
    while segundos > 0:
        paso = min(4.0, segundos)
        reloj.t += paso
        segundos -= paso
        for t in tokens:
            client.get("/api/arena/salas/%s" % codigo, params={"token": t})


def sala_de(client, codigo):
    return client.app.state.arena.sala(codigo)


def jugar_reto(client, reloj, codigo, tokens, niveles=(0.95, 0.75, 0.5, 0.25)):
    """Cada cliente juega el reto en curso por la API, como lo haria el navegador. Devuelve la clave del reto."""
    v = vista(client, codigo, tokens[0])
    reto = v["reto"]
    clave = reto["clave"]
    sala = sala_de(client, codigo)
    avanzar(client, reloj, codigo, tokens, reto["inicio_en_ms"] / 1000.0 + 0.2)
    if clave in ("contencion", "plataformas", "ritmo"):
        avanzar(client, reloj, codigo, tokens, reto["duracion_ms"] / 1000.0)
    for i, t in enumerate(tokens):
        rng = random.Random(i)
        nivel = niveles[i]
        if clave == "moderador":
            pubs = sala.reto["pubs"]
            for k, pub in enumerate(pubs):
                eliminar = pub.es_falsa if rng.random() < nivel else not pub.es_falsa
                r = post(client, codigo, "moderar", token=t, indice=k, eliminar=eliminar, id="m%d-%d" % (i, k))
                assert r.status_code == 200, r.text
                assert r.json()["correcto"] == (eliminar == pub.es_falsa)
                if r.json()["terminado"]:
                    break
        elif clave == "rastreador":
            tablero = vista(client, codigo, t)["reto"]["tablero"]
            assert "solucion" not in str(tablero) and "origen" not in tablero       # el origen no viaja al cliente
            p = sala.reto["estado"]["j%d" % (i + 1)]
            if nivel < 0.6:
                mala = list(reversed(p.solucion))
                otra = next(c for c in p.opciones_conclusion if c != p.tipo_origen())
                r = post(client, codigo, "rastrear", token=t, accion="comprobar", slots=mala, conclusion=otra)
                assert r.status_code == 200 and r.json()["estado"] == "jugando" and r.json()["explicaciones"]
                assert post(client, codigo, "rastrear", token=t, accion="pista").status_code == 200
            r = post(client, codigo, "rastrear", token=t, accion="comprobar", slots=list(p.solucion), conclusion=p.tipo_origen())
            assert r.status_code == 200, r.text
            assert r.json()["estado"] == "victoria" and r.json()["resultado"]["normalizado"] > 0
        elif clave == "contencion":
            datos = CW.toques_bot(reto["config"], nivel, rng)
            r = post(client, codigo, "reto", token=t, id="c%d" % i, datos=datos)
            assert r.status_code == 200, r.text
            assert r.json()["resultado"]["normalizado"] == CW.puntuar(reto["config"], datos)["normalizado"]
        elif clave == "plataformas":
            carrera = PL.bot(reto["config"]["nivel"], rng, nivel)
            r = post(client, codigo, "reto", token=t, id="p%d" % i, datos={"traza": carrera.traza, "score_normalized": 1000})
            assert r.status_code == 200, r.text
            assert r.json()["resultado"]["normalizado"] == carrera.puntuacion()      # el servidor rejuega; ignora el campo enviado
        else:
            chart = client.get("/api/arena/ritmo/" + reto["config"]["modo"]).json()["chart"]
            datos = DO.payload_bot(chart, nivel, rng)
            r = post(client, codigo, "reto", token=t, id="d%d" % i, datos=datos)
            assert r.status_code == 200, r.text
            assert r.json()["resultado"]["normalizado"] == DO.validar_y_puntuar(chart, datos, 10 ** 9)["normalizado"]
    return clave


def hasta(client, reloj, codigo, tokens, fase, limite=400):
    for _ in range(limite):
        v = vista(client, codigo, tokens[0])
        if v["fase"] == fase:
            return v
        if v["fase"] == "escena":
            for t in tokens:
                post(client, codigo, "escena", token=t)
        elif v["fase"] == "ronda":
            for t in tokens:
                vt = vista(client, codigo, t)
                if not vt["ya_decidiste"]:
                    assert post(client, codigo, "accion", token=t, ronda=vt["ronda"], ruta=[2]).status_code == 200
            reloj.t += 1
        elif v["fase"] in ("resultado", "reto_resultado"):
            post(client, codigo, "continuar", token=tokens[0])
        else:
            reloj.t += 1
    raise AssertionError("no se llego a %s (fase %s)" % (fase, v["fase"]))


@pytest.mark.parametrize("n", [2, 3, 4])
def test_campana_completa_2_3_4_jugadores(client, reloj, n):
    codigo, tokens = preparar(client, n)
    retos, fases = [], []
    for ronda in range(5):
        v = hasta(client, reloj, codigo, tokens, "escena")
        assert v["escena"]["ronda"] == ronda + 1 and v["ronda"] == ronda
        hasta(client, reloj, codigo, tokens, "reto")
        retos.append(jugar_reto(client, reloj, codigo, tokens))            # TODOS compiten en cada reto
        v = hasta(client, reloj, codigo, tokens, "reto_resultado")
        resumen = v["reto_resumen"]
        assert len(resumen["resultados"]) == n and resumen["ganador"] == "j1"
        for t in tokens[1:]:
            assert vista(client, codigo, t)["reto_resumen"] == resumen       # resultado sincronizado
        v = hasta(client, reloj, codigo, tokens, "ronda")                    # decision civica ligada a la ronda
        assert v["decision_intro"] and v["arbol"]["hijos"]
        v = hasta(client, reloj, codigo, tokens, "resultado")                # consecuencia: BFS e indicadores
        assert "n_alcanzados" in v["resultado"] and v["resultado"]["delta_indicadores"] is not None
        fases.append(v["ronda"])
    assert retos == ORDEN_RETOS and fases == [1, 2, 3, 4, 5]
    hasta(client, reloj, codigo, tokens, "final")
    finales = [vista(client, codigo, t)["final"] for t in tokens]
    assert all(f == finales[0] for f in finales)
    tor = finales[0]["torneo"]
    assert tor["campeon"] == "j1" and len(tor["clasificacion"]) == n and len(tor["pruebas"]) == 5
    for fila in tor["clasificacion"]:
        assert set(fila["pruebas"]) == set(ORDEN_RETOS)
        assert fila["total"] == fila["consejo"] + sum(fila["pruebas"].values())
    assert finales[0]["ganador"] and finales[0]["ciudad"]["titulo"]         # tres resultados distintos: campeon, alcalde, ciudad


def test_pistas_privadas_solo_llegan_a_su_rol(client, reloj):
    codigo, tokens = preparar(client, 4)
    for ronda in CA.RONDAS:
        vistas = [hasta(client, reloj, codigo, [t], "escena") if i == 0 else vista(client, codigo, t) for i, t in enumerate(tokens)]
        for i, v in enumerate(vistas):
            rol = ROLES[i]
            texto = str(v)
            assert v["escena"]["privada"]["texto"] == ronda["privada"][rol][1]
            for otro in ROLES:
                if otro != rol:
                    assert ronda["privada"][otro][1] not in texto, (rol, otro)   # ni rastro de la pista ajena
            assert [x["texto"] for x in v["escena"]["comun"]] == [t for _q, t in ronda["comun"]]
            assert "ausente" not in v["escena"]                                 # con los 4 roles no hace falta NPC
        publico = client.get("/api/arena/salas/%s/publico" % codigo).json()
        for rol in ROLES:
            assert ronda["privada"][rol][1] not in str(publico)                 # espectadores: sin pistas
        hasta(client, reloj, codigo, tokens, "reto")
        jugar_reto(client, reloj, codigo, tokens)
        hasta(client, reloj, codigo, tokens, "resultado")
        if ronda is not CA.RONDAS[-1]:
            post(client, codigo, "continuar", token=tokens[0])


def test_rol_ausente_no_bloquea_la_historia(client, reloj):
    codigo, tokens = preparar(client, 2)                  # ciudadano y periodista: faltan influencer y candidato
    vistos = []
    for _ in range(5):
        v = hasta(client, reloj, codigo, tokens, "escena")
        vistos.append((v["escena"]["protagonista"], "ausente" in v["escena"]))
        hasta(client, reloj, codigo, tokens, "reto")
        jugar_reto(client, reloj, codigo, tokens)
        hasta(client, reloj, codigo, tokens, "resultado")
        post(client, codigo, "continuar", token=tokens[0])
    assert vistos == [("ciudadano", False), ("periodista", False), ("candidato", True), ("influencer", True), (None, False)]


def test_escena_avanza_sola_y_reto_no_empieza_antes(client, reloj):
    codigo, tokens = preparar(client, 2)
    assert vista(client, codigo, tokens[0])["fase"] == "escena"
    post(client, codigo, "escena", token=tokens[0])
    assert vista(client, codigo, tokens[0])["fase"] == "escena"            # falta el otro jugador
    avanzar(client, reloj, codigo, tokens, CA.SEGUNDOS_ESCENA + 1)        # nadie mas pulsa: avanza por tiempo
    v = vista(client, codigo, tokens[0])
    assert v["fase"] == "reto" and v["reto"]["clave"] == "moderador" and v["reto"]["inicio_en_ms"] > 0
    r = post(client, codigo, "moderar", token=tokens[0], indice=0, eliminar=True)
    assert r.status_code == 409                                            # cuenta atras: aun no empieza
    assert post(client, codigo, "pausa", token=tokens[0], pausar=True).status_code == 409


def test_moderacion_no_revela_quien_es_bot_y_juzga_en_el_servidor(client, reloj):
    codigo, tokens = preparar(client, 2)
    hasta(client, reloj, codigo, tokens, "reto")
    v = vista(client, codigo, tokens[0])
    comentarios = v["reto"]["config"]["comentarios"]
    assert comentarios and all(set(c) == {"autor", "texto", "creada"} for c in comentarios)
    avanzar(client, reloj, codigo, tokens, v["reto"]["inicio_en_ms"] / 1000.0 + 0.1)
    assert post(client, codigo, "moderar", token=tokens[0], indice=3, eliminar=True).status_code == 409      # fuera de orden
    a = post(client, codigo, "moderar", token=tokens[0], indice=0, eliminar=True, id="x")
    b = post(client, codigo, "moderar", token=tokens[0], indice=0, eliminar=True, id="x")                     # reintento de red
    assert a.status_code == 200 and b.status_code == 200 and b.json().get("repetido")
    assert vista(client, codigo, tokens[0])["reto"]["decididos"] == 1


def test_resultados_manipulados_y_antes_de_tiempo(client, reloj):
    codigo, tokens = preparar(client, 2)
    for objetivo in ("contencion", "plataformas"):
        while True:
            hasta(client, reloj, codigo, tokens, "reto")
            v = vista(client, codigo, tokens[0])
            if v["reto"]["clave"] == objetivo:
                break
            jugar_reto(client, reloj, codigo, tokens)
            hasta(client, reloj, codigo, tokens, "resultado")
            post(client, codigo, "continuar", token=tokens[0])
        cfg = v["reto"]["config"]
        avanzar(client, reloj, codigo, tokens, v["reto"]["inicio_en_ms"] / 1000.0 + 1)
        if objetivo == "contencion":
            completo = CW.toques_bot(cfg, 1.0, random.Random(1))
            assert post(client, codigo, "reto", token=tokens[0], datos=completo).status_code == 409        # aun no pasaron sus ticks
            malos = [{"toques": [[5, 0, 1, 1]], "fallos": 0}, {"toques": "x"}, {"toques": [], "fallos": -1}]
        else:
            carrera = PL.bot(cfg["nivel"], random.Random(1), 1.0)
            assert post(client, codigo, "reto", token=tokens[0], datos={"traza": carrera.traza}).status_code == 409   # mas larga que el tiempo real
            malos = [{"traza": [[9, 5]]}, {"traza": "x"}, {}]
        avanzar(client, reloj, codigo, tokens, v["reto"]["duracion_ms"] / 1000.0)
        for datos in malos:
            assert post(client, codigo, "reto", token=tokens[0], datos=datos).status_code == 409, datos
        bueno = CW.toques_bot(cfg, 0.9, random.Random(2)) if objetivo == "contencion" else {"traza": PL.bot(cfg["nivel"], random.Random(2), 0.9).traza}
        assert post(client, codigo, "reto", token=tokens[0], id="ok", datos=bueno).status_code == 200
        assert post(client, codigo, "reto", token=tokens[0], id="ok", datos=bueno).status_code == 200      # idempotente
        assert post(client, codigo, "reto", token=tokens[0], id="otra", datos=bueno).status_code == 409    # segunda entrega
        assert post(client, codigo, "reto", token=tokens[1], id="b", datos=bueno).status_code == 200
        hasta(client, reloj, codigo, tokens, "resultado")
        post(client, codigo, "continuar", token=tokens[0])


def test_desconexion_en_un_reto_y_bots_completan_la_sala(client, reloj):
    codigo, tokens = preparar(client, 1, bots=True)       # 1 humano + 3 automaticos
    hasta(client, reloj, codigo, tokens, "reto")
    jugar_reto(client, reloj, codigo, tokens)
    v = hasta(client, reloj, codigo, tokens, "reto_resultado")
    assert len(v["reto_resumen"]["resultados"]) == 4
    assert all(r["normalizado"] >= 0 for r in v["reto_resumen"]["resultados"].values())
    # Segunda ronda: el humano deja de responder en mitad del reto -> al vencer el margen recibe 0 y la sala sigue.
    hasta(client, reloj, codigo, tokens, "reto")
    sala = sala_de(client, codigo)
    reloj.t += 600
    sala.tick()
    assert sala.partida.fase == "reto_resultado"
    assert sala.retos[-1]["resultados"]["j1"]["normalizado"] == 0


def test_pista_del_rastreador_usa_el_tablero_actual(client, reloj):
    codigo, tokens = preparar(client, 2)
    while True:
        hasta(client, reloj, codigo, tokens, "reto")
        v = vista(client, codigo, tokens[0])
        if v["reto"]["clave"] == "rastreador":
            break
        jugar_reto(client, reloj, codigo, tokens)
        hasta(client, reloj, codigo, tokens, "resultado")
        post(client, codigo, "continuar", token=tokens[0])
    avanzar(client, reloj, codigo, tokens, v["reto"]["inicio_en_ms"] / 1000.0 + 0.5)
    p = sala_de(client, codigo).reto["estado"]
    pista = lambda slots: post(client, codigo, "rastrear", token=tokens[0], accion="pista", slots=slots).json()["pista"]
    pista(["", ""])
    primera = pista(["", ""])["carta"]                       # nivel 2: revela la cuenta del primer hueco
    puzzle = p["j1"]
    assert primera == puzzle.solucion[0]
    pista([primera, ""])
    segunda = pista([primera, ""])["carta"]                  # con la primera puesta, la pista apunta al siguiente hueco
    assert segunda == puzzle.solucion[1] != primera


def test_sala_clasica_sigue_existiendo(client, reloj):
    r = client.post("/api/arena/salas", json={"nombre": "A", "rol": "ciudadano", "duelo": False})
    codigo, token = r.json()["codigo"], r.json()["token"]
    assert post(client, codigo, "bots", token=token).status_code == 200
    assert post(client, codigo, "empezar", token=token).status_code == 200
    v = vista(client, codigo, token)
    assert v["fase"] == "ronda" and v["campana"] is False


def test_pantalla_de_espectadores(client, reloj):
    codigo, tokens = preparar(client, 2)
    hasta(client, reloj, codigo, tokens, "reto")
    p = client.get("/api/arena/salas/%s/publico" % codigo).json()
    assert p["fase"] == "reto" and p["reto"]["clave"] == "moderador"
    assert "config" not in p["reto"] and "arbol" not in p and "yo" not in p
    assert len(p["plan"]) == 5 and p["clasificacion"]
