"""
Arena Civitas: reglas del modo multijugador (2 a 4 jugadores) en Python puro.

El servidor es el unico que ejecuta estas reglas (autoritativo); los clientes solo envian la ruta que
eligieron en su arbol de decisiones. Todo el azar sale de random.Random(semilla): misma semilla, misma
partida, lo que permite pruebas reproducibles y que dos partidas distintas sean distintas.

Estructuras de datos (rubrica §5-7):
- Arbol de decisiones (ArbolDecisiones) por jugador y ronda: Compartir / Verificar -> ¿Es verdadera? ->
  (Si: compartir con fuente | No: reportar) / Ignorar / Reportar. Los roles insertan o eliminan ramas.
- Grafo social dirigido y ponderado (GrafoSocial): ciudadanos, candidatos y jugadores. La publicacion se
  propaga con BFS multifuente desde el autor y desde quienes la comparten; los reportes bloquean nodos.
- Grafo de la ciudad (no dirigido): COLEGIO-BARRIO-PARQUE/PLAZA-ALCALDIA. La zona de la publicacion
  decide por donde empieza el boca a boca y como se reparten los conflictos entre zonas vecinas.
"""
import copy
import random

from clases.GrafoSocial import GrafoSocial
from clases.Tree import ArbolDecisiones

ROLES = ("ciudadano", "periodista", "influencer", "candidato")
NOMBRE_ROL = {"ciudadano": "Ciudadano", "periodista": "Periodista", "influencer": "Influencer",
              "candidato": "Candidato a alcalde"}
DESCRIPCION_ROL = {
    "ciudadano": "Alerta vecinal: cuando reporta, protege a toda su zona. Gana participación por actuar.",
    "periodista": "Investiga: al verificar ve la fuente real. Su desmentido protege a quienes la siguen.",
    "influencer": "Alcance masivo: lo que comparte llega el doble de lejos. Sus aciertos y errores pesan x2.",
    "candidato": "Si un rumor es sobre su candidatura puede responder con datos; no puede reportar críticas propias.",
}
MIN_JUGADORES, MAX_JUGADORES = 2, 4

CANDIDATOS = (("vega", "Tomás Vega"), ("ortega", "Juan Ortega"), ("prado", "Inés Prado"), ("ruiz", "Elena Ruiz"))
NOMBRE_CANDIDATO = dict(CANDIDATOS)

INDICADORES = ("info_verificada", "confianza", "convivencia", "bienestar", "participacion",
               "desinformacion", "conflictos", "rumores")
NEGATIVOS = ("desinformacion", "conflictos", "rumores")
NOMBRE_INDICADOR = {"info_verificada": "Información verificada", "confianza": "Confianza ciudadana",
                    "convivencia": "Convivencia", "bienestar": "Bienestar digital",
                    "participacion": "Participación responsable", "desinformacion": "Desinformación",
                    "conflictos": "Conflictos", "rumores": "Rumores en circulación"}
INICIALES = {"info_verificada": 45, "confianza": 50, "convivencia": 55, "bienestar": 55, "participacion": 40,
             "desinformacion": 30, "conflictos": 20, "rumores": 20}

# ---------- Grafo de la ciudad (PDF p. 5) ----------
ZONAS = ("colegio", "barrio", "parque", "plaza", "alcaldia")
NOMBRE_ZONA = {"colegio": "Colegio", "barrio": "Barrio", "parque": "Parque", "plaza": "Plaza", "alcaldia": "Alcaldía"}
CALLES = (("colegio", "barrio"), ("barrio", "parque"), ("barrio", "plaza"), ("plaza", "alcaldia"))

# ---------- Grafo social (PDF p. 5): nombre, zona ----------
CIUDADANOS = (("ana", "Ana", "barrio"), ("luis", "Luis", "colegio"), ("pedro", "Pedro", "plaza"),
              ("carlos", "Carlos", "parque"), ("maria", "María", "plaza"), ("sofia", "Sofía", "colegio"),
              ("diego", "Diego", "barrio"), ("valentina", "Valentina", "parque"), ("andres", "Andrés", "alcaldia"),
              ("camila", "Camila", "colegio"), ("jorge", "Jorge", "alcaldia"), ("paula", "Paula", "barrio"),
              ("mateo", "Mateo", "plaza"), ("laura", "Laura", "parque"), ("daniel", "Daniel", "alcaldia"),
              ("isabel", "Isabel", "barrio"))
# Quien sigue a quien (origen -> destino: lo que publica origen le llega a destino), con fuerza.
SEGUIMIENTOS = (("ana", "luis", .7), ("ana", "pedro", .7), ("luis", "carlos", .6), ("pedro", "maria", .6),
                ("carlos", "maria", .6), ("maria", "carlos", .6), ("ana", "diego", .5), ("diego", "paula", .6),
                ("paula", "isabel", .6), ("isabel", "ana", .5), ("luis", "sofia", .6), ("sofia", "camila", .7),
                ("camila", "luis", .5), ("pedro", "mateo", .6), ("mateo", "jorge", .5), ("jorge", "andres", .6),
                ("andres", "daniel", .6), ("daniel", "maria", .4), ("carlos", "valentina", .6),
                ("valentina", "laura", .7), ("laura", "carlos", .5), ("mateo", "valentina", .4),
                ("diego", "sofia", .4), ("andres", "mateo", .4), ("isabel", "laura", .4), ("camila", "paula", .4))
AUDIENCIA_CANDIDATO = {"vega": ("andres", "jorge", "daniel", "maria"), "ortega": ("luis", "sofia", "camila", "ana"),
                       "prado": ("pedro", "mateo", "valentina", "diego"), "ruiz": ("carlos", "laura", "paula", "isabel")}

# ---------- Publicaciones (PDF p. 2: verdaderas, opiniones y falsas) ----------
# tipo: verdadera | falsa | opinion. candidato + sentido ("ataque"/"apoyo") si habla de una candidatura.
PUBLICACIONES = (
    {"id": "colegio", "texto": "El candidato Juan quiere cerrar el colegio.", "tipo": "falsa", "autor": "@verdad.oculta",
     "zona": "colegio", "candidato": "ortega", "sentido": "ataque",
     "fuente": "No hay ninguna propuesta de Juan Ortega sobre el colegio; la imagen es un montaje de otro país.",
     "pista": "La foto no tiene fecha y la cuenta se creó ayer."},
    {"id": "robo", "texto": "El alcalde actual está robando dinero.", "tipo": "falsa", "autor": "@ciudadano_furioso",
     "zona": "alcaldia", "candidato": "vega", "sentido": "ataque",
     "fuente": "La Contraloría publicó las cuentas: no hay ningún hallazgo. El audio citado es sintético.",
     "pista": "No enlaza ningún documento; solo dice 'me lo contaron'."},
    {"id": "parques", "texto": "Mañana cerrarán todos los parques.", "tipo": "falsa", "autor": "@alerta_nova",
     "zona": "parque", "candidato": None, "sentido": None,
     "fuente": "La Secretaría de Ambiente solo cierra el Parque Norte un día por mantenimiento.",
     "pista": "Mezcla un dato real (un cierre) con una exageración (todos)."},
    {"id": "agua", "texto": "Envenenaron el agua del barrio: no la tomen.", "tipo": "falsa", "autor": "@verdad.oculta",
     "zona": "barrio", "candidato": None, "sentido": None,
     "fuente": "El acueducto publicó la muestra 14: el agua es potable. El rumor nació de una tubería rota.",
     "pista": "Usa mayúsculas y pide compartir 'antes de que lo borren'."},
    {"id": "prado_robo", "texto": "Inés Prado tiene una casa pagada con dinero público.", "tipo": "falsa",
     "autor": "@nova_libre", "zona": "plaza", "candidato": "prado", "sentido": "ataque",
     "fuente": "La escritura de la casa es de 2009, antes de que Inés Prado entrara a la política.",
     "pista": "La captura no muestra el enlace original."},
    {"id": "horario", "texto": "La Registraduría amplía el horario de votación hasta las 6 p.m.", "tipo": "verdadera",
     "autor": "@registraduria", "zona": "alcaldia", "candidato": None, "sentido": None,
     "fuente": "Resolución publicada en la web oficial de la Registraduría, con número y fecha.",
     "pista": "Enlaza la resolución oficial."},
    {"id": "transporte", "texto": "Inés Prado presenta su plan de transporte con cifras y presupuesto.",
     "tipo": "verdadera", "autor": "@ines.prado", "zona": "plaza", "candidato": "prado", "sentido": "apoyo",
     "fuente": "El documento completo está publicado y lo revisó un centro de estudios independiente.",
     "pista": "Trae el documento completo, no una frase suelta."},
    {"id": "debate", "texto": "El debate de candidatos será el jueves en la plaza y se transmite en vivo.",
     "tipo": "verdadera", "autor": "@noticias_nova", "zona": "plaza", "candidato": None, "sentido": None,
     "fuente": "Confirmado por las cuatro campañas y por el canal que lo transmite.", "pista": "Varias fuentes lo confirman."},
    {"id": "ortega_becas", "texto": "Juan Ortega propone 300 becas para el colegio público.", "tipo": "verdadera",
     "autor": "@juan.ortega", "zona": "colegio", "candidato": "ortega", "sentido": "apoyo",
     "fuente": "Está en su programa registrado, página 12, con la fuente de financiación.",
     "pista": "Cita el programa registrado."},
    {"id": "ruiz_opinion", "texto": "Elena Ruiz habla bonito, pero no me convence.", "tipo": "opinion",
     "autor": "@vecino_critico", "zona": "barrio", "candidato": "ruiz", "sentido": "ataque",
     "fuente": "Es una opinión personal: no afirma ningún hecho que se pueda comprobar.", "pista": "Habla de gustos, no de datos."},
    {"id": "vega_opinion", "texto": "Para mí, Tomás Vega es el que más ha trabajado por el parque.", "tipo": "opinion",
     "autor": "@vecina_parque", "zona": "parque", "candidato": "vega", "sentido": "apoyo",
     "fuente": "Es una opinión: valora, pero no inventa datos.", "pista": "Empieza con 'para mí'."},
    {"id": "discusion", "texto": "Los del barrio siempre votan por los peores. ¡Que se vayan!", "tipo": "opinion",
     "autor": "@troll_nova", "zona": "barrio", "candidato": None, "sentido": None,
     "fuente": "Es un ataque a un grupo de vecinos, no una información.", "pista": "Insulta a un grupo entero."},
)
POR_ID = {p["id"]: p for p in PUBLICACIONES}

# ---------- Eventos aleatorios (PDF pp. 6-7) ----------
EVENTOS = {
    "noticia_falsa": {"titulo": "Aparece una noticia falsa", "tipos": ("falsa",)},
    "viral": {"titulo": "Una publicación se vuelve viral", "tipos": ("falsa", "verdadera"), "factor": 1.6, "tiempo": 0.6},
    "rumor_candidato": {"titulo": "Aparece un rumor sobre un candidato", "tipos": ("falsa",), "con_candidato": True},
    "discusion": {"titulo": "Se produce una discusión entre ciudadanos", "tipos": ("opinion",), "conflictos": 4},
    "noticia_verdadera": {"titulo": "Se publica una noticia verdadera", "tipos": ("verdadera",)},
    "campana_convivencia": {"titulo": "Aparece una campaña de convivencia digital", "tipos": ("verdadera", "opinion"),
                            "convivencia": 5, "bienestar": 3},
    "reporte_ciudadano": {"titulo": "Un ciudadano reporta contenido", "tipos": ("falsa", "opinion"), "protegidos": 2},
}

# ---------- Arbol de decisiones (PDF p. 4) ----------
COMPARTIR, VERIFICADA, IGNORAR, REPORTAR, REPORTAR_FALSA, RESPONDER, SIN_RESPUESTA = (
    "compartir", "compartir_verificada", "ignorar", "reportar", "reportar_falsa", "responder", "sin_respuesta")
TEXTO_ACCION = {COMPARTIR: "compartió sin verificar", VERIFICADA: "verificó y compartió con la fuente",
                IGNORAR: "la ignoró", REPORTAR: "la reportó", REPORTAR_FALSA: "la verificó y la reportó como falsa",
                RESPONDER: "respondió con datos", SIN_RESPUESTA: "no alcanzó a decidir"}


def arbol_base():
    """El arbol del PDF, igual para todos; luego cada rol inserta o elimina ramas."""
    arbol = ArbolDecisiones()
    raiz = arbol.insertar_raiz("¿Qué quieres hacer?")
    arbol.insertar_hijo(raiz, "Compartir", COMPARTIR, "compartir")
    verificar = arbol.insertar_hijo(raiz, "¿Es verdadera?", None, "verificar")
    arbol.insertar_hijo(verificar, "Sí: compartir con la fuente", VERIFICADA, "si")
    arbol.insertar_hijo(verificar, "No: reportarla", REPORTAR_FALSA, "no")
    arbol.insertar_hijo(raiz, "Ignorar", IGNORAR, "ignorar")
    arbol.insertar_hijo(raiz, "Reportar", REPORTAR, "reportar")
    return arbol


def arbol_para(rol, pub, candidato_propio):
    """Arbol de una ronda para un jugador: las reglas del rol modifican el arbol base."""
    arbol = arbol_base()
    verificar = arbol.buscar("verificar")
    if rol == "periodista":
        verificar.texto = "Tu investigación: %s ¿Es verdadera?" % pub["fuente"]
    else:
        verificar.texto = "Lo que encuentras: %s ¿Es verdadera?" % pub["pista"]
    if rol == "candidato" and pub.get("candidato") == candidato_propio:
        # Conflicto de interes: no puede reportar lo que se dice de su campana; si puede responder con datos.
        arbol.eliminar(arbol.buscar("reportar"))
        arbol.insertar_hijo(arbol.raiz, "Responder con datos", RESPONDER, "responder")
    return arbol


def arbol_a_dict(nodo):
    return {"texto": nodo.texto, "etiqueta": nodo.etiqueta, "hijos": [arbol_a_dict(h) for h in nodo.hijos]}


def construir_grafo_social():
    g = GrafoSocial()
    for nodo, nombre, zona in CIUDADANOS:
        g.agregar_usuario(nodo, nombre, "ciudadano", 1, {"zona": zona})
    for origen, destino, peso in SEGUIMIENTOS:
        g.agregar_conexion(origen, destino, peso)
    for cid, nombre in CANDIDATOS:
        g.agregar_usuario("@" + cid, nombre, "candidato", 4)
        for seguidor in AUDIENCIA_CANDIDATO[cid]:
            g.agregar_conexion("@" + cid, seguidor, 0.6)
    for pub in PUBLICACIONES:
        if not g.existe(pub["autor"]):
            g.agregar_usuario(pub["autor"], pub["autor"], "fuente", 2)
    return g


def construir_grafo_ciudad():
    g = GrafoSocial()
    for z in ZONAS:
        g.agregar_usuario(z, NOMBRE_ZONA[z], "zona")
    for a, b in CALLES:
        g.agregar_conexion(a, b, 1.0)
        g.agregar_conexion(b, a, 1.0)
    return g


def distancias_zona(grafo_ciudad, zona):
    """BFS sobre el grafo de la ciudad: a cuantas calles queda cada zona."""
    return {z: d for d, nivel in enumerate(grafo_ciudad.bfs_propagacion(zona)) for z in nivel}


class Jugador:
    def __init__(self, jid, nombre, rol, candidato=None):
        self.id, self.nombre, self.rol, self.candidato = jid, nombre, rol, candidato
        self.puntos = 0
        self.reputacion = 50
        self.logros = []
        self.aciertos = 0
        self.historial = []      # [(ronda, accion, delta_puntos)]
        self.conectado = True

    def publico(self):
        return {"id": self.id, "nombre": self.nombre, "rol": self.rol, "rol_nombre": NOMBRE_ROL[self.rol],
                "candidato": self.candidato, "puntos": self.puntos, "reputacion": self.reputacion,
                "logros": list(self.logros), "conectado": self.conectado}


class Partida:
    """Estado y reglas de una partida de Arena. No sabe nada de sockets ni de pantallas."""

    def __init__(self, semilla=0, rondas=5, segundos=25):
        self.semilla = semilla
        self.rng = random.Random("arena|%s" % semilla)
        self.total_rondas = rondas
        self.segundos = segundos
        self.jugadores = {}            # id -> Jugador (orden de llegada)
        self.fase = "lobby"            # lobby -> ronda -> resultado -> ... -> final
        self.ronda = 0
        self.indicadores = dict(INICIALES)
        self.grafo = construir_grafo_social()
        self.ciudad = construir_grafo_ciudad()
        # Confianza de cada ciudadano en cada candidato: azar moderado, distinto en cada partida.
        self.confianza_cand = {n: {c: 50 + self.rng.randint(-6, 6) for c, _ in CANDIDATOS} for n, _, _ in CIUDADANOS}
        self.causas = {c: [] for c, _ in CANDIDATOS}   # explicacion causal de la eleccion
        self.publicacion = None
        self.evento = None
        self.arboles = {}
        self.acciones = {}             # jid -> (ruta, accion)
        self.ultimo_resultado = None
        self.usadas = []
        self.desmentidas = set()
        self.eleccion = None
        self.con_torneo = False         # el torneo de minijuegos va entre el Consejo y la eleccion

    # ----- lobby -----
    def unir(self, jid, nombre, rol):
        if self.fase != "lobby":
            return "La partida ya empezó."
        if rol not in ROLES:
            return "Rol desconocido."
        if len(self.jugadores) >= MAX_JUGADORES:
            return "La sala está llena (máximo 4)."
        if any(j.rol == rol for j in self.jugadores.values()):
            return "Ese rol ya está ocupado."
        nombre = (str(nombre).strip() or NOMBRE_ROL[rol])[:20]
        candidato = None
        if rol == "candidato":
            candidato = "prado"
        self.jugadores[jid] = Jugador(jid, nombre, rol, candidato)
        self._conectar_jugador(self.jugadores[jid])
        return None

    def _conectar_jugador(self, j):
        """La cuenta del jugador entra al grafo social con el alcance de su rol."""
        nodo = "j:" + j.id
        self.grafo.agregar_usuario(nodo, j.nombre, "jugador", 6 if j.rol == "influencer" else 2, {"rol": j.rol})
        if j.rol == "influencer":
            seguidores = [n for n, _, _ in CIUDADANOS][::2]
            peso = .75
        elif j.rol == "periodista":
            seguidores = ("ana", "pedro", "sofia", "jorge", "laura")
            peso = .65
        elif j.rol == "candidato":
            seguidores = AUDIENCIA_CANDIDATO[j.candidato]
            peso = .6
        else:
            seguidores = ("diego", "paula", "isabel")
            peso = .6
        for s in seguidores:
            self.grafo.agregar_conexion(nodo, s, peso)

    def quitar(self, jid):
        if jid in self.jugadores and self.fase == "lobby":
            del self.jugadores[jid]
            self.grafo.eliminar_usuario("j:" + jid)

    def puede_empezar(self):
        return self.fase == "lobby" and MIN_JUGADORES <= len(self.jugadores) <= MAX_JUGADORES

    # ----- rondas -----
    def nueva_ronda(self, evento=None):
        """evento: clave de EVENTOS para ligar la ronda a la historia (campana online); None = al azar con la semilla."""
        self.ronda += 1
        self.fase = "ronda"
        azar = self.rng.choice(sorted(EVENTOS))          # se consume siempre: la semilla da la misma secuencia
        clave = evento if evento in EVENTOS else azar
        evento = EVENTOS[clave]
        candidatas = [p for p in PUBLICACIONES if p["tipo"] in evento["tipos"] and p["id"] not in self.usadas
                      and (not evento.get("con_candidato") or p["candidato"])]
        if not candidatas:
            candidatas = [p for p in PUBLICACIONES if p["tipo"] in evento["tipos"]] or list(PUBLICACIONES)
        self.publicacion = self.rng.choice(candidatas)
        self.usadas.append(self.publicacion["id"])
        self.evento = dict(evento, clave=clave)
        self.acciones = {}
        self.arboles = {jid: arbol_para(j.rol, self.publicacion, j.candidato) for jid, j in self.jugadores.items()}
        return self.vista_ronda_publica()

    def tiempo_ronda(self):
        return max(8, int(round(self.segundos * self.evento.get("tiempo", 1.0))))

    def registrar_accion(self, jid, ruta):
        """Valida la ruta contra el arbol de ESE jugador. Solo cuenta la primera accion de la ronda."""
        if self.fase != "ronda":
            return "No hay una ronda abierta."
        if jid not in self.jugadores:
            return "Jugador desconocido."
        if jid in self.acciones:
            return "Ya decidiste en esta ronda."
        if not isinstance(ruta, list) or len(ruta) > 4:
            return "Ruta inválida."
        nodos = self.arboles[jid].recorrer_ruta(ruta)
        if nodos is None or not nodos[-1].es_hoja():
            return "Ruta inválida."
        self.acciones[jid] = (list(ruta), nodos[-1].consecuencia)
        return None

    def todos_decidieron(self):
        return all(jid in self.acciones or not j.conectado for jid, j in self.jugadores.items())

    def resolver_ronda(self):
        pub, evento = self.publicacion, self.evento
        rng = random.Random("ronda|%s|%s" % (self.semilla, self.ronda))
        acciones = {jid: self.acciones.get(jid, (None, SIN_RESPUESTA))[1] for jid in self.jugadores}
        antes = dict(self.indicadores)

        # --- quien comparte y quien frena (arbol -> grafo) ---
        fuentes, factores, bloqueados = [pub["autor"]], {pub["autor"]: 1.0}, set()
        # Boca a boca en la zona de la publicacion: el grafo de la ciudad dice donde empieza.
        dist = distancias_zona(self.ciudad, pub["zona"])
        reportes = 0
        for jid, accion in sorted(acciones.items()):
            j = self.jugadores[jid]
            nodo = "j:" + jid
            fuerza = 2.0 if j.rol == "influencer" else (1.3 if j.rol == "candidato" else 1.0)
            if accion in (COMPARTIR, VERIFICADA):
                fuentes.append(nodo)
                factores[nodo] = fuerza
            elif accion in (REPORTAR, REPORTAR_FALSA):
                reportes += 1
                bloqueados.update(self.grafo.vecinos(nodo))
                if j.rol == "ciudadano":
                    bloqueados.update(n for n, _, z in CIUDADANOS if z == self._zona_jugador(j))
                if j.rol == "periodista" and accion == REPORTAR_FALSA:
                    for nivel in self.grafo.bfs_propagacion(nodo)[1:3]:
                        bloqueados.update(nivel)
            elif accion == RESPONDER:
                bloqueados.update(self.grafo.vecinos(nodo))
        for _ in range(evento.get("protegidos", 0)):
            bloqueados.add(rng.choice([n for n, _, _ in CIUDADANOS]))
        if reportes >= 2:
            factores[pub["autor"]] = 0.3   # Civitas retira la publicacion: el autor apenas llega a alguien
        for n, _, z in CIUDADANOS:
            if dist.get(z) == 0 and n not in bloqueados:
                fuentes.append(n)
                factores[n] = 0.5
        bloqueados -= set(fuentes)
        padres = {}
        niveles = self.grafo.bfs_multifuente(fuentes, semilla="%s|%s" % (self.semilla, self.ronda),
                                             factor=evento.get("factor", 1.0), bloqueados=bloqueados,
                                             padres=padres, factores=factores)
        ciudadanos = {n for n, _, _ in CIUDADANOS}
        alcanzados = [n for nivel in niveles for n in nivel if n in ciudadanos]
        n_alc = len(alcanzados)
        protegidos = sorted(bloqueados & ciudadanos)

        # --- consecuencias en la ciudad ---
        d = {k: 0 for k in INDICADORES}
        verificada = any(a in (VERIFICADA, REPORTAR_FALSA) for a in acciones.values())
        # Un rumor queda desmentido si alguien lo verifico y lo reporto, si el candidato respondio con datos
        # o si lo reportaron al menos dos jugadores.
        desmentida = pub["tipo"] == "falsa" and (
            reportes >= 2 or REPORTAR_FALSA in acciones.values() or RESPONDER in acciones.values())
        tipo = pub["tipo"]
        if tipo == "falsa":
            peso = 0.4 if desmentida else 1.0
            d["desinformacion"] += round(n_alc * 1.2 * peso)
            d["rumores"] += round(n_alc * 0.6 * peso)
            d["confianza"] -= round(n_alc * 0.5 * peso)
            d["conflictos"] += round(n_alc * (0.5 if pub["sentido"] == "ataque" else 0.3) * peso)
            if desmentida:
                d["info_verificada"] += 6
                self.desmentidas.add(pub["id"])
        elif tipo == "verdadera":
            refuerzo = 1.3 if verificada else 1.0
            d["info_verificada"] += round(n_alc * 0.8 * refuerzo)
            d["participacion"] += round(n_alc * 0.4)
            d["confianza"] += round(n_alc * 0.3 * refuerzo)
        else:
            con_contexto = VERIFICADA in acciones.values()
            d["conflictos"] += round(n_alc * (0.15 if con_contexto else 0.35)) + evento.get("conflictos", 0)
            d["convivencia"] -= round(n_alc * (0.1 if con_contexto else 0.3))
            d["convivencia"] -= 3 * reportes      # reportar opiniones es censura: tambien pesa
        d["convivencia"] += evento.get("convivencia", 0) - (d["conflictos"] // 3)
        d["bienestar"] += evento.get("bienestar", 0) - (d["conflictos"] + d["desinformacion"]) // 6
        for jid, accion in acciones.items():
            d["participacion"] += -2 if accion == SIN_RESPUESTA else (2 if self.jugadores[jid].rol == "ciudadano" else 1)
        for k, v in d.items():
            self.indicadores[k] = max(0, min(100, self.indicadores[k] + v))

        # --- confianza en candidatos (lo que decide la eleccion) ---
        cand = pub.get("candidato")
        if cand:
            if tipo == "falsa" and pub["sentido"] == "ataque":
                delta = 3 if desmentida else -6
                motivo = ("Rumor falso desmentido a tiempo" if desmentida else "Rumor falso sin desmentir")
            elif tipo == "verdadera" and pub["sentido"] == "apoyo":
                delta, motivo = 4, "Propuesta verificada que llegó a la gente"
            elif tipo == "opinion" and pub["sentido"] == "apoyo":
                delta, motivo = 1, "Opiniones a favor"
            elif tipo == "opinion" and pub["sentido"] == "ataque":
                delta, motivo = -1, "Opiniones en contra"
            else:
                delta, motivo = 0, ""
            for n in alcanzados:
                self.confianza_cand[n][cand] = max(0, min(100, self.confianza_cand[n][cand] + delta))
            if alcanzados and delta:
                self.causas[cand].append((self.ronda, delta * len(alcanzados), "%s (%s, %d ciudadanos)" % (
                    motivo, pub["texto"], len(alcanzados))))
        for jid, accion in acciones.items():
            j = self.jugadores[jid]
            if j.rol == "candidato" and accion == RESPONDER:
                for n in self.grafo.vecinos("j:" + jid):
                    if n in self.confianza_cand:
                        self.confianza_cand[n][j.candidato] += 3
                self.causas[j.candidato].append((self.ronda, 3 * len(self.grafo.vecinos("j:" + jid)),
                                                 "Su candidatura respondió con datos"))

        # --- puntuacion individual ---
        detalle = []
        for jid in sorted(acciones):
            j, accion = self.jugadores[jid], acciones[jid]
            puntos, rep, nota = self._valorar(j, accion, tipo, pub)
            j.puntos += puntos
            j.reputacion = max(0, min(100, j.reputacion + rep))
            j.historial.append((self.ronda, accion, puntos))
            if puntos > 0:
                j.aciertos += 1
            nuevos = self._logros(j, accion, tipo, len(protegidos))
            detalle.append({"jugador": jid, "nombre": j.nombre, "rol": j.rol, "accion": accion,
                            "texto_accion": TEXTO_ACCION[accion], "puntos": puntos, "reputacion": rep,
                            "nota": nota, "logros_nuevos": nuevos})

        self.fase = "resultado"
        self.ultimo_resultado = {
            "ronda": self.ronda, "publicacion": self._pub_publica(revelar=True), "evento": evento["titulo"],
            "acciones": detalle, "alcanzados": alcanzados, "niveles": niveles, "padres": padres,
            "protegidos": protegidos, "n_alcanzados": n_alc, "saltos": max(0, len(niveles) - 1),
            "velocidad": round(n_alc / max(1, len(niveles) - 1), 1), "desmentida": bool(desmentida),
            "retirada": reportes >= 2, "delta_indicadores": {k: self.indicadores[k] - antes[k] for k in INDICADORES},
            "indicadores": dict(self.indicadores),
        }
        return self.ultimo_resultado

    def _zona_jugador(self, j):
        vecinos = [n for n in self.grafo.vecinos("j:" + j.id) if n in self.confianza_cand]
        zonas = {z for n, _, z in CIUDADANOS if n in vecinos}
        return sorted(zonas)[0] if zonas else "barrio"

    def _valorar(self, j, accion, tipo, pub):
        """Puntos y reputacion por accion. Responsable suma, irresponsable resta; el rol cambia el peso."""
        tabla = {
            "falsa": {COMPARTIR: (-10, -8, "Difundiste un rumor falso."), VERIFICADA: (-12, -10, "La verificaste y aun así la compartiste."),
                      IGNORAR: (2, 0, "No la difundiste."), REPORTAR: (6, 3, "Frenaste un rumor falso."),
                      REPORTAR_FALSA: (10, 6, "Verificaste y frenaste un rumor falso."),
                      RESPONDER: (9, 6, "Respondiste a un rumor con datos.")},
            "verdadera": {COMPARTIR: (4, 1, "Era cierta, pero la compartiste sin comprobar."),
                          VERIFICADA: (10, 6, "Verificaste y difundiste información útil."),
                          IGNORAR: (0, 0, "Era útil y no la difundiste."), REPORTAR: (-6, -4, "Reportaste información verdadera."),
                          REPORTAR_FALSA: (-8, -5, "La verificaste mal: era verdadera."),
                          RESPONDER: (6, 3, "Ampliaste una propuesta con datos.")},
            "opinion": {COMPARTIR: (-2, -1, "Difundiste una opinión como si fuera un hecho."),
                        VERIFICADA: (5, 3, "La compartiste aclarando que es una opinión."),
                        IGNORAR: (4, 1, "No avivaste una discusión."), REPORTAR: (-3, -2, "Reportar opiniones también daña la convivencia."),
                        REPORTAR_FALSA: (-3, -2, "Una opinión no es falsa ni verdadera: es una opinión."),
                        RESPONDER: (5, 3, "Respondiste a una crítica con propuestas.")},
        }
        if accion == SIN_RESPUESTA:
            return -3, -1, "Se acabó el tiempo: tu silencio también cuenta."
        puntos, rep, nota = tabla[tipo][accion]
        if j.rol == "influencer":
            puntos *= 2
        if j.rol == "periodista" and accion in (VERIFICADA, REPORTAR_FALSA) and puntos > 0:
            puntos += 4
        if j.rol == "ciudadano" and accion != IGNORAR and puntos > 0:
            puntos += 2
        if j.rol == "candidato" and accion == RESPONDER:
            puntos += 3
        return puntos, rep, nota

    def _logros(self, j, accion, tipo, protegidos):
        nuevos = []
        def dar(nombre):
            if nombre not in j.logros:
                j.logros.append(nombre)
                nuevos.append(nombre)
        if sum(1 for _, a, p in j.historial if a in (VERIFICADA, REPORTAR_FALSA) and p > 0) >= 2:
            dar("Verificador/a")
        if accion in (REPORTAR, REPORTAR_FALSA) and tipo == "falsa" and protegidos >= 5:
            dar("Cortafuegos")
        if j.rol == "influencer" and sum(1 for _, a, p in j.historial if a == VERIFICADA and p > 0) >= 1:
            dar("Voz de confianza")
        if accion == RESPONDER:
            dar("Debate limpio")
        if len(j.historial) >= 3 and all(a != SIN_RESPUESTA for _, a, _ in j.historial):
            dar("Siempre presente")
        return nuevos

    def consejo_terminado(self):
        return self.ronda >= self.total_rondas

    def cerrar_resultado(self):
        if self.consejo_terminado() and not self.con_torneo:
            return self.elegir_alcalde()
        return None

    # ----- eleccion final (PDF p. 9) -----
    def elegir_alcalde(self):
        rng = random.Random("eleccion|%s" % self.semilla)
        ind = self.indicadores
        votos = {c: 0 for c, _ in CANDIDATOS}
        abstencion = 0
        prob_voto = 0.35 + 0.6 * ind["participacion"] / 100.0
        bono_jugador = {}
        for j in self.jugadores.values():
            if j.rol == "candidato":
                bono_jugador[j.candidato] = (j.reputacion - 50) / 5.0
        for n, _, _ in CIUDADANOS:
            if rng.random() > prob_voto:
                abstencion += 1
                continue
            prefer = {c: v + bono_jugador.get(c, 0) + rng.uniform(-2, 2) for c, v in self.confianza_cand[n].items()}
            votos[max(sorted(prefer), key=lambda c: prefer[c])] += 1
        ganador = max(sorted(votos), key=lambda c: (votos[c], -sorted(votos).index(c)))
        explicacion = []
        for ronda, peso, motivo in sorted(self.causas[ganador], key=lambda x: -abs(x[1]))[:2]:
            explicacion.append("A favor de %s, ronda %d: %s" % (NOMBRE_CANDIDATO[ganador], ronda, motivo))
        if ganador in bono_jugador:
            explicacion.append("Su campaña la jugó una persona: terminó con reputación %d (%+.0f de confianza por votante)." % (
                50 + bono_jugador[ganador] * 5, bono_jugador[ganador]))
        for rival, _ in CANDIDATOS:
            if rival == ganador:
                continue
            golpes = [x for x in self.causas[rival] if x[1] < 0]
            if golpes:
                ronda, peso, motivo = min(golpes, key=lambda x: x[1])
                explicacion.append("En contra de %s, ronda %d: %s" % (NOMBRE_CANDIDATO[rival], ronda, motivo))
        if not explicacion:
            explicacion.append("Ninguna publicación movió el voto: ganó con la confianza que ya tenía en sus barrios.")
        explicacion.append("Participación responsable %d/100: votaron %d de %d ciudadanos." % (
            ind["participacion"], len(CIUDADANOS) - abstencion, len(CIUDADANOS)))
        self.fase = "final"
        self.eleccion = {"votos": votos, "abstencion": abstencion, "ganador": ganador,
                         "ganador_nombre": NOMBRE_CANDIDATO[ganador], "explicacion": explicacion,
                         "ciudad": self.resultado_ciudad(),
                         "ranking": [j.publico() for j in sorted(self.jugadores.values(), key=lambda j: (-j.puntos, j.id))]}
        return self.eleccion

    def resultado_ciudad(self):
        ind = self.indicadores
        positivo = sum(ind[k] for k in INDICADORES if k not in NEGATIVOS) / 5.0
        negativo = sum(ind[k] for k in NEGATIVOS) / 3.0
        indice = int(round(max(0, min(100, 50 + (positivo - negativo) / 2))))
        if indice >= 65:
            titulo, texto = "Ciudad informada", "Ciudad Nova llega a las urnas preguntando antes de compartir."
        elif indice >= 50:
            titulo, texto = "Ciudad dividida", "Se frenaron algunos rumores, pero la conversación quedó partida."
        else:
            titulo, texto = "Ciudad en caos informativo", "Los rumores corrieron más rápido que los datos."
        return {"indice": indice, "titulo": titulo, "texto": texto}

    # ----- vistas para la red (sin secretos) -----
    def _pub_publica(self, revelar=False):
        p = self.publicacion
        if p is None:
            return None
        datos = {"id": p["id"], "texto": p["texto"], "autor": p["autor"], "zona": p["zona"],
                 "zona_nombre": NOMBRE_ZONA[p["zona"]],
                 "candidato": NOMBRE_CANDIDATO.get(p["candidato"]) if p["candidato"] else None}
        if revelar:
            datos.update(tipo=p["tipo"], fuente=p["fuente"])
        return datos

    def vista_ronda_publica(self):
        return {"ronda": self.ronda, "total_rondas": self.total_rondas, "evento": self.evento["titulo"],
                "publicacion": self._pub_publica(), "segundos": self.tiempo_ronda()}

    def arbol_de(self, jid):
        return arbol_a_dict(self.arboles[jid].raiz) if jid in self.arboles else None

    def estado_publico(self):
        return {"fase": self.fase, "ronda": self.ronda, "total_rondas": self.total_rondas,
                "jugadores": [j.publico() for j in self.jugadores.values()],
                "indicadores": dict(self.indicadores), "decidieron": sorted(self.acciones),
                "candidatos": [{"id": c, "nombre": n} for c, n in CANDIDATOS]}

    def grafo_publico(self):
        nodos = [{"id": n, "nombre": self.grafo.nombre(n), "tipo": self.grafo.tipo(n),
                  "zona": self.grafo.perfil(n).get("zona")} for n in self.grafo.lista_nodos()]
        return {"nodos": nodos, "aristas": [[a, b, w] for a, b, w in self.grafo.aristas()],
                "zonas": list(ZONAS), "calles": [list(c) for c in CALLES]}
