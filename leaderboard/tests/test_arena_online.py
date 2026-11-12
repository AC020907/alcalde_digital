"""Arena Online por HTTPS: salas, roles, inicio, decisiones, tiempo, reconexion, seguridad y final."""
import pytest


def crear(client, rol="ciudadano", nombre="Ana", duelo=False):
    # Por defecto la Arena clasica; el Duelo de Frecuencias online tiene sus propias pruebas (test_arena_duelo_online.py).
    r = client.post("/api/arena/salas", json={"nombre": nombre, "rol": rol, "duelo": duelo})
    assert r.status_code == 200, r.text
    return r.json()


def unir(client, codigo, rol, nombre="X"):
    return client.post("/api/arena/salas/%s/unir" % codigo, json={"nombre": nombre, "rol": rol})


def vista(client, codigo, token, grafo=0):
    r = client.get("/api/arena/salas/%s" % codigo, params={"token": token, "grafo": grafo})
    assert r.status_code == 200, r.text
    return r.json()


def orden(client, codigo, nombre, token, **datos):
    return client.post("/api/arena/salas/%s/%s" % (codigo, nombre), json=dict(datos, token=token))


def sala_lista(client, n):
    roles = ["ciudadano", "periodista", "influencer", "candidato"][:n]
    host = crear(client, roles[0])
    codigo = host["codigo"]
    tokens = [host["token"]]
    for rol in roles[1:]:
        r = unir(client, codigo, rol)
        assert r.status_code == 200, r.text
        tokens.append(r.json()["token"])
        assert orden(client, codigo, "listo", tokens[-1], listo=True).status_code == 200
    assert orden(client, codigo, "empezar", tokens[0]).status_code == 200
    return codigo, tokens


def decidir_todos(client, codigo, tokens, ruta=(2,)):
    for t in tokens:
        v = vista(client, codigo, t)
        if v["fase"] == "ronda" and not v["ya_decidiste"]:
            r = orden(client, codigo, "accion", t, ronda=v["ronda"], ruta=list(ruta), id="m%s%s" % (t[:4], v["ronda"]))
            assert r.status_code == 200, r.text


@pytest.mark.parametrize("n", [2, 3, 4])
def test_partida_completa_2_3_4(client, n):
    codigo, tokens = sala_lista(client, n)
    arena = arena_online_de(client)
    sala = arena.sala(codigo)
    for _ in range(sala.partida.total_rondas):
        decidir_todos(client, codigo, tokens)
        assert vista(client, codigo, tokens[0])["fase"] in ("resultado", "final")
        orden(client, codigo, "continuar", tokens[0])
    finales = [vista(client, codigo, t)["final"] for t in tokens]
    assert all(f == finales[0] for f in finales)
    assert len(finales[0]["ranking"]) == n
    assert sum(finales[0]["votos"].values()) + finales[0]["abstencion"] == 16


def arena_online_de(client):
    return client.app.state.arena


def test_roles_unicos_sala_llena_y_codigo_inexistente(client):
    host = crear(client, "periodista")
    codigo = host["codigo"]
    assert unir(client, codigo, "periodista").status_code == 409
    for rol in ("ciudadano", "influencer", "candidato"):
        assert unir(client, codigo, rol).status_code == 200
    assert unir(client, codigo, "ciudadano").status_code == 409
    assert unir(client, "ZZZZZ", "ciudadano").status_code == 404
    assert unir(client, codigo, "hechicero").status_code == 400


def test_solo_el_anfitrion_empieza_y_con_listos(client):
    host = crear(client)
    codigo = host["codigo"]
    otro = unir(client, codigo, "periodista").json()["token"]
    assert orden(client, codigo, "empezar", otro).status_code == 403
    assert orden(client, codigo, "empezar", host["token"]).status_code == 409   # falta "listo"
    orden(client, codigo, "listo", otro, listo=True)
    assert orden(client, codigo, "empezar", host["token"]).status_code == 200
    assert unir(client, codigo, "influencer").status_code == 409                # ya empezo


def test_anfitrion_solo_completa_con_bots_y_juegan(client):
    host = crear(client)
    codigo = host["codigo"]
    assert orden(client, codigo, "empezar", host["token"]).status_code == 409
    assert orden(client, codigo, "bots", host["token"]).status_code == 200
    v = vista(client, codigo, host["token"])
    assert len(v["jugadores"]) == 4 and len(v["bots"]) == 3
    assert orden(client, codigo, "empezar", host["token"]).status_code == 200
    sala = arena_online_de(client).sala(codigo)
    sala.reloj = lambda: 10 ** 9      # el tiempo de los bots ya paso
    for b in sala.bots.values():
        b[1] = 0
    decidir_todos(client, codigo, [host["token"]])
    assert vista(client, codigo, host["token"])["fase"] == "resultado"


def test_token_falso_y_puntos_del_cliente_ignorados(client):
    codigo, tokens = sala_lista(client, 2)
    assert client.get("/api/arena/salas/%s" % codigo, params={"token": "x" * 20}).status_code == 403
    v = vista(client, codigo, tokens[0])
    r = client.post("/api/arena/salas/%s/accion" % codigo,
                    json={"token": tokens[0], "ronda": v["ronda"], "ruta": [0], "puntos": 9999})
    assert r.status_code == 200
    decidir_todos(client, codigo, tokens[1:])
    res = vista(client, codigo, tokens[0])["resultado"]
    assert all(abs(a["puntos"]) < 100 for a in res["acciones"])


def test_accion_repetida_invalida_o_de_otra_ronda(client):
    codigo, tokens = sala_lista(client, 2)
    v = vista(client, codigo, tokens[0])
    assert orden(client, codigo, "accion", tokens[0], ronda=v["ronda"] + 1, ruta=[0]).status_code == 409
    assert orden(client, codigo, "accion", tokens[0], ronda=v["ronda"], ruta=[1]).status_code == 409   # nodo interno
    assert orden(client, codigo, "accion", tokens[0], ronda=v["ronda"], ruta=[0], id="a1").status_code == 200
    assert orden(client, codigo, "accion", tokens[0], ronda=v["ronda"], ruta=[0], id="a1").status_code == 200  # idempotente
    assert orden(client, codigo, "accion", tokens[0], ronda=v["ronda"], ruta=[2], id="a2").status_code == 409  # ya decidio
    assert client.post("/api/arena/salas/%s/accion" % codigo,
                       json={"token": tokens[0], "ronda": "1", "ruta": ["x"]}).status_code == 422


def test_tiempo_agotado_y_desconexion(client):
    codigo, tokens = sala_lista(client, 2)
    sala = arena_online_de(client).sala(codigo)
    base = sala.reloj()
    sala.reloj = lambda: base + 1000            # nadie decidio y pasaron 1000 s
    res = vista(client, codigo, tokens[0])
    assert res["fase"] in ("resultado", "ronda", "final")
    assert any(a["accion"] == "sin_respuesta" for a in sala.partida.ultimo_resultado["acciones"])
    # el jugador 2 no consulta en mucho tiempo: aparece desconectado; con su token vuelve.
    jugadores = {j["id"]: j for j in vista(client, codigo, tokens[0])["jugadores"]}
    assert not jugadores["j2"]["conectado"]
    jugadores = {j["id"]: j for j in vista(client, codigo, tokens[1])["jugadores"]}
    assert jugadores["j2"]["conectado"]


def test_pausa_congela_el_tiempo(client):
    codigo, tokens = sala_lista(client, 2)
    sala = arena_online_de(client).sala(codigo)
    t = [sala.reloj()]
    sala.reloj = lambda: t[0]
    assert orden(client, codigo, "pausa", tokens[1], pausar=True).status_code == 403
    assert orden(client, codigo, "pausa", tokens[0], pausar=True).status_code == 200
    antes = vista(client, codigo, tokens[0])["restante"]
    t[0] += 500
    assert vista(client, codigo, tokens[0])["restante"] == antes
    assert vista(client, codigo, tokens[0])["fase"] == "ronda"


def test_grafo_solo_si_se_pide_y_pagina_servida(client):
    host = crear(client)
    assert "grafo" not in vista(client, host["codigo"], host["token"])
    assert vista(client, host["codigo"], host["token"], grafo=1)["grafo"]["nodos"]
    r = client.get("/arena")
    assert r.status_code == 200 and "Arena Civitas" in r.text
