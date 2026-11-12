## Arena Civitas: multijugador local de 2 a 4 jugadores (cliente-servidor por sockets TCP en la LAN).
## La logica vive en clases/arena (Python puro, probada sin interfaz); aqui solo se dibuja y se envia
## lo que el jugador elige. Un equipo crea la sala (servidor + su propio cliente); los demas se unen con la IP.

init -5 python:
    import time as _arena_time
    from clases.arena import reglas as AR
    from clases.arena import protocolo as AP
    from clases.arena import sesion as AS
    # Sockets e hilos solo en escritorio: en la web la Arena muestra un aviso y estos modulos no se cargan.
    if not renpy.emscripten:
        from clases.arena.servidor import ServidorArena
        from clases.arena.cliente import ClienteArena
        from clases.arena.bot import BotArena
    from clases.GrafoSocial import GrafoSocial as _GrafoArena

    ARENA_RONDAS = 5
    ARENA_SEGUNDOS = 25
    ARENA_ICONO_TIPO = {"ciudadano": "ciudadano", "candidato": "influencer", "fuente": "medio", "jugador": "jugador"}
    ARENA_COLOR_ROL = {"ciudadano": "#2f9e8f", "periodista": "#5b5bd6", "influencer": "#d6457a", "candidato": "#c58a1b"}
    ARENA_CENTRO_ZONA = {"colegio": (1290, 290), "barrio": (1290, 470), "parque": (1035, 645),
                         "plaza": (1545, 645), "alcaldia": (1545, 830)}

    def arena_url_online():
        """Pagina de la Arena Online (servidor del leaderboard). Vacia si no hay servidor configurado."""
        base = url_api()
        return (base + "/arena") if base else ""

    def arena_error(texto):
        store.arena_mensaje = texto
        renpy.restart_interaction()

    def arena_crear(nombre, rol):
        arena_salir()
        try:
            import uuid as _uuid
            AS.clave = _uuid.uuid4().hex
            torneo = None if AS.modo == "clasica" else AS.modo
            AS.servidor = ServidorArena(puerto=AP.PUERTO, rondas=None if torneo else ARENA_RONDAS,
                                        segundos=ARENA_SEGUNDOS, clave_anfitrion=AS.clave, torneo=torneo)
            AS.servidor.iniciar()
        except OSError:
            AS.servidor = None
            return arena_error("No se pudo abrir el puerto %d: ¿hay otra sala abierta en este equipo?" % AP.PUERTO)
        return arena_conectar("127.0.0.1", nombre, rol, AS.clave)

    def arena_conectar(ip, nombre, rol, clave=None):
        if not rol:
            return arena_error("Elige un rol.")
        AS.cliente = ClienteArena((ip or "").strip() or "127.0.0.1", AP.PUERTO, timeout=3.0)
        try:
            AS.cliente.conectar()
        except OSError:
            AS.cliente = None
            return arena_error("No hay ninguna sala en %s. Revisa la IP y que estén en la misma red." % ip)
        AS.cliente.unirse(nombre, rol, clave=clave)
        AS.cliente.esperar(lambda c: c.jugador_id or c.error, 3.0)
        if not AS.cliente.jugador_id:
            texto = AS.cliente.error or "El servidor no respondió."
            AS.cliente.cerrar()
            AS.cliente = None
            return arena_error(texto)
        AS.ruta, AS.ronda_vista, AS.resultado_visto, AS.final_visto = [], None, None, False
        AS.prueba_jugada, AS.resumen_visto = None, None
        arena_preparar_grafo()
        store.arena_mensaje = ""
        return True

    def arena_salir():
        for b in AS.bots:
            b.detener()
        AS.bots = []
        if AS.cliente:
            AS.cliente.cerrar()
        AS.cliente = None
        if AS.servidor:
            AS.servidor.detener()
        AS.servidor = None

    def arena_tick():
        c = AS.cliente
        if c is None:
            return
        cambios = c.procesar()
        if AS.empezar_pendiente and c.estado and c.estado.get("fase") == "lobby":
            jugadores, faltan = arena_sala_info()
            if len(jugadores) >= AR.MIN_JUGADORES and not faltan:
                AS.empezar_pendiente = False
                c.enviar("empezar")
        elif AS.empezar_pendiente and c.estado and c.estado.get("fase") != "lobby":
            AS.empezar_pendiente = False
        if c.grafo is not AS.grafo_fuente:
            arena_preparar_grafo()
        if c.ronda and c.ronda["ronda"] != AS.ronda_vista:
            AS.ronda_vista, AS.ruta, AS.aviso_tiempo = c.ronda["ronda"], [], None
            sfx("alarma" if "viral" in c.ronda["evento"].lower() else "notificacion")
        if c.resultado and c.resultado["ronda"] != AS.resultado_visto:
            AS.resultado_visto = c.resultado["ronda"]
            mio = arena_mi_resultado()
            sfx("logro" if mio and mio["logros_nuevos"] else ("pista" if mio and mio["puntos"] > 0 else "error"))
        if c.resumen and c.resumen["indice"] != AS.resumen_visto:
            AS.resumen_visto = c.resumen["indice"]
            sfx("logro" if c.resumen["ganador"] == c.jugador_id else "pagina")
        if c.final and not AS.final_visto:
            AS.final_visto = True
            sfx("logro")
        restante = c.restante()
        if c.ronda and restante is not None and restante <= 5 and AS.aviso_tiempo is None and not c.ya_decidi():
            AS.aviso_tiempo = True
            sfx("alarma")
        if cambios or (c.ronda and not c.ya_decidi()) or c.prueba:
            renpy.restart_interaction()

    def arena_reconectar():
        """Vuelve al mismo puesto con el token: el servidor reenvia la ronda en curso."""
        try:
            AS.cliente.reconectar()
        except OSError:
            return arena_error("Sigue sin haber conexión con la sala.")
        store.arena_mensaje = ""
        renpy.restart_interaction()

    def arena_sala_info():
        """(jugadores, faltan_listos) de la sala, para explicar por que aun no se puede empezar."""
        est = (AS.cliente.estado if AS.cliente else None) or {"jugadores": [], "listos": []}
        jugadores = est["jugadores"]
        faltan = [j["nombre"] for j in jugadores if j["id"] != est.get("anfitrion") and j["id"] not in est["listos"]]
        return jugadores, faltan

    def arena_empezar():
        """Si el anfitrion esta solo, completa la sala con jugadores automaticos y empieza cuando esten listos."""
        jugadores, faltan = arena_sala_info()
        if len(jugadores) < AR.MIN_JUGADORES and AS.servidor:
            for _ in range(AR.MAX_JUGADORES - len(jugadores)):
                arena_agregar_bot()
            AS.empezar_pendiente = True
            store.arena_mensaje = ""
            AS.cliente.error = None
        elif faltan:
            AS.empezar_pendiente = True
        else:
            AS.cliente.enviar("empezar")
        renpy.restart_interaction()

    def arena_agregar_bot():
        if not AS.servidor:
            return
        ocupados = {j["rol"] for j in (AS.cliente.estado or {}).get("jugadores", [])}
        libres = [r for r in AR.ROLES if r not in ocupados and r not in [b.rol for b in AS.bots]]
        if libres:
            AS.bots.append(BotArena("127.0.0.1", AS.servidor.puerto, libres[0], semilla=len(AS.bots)).iniciar())

    # ----- arbol de decisiones de la ronda -----
    def arena_nodo():
        c = AS.cliente
        nodo = c.arbol if c and c.arbol else None
        for i in AS.ruta:
            if nodo is None or i >= len(nodo["hijos"]):
                return None
            nodo = nodo["hijos"][i]
        return nodo

    def arena_elegir(i):
        nodo = arena_nodo()
        if nodo is None or AS.cliente.ya_decidi():
            return
        hijo = nodo["hijos"][i]
        if hijo["hijos"]:
            AS.ruta.append(i)
            sfx("pagina")
        else:
            AS.cliente.decidir(AS.ruta + [i])
            sfx("decision")
        renpy.restart_interaction()

    def arena_volver():
        if AS.ruta:
            AS.ruta.pop()
        renpy.restart_interaction()

    # ----- grafo para dibujar -----
    def arena_preparar_grafo():
        datos = AS.cliente.grafo if AS.cliente else None
        AS.grafo_fuente = datos
        if not datos:
            AS.grafo = None
            return
        g = _GrafoArena()
        for n in datos["nodos"]:
            g.agregar_usuario(n["id"], n["nombre"], ARENA_ICONO_TIPO.get(n["tipo"], "medio"),
                              4 if n["tipo"] == "candidato" else 1, {"zona": n.get("zona")})
        for a, b, w in datos["aristas"]:
            g.agregar_conexion(a, b, w)
        AS.grafo = g

    def arena_grafo_ronda(autor):
        """Subgrafo visible: ciudadanos agrupados por zona, candidatos, jugadores y el autor de la publicacion."""
        base = AS.grafo
        if base is None:
            return None, {}
        jugadores = ["j:" + j["id"] for j in (AS.cliente.estado or {}).get("jugadores", [])]
        visibles = [n for n in base.lista_nodos() if base.tipo(n) == "ciudadano"]
        candidatos = ["@" + c for c, _ in AR.CANDIDATOS]
        visibles += candidatos + [j for j in jugadores if base.existe(j)]
        if autor and base.existe(autor):
            visibles.append(autor)
        g = _GrafoArena()
        for n in visibles:
            g.agregar_usuario(n, base.nombre(n), base.tipo(n), 1, base.perfil(n))
        for a, b, w in base.aristas():
            if a in g.adyacencia and b in g.adyacencia:
                g.agregar_conexion(a, b, w)
        pos = {}
        import math
        por_zona = {}
        for n in visibles:
            z = base.perfil(n).get("zona")
            if z:
                por_zona.setdefault(z, []).append(n)
        for z, nodos in por_zona.items():
            cx, cy = ARENA_CENTRO_ZONA[z]
            for k, n in enumerate(nodos):
                ang = 2 * math.pi * k / len(nodos) - math.pi / 2
                pos[n] = (int(cx + 92 * math.cos(ang)), int(cy + 70 * math.sin(ang)))
        for k, n in enumerate(candidatos):
            pos[n] = (1830, 240 + k * 150)
        for k, n in enumerate([j for j in jugadores if j in g.adyacencia]):
            pos[n] = (790, 300 + k * 150)
        if autor in g.adyacencia:
            pos[autor] = (790, 200 if not jugadores else 900)
        return g, pos

    def arena_estados(resultado):
        estados, resaltadas = {}, {}
        tipo = resultado["publicacion"].get("tipo")
        color = {"falsa": "infectado", "verdadera": "verificado"}.get(tipo, "activo")
        for n in resultado["alcanzados"]:
            estados[n] = color
        for n in resultado["protegidos"]:
            estados[n] = "contenido"
        for n in (resultado["niveles"][0] if resultado["niveles"] else []):
            estados[n] = "origen"
        for hijo, padre in resultado["padres"].items():
            resaltadas[(padre, hijo)] = COLOR_ESTADO[color]
        return estados, resaltadas

    def arena_mi_resultado():
        c = AS.cliente
        if not c or not c.resultado:
            return None
        for a in c.resultado["acciones"]:
            if a["jugador"] == c.jugador_id:
                return a
        return None

    def arena_yo():
        c = AS.cliente
        for j in (c.estado or {}).get("jugadores", []) if c else []:
            if j["id"] == c.jugador_id:
                return j
        return None

default arena_mensaje = ""

## ---------------- Entrada ----------------
label arena:
    $ _game_menu_screen = None
    $ quick_menu = False
    $ renpy.block_rollback()
    scene bg operaciones
    $ musica("crisis") if renpy.loadable("assets/audio/music/crisis.ogg") else None
    if renpy.emscripten:
        call screen arena_solo_escritorio
        return
    call screen arena_inicio
    if _return:
        $ arena_seguir = True
        while arena_seguir:
            call screen arena_partida
            if _return == "prueba":
                call arena_jugar_prueba
            else:
                $ arena_seguir = False
    $ arena_salir()
    $ _game_menu_screen = "save"
    return

screen arena_solo_escritorio():
    modal True
    add Solid("#120d1ccc")
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xsize 1100
        vbox:
            spacing 18
            text "ARENA CIVITAS" style "arena_titulo"
            text "En el navegador la Arena se juega online: cada persona abre la Arena en su teléfono o computador, una crea la sala y comparte el código. La gran final es el Duelo de Frecuencias: pulsa «Entrar al duelo» para activar el sonido y toca los 4 carriles al ritmo. La Arena de red local (sockets TCP) y el torneo con los 5 minijuegos están en la versión de escritorio." style "arena_texto"
            if arena_url_online():
                textbutton "Abrir Arena Online" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action OpenURL(arena_url_online()) default_focus True
                text arena_url_online() style "arena_nota" xalign 0.5
            textbutton "Volver" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return()

screen arena_inicio():
    modal True
    default nombre = ""
    default rol = "ciudadano"
    default ip = "192.168."
    default editando = "nombre"
    key "game_menu" action Return(False)
    add "bg operaciones"
    add Solid("#120d1cdd")
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xsize 1500
        vbox:
            spacing 16
            text "ARENA CIVITAS  ·  2 a 4 jugadores en la misma red" style "arena_titulo"
            text "Cada jugador usa su propio equipo. Uno crea la sala (es el servidor) y los demás se unen con su IP. Elegirán qué hacer con cada publicación de Civitas; el servidor propaga sus decisiones por la red social de Ciudad Nova y, al final, la ciudad elige alcalde." style "arena_texto"
            hbox:
                spacing 20
                text "Tu nombre:" style "arena_texto" yalign 0.5
                button:
                    style "arena_campo"
                    action SetScreenVariable("editando", "nombre")
                    input value ScreenVariableInputValue("nombre") length 20 style "arena_input" changed None:
                        default (editando == "nombre")
            hbox:
                spacing 14
                text "Modo:" style "arena_texto" yalign 0.5
                for m, etiqueta in ARENA_MODOS:
                    textbutton etiqueta style "arena_modo" text_style "arena_modo_texto" selected (AS.modo == m) action [SetField(AS, "modo", m), Function(sfx, "pagina")]
            text ARENA_DESCRIPCION_MODO[AS.modo] style "arena_nota"
            text "Elige tu rol (no se puede repetir en la sala):" style "arena_texto"
            hbox:
                spacing 14
                for r in AR.ROLES:
                    button:
                        style "arena_rol"
                        selected (rol == r)
                        background Frame("gui/frame.png", 20, 20)
                        foreground (Frame(Solid(ARENA_COLOR_ROL[r] + "40"), 0, 0) if rol == r else None)
                        action [SetScreenVariable("rol", r), Function(sfx, "pagina")]
                        vbox:
                            spacing 6
                            text ("» %s «" % AR.NOMBRE_ROL[r] if rol == r else AR.NOMBRE_ROL[r]) size 26 bold True color ARENA_COLOR_ROL[r]
                            text AR.DESCRIPCION_ROL[r] size 18 color "#2b2440"
            hbox:
                spacing 24
                xalign 0.5
                textbutton "Crear sala en este equipo" style "boton_vn_compacto" text_style "boton_vn_text" xsize 460 ysize 86:
                    action Function(_arena_intentar, "crear", nombre, rol, ip)
                    default_focus True
                vbox:
                    spacing 6
                    hbox:
                        spacing 10
                        text "IP de la sala:" style "arena_texto" yalign 0.5
                        button:
                            style "arena_campo"
                            xsize 300
                            action SetScreenVariable("editando", "ip")
                            input value ScreenVariableInputValue("ip") length 15 allow "0123456789." style "arena_input" changed None:
                                default (editando == "ip")
                    textbutton "Unirse a esa sala" style "boton_vn_compacto" text_style "boton_vn_text" xsize 460 ysize 86 action Function(_arena_intentar, "unir", nombre, rol, ip)
                textbutton "Volver" style "boton_vn_compacto" text_style "boton_vn_text" xsize 240 ysize 86 action Return(False)
            if arena_mensaje:
                text arena_mensaje style "arena_texto" color "#c0392b" xalign 0.5
            hbox:
                xalign 0.5
                spacing 30
                textbutton "AYUDA: roles, reglas y cómo ganar" style "arena_link" action Show("ayuda_civitas", pestana="arena")
                if arena_url_online():
                    textbutton "¿Cada uno en su red o en el teléfono? Arena Online" style "arena_link" action OpenURL(arena_url_online())

init python:
    def _arena_intentar(modo, nombre, rol, ip):
        ok = arena_crear(nombre, rol) if modo == "crear" else arena_conectar(ip, nombre, rol)
        if ok is True:
            return True   # termina la pantalla (call screen) con True
        return None

## ---------------- Partida (sala, rondas, resultados y eleccion) ----------------
screen arena_partida():
    modal True
    timer 0.1 repeat True action Function(arena_tick)
    $ c = AS.cliente
    add "bg operaciones"
    add Solid("#120d1ce6")
    if c is None:
        null
    elif c.cerrado and not c.final:
        use arena_aviso("Conexión perdida", c.cerrado, puede_reconectar=(AS.servidor is None and c.token is not None))
    elif c.final and c.final.get("torneo"):
        use arena_final_torneo(c)
    elif c.final:
        use arena_final(c)
    elif c.prueba:
        use arena_prueba(c)
    elif c.resumen:
        use arena_resumen_prueba(c)
    elif c.estado is None or c.estado["fase"] == "lobby":
        use arena_sala(c)
    else:
        use arena_cabecera(c)
        if c.resultado:
            use arena_resultado(c)
        else:
            use arena_ronda(c)
        use arena_marcador(c)
    key "game_menu" action Show("arena_confirmar_salida")

screen arena_aviso(titulo, texto, puede_reconectar=False):
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xsize 1000
        vbox:
            spacing 18
            text titulo style "arena_titulo"
            text texto style "arena_texto"
            hbox:
                spacing 20
                xalign 0.5
                if puede_reconectar:
                    textbutton "Reconectar" style "boton_vn" text_style "boton_vn_text" action Function(arena_reconectar) default_focus True
                textbutton "Volver al menú" style "boton_vn" text_style "boton_vn_text" action Return(False) default_focus (not puede_reconectar)
            if arena_mensaje:
                text arena_mensaje style "arena_texto" color "#c0392b"

screen arena_confirmar_salida():
    modal True
    zorder 200
    add Solid("#000000a0")
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        vbox:
            spacing 16
            text "¿Salir de la Arena?" style "arena_titulo"
            text ("Eres el servidor: si sales, la sala se cierra para todos." if AS.servidor else "Tu puesto se guarda unos minutos por si vuelves a unirte.") style "arena_texto"
            hbox:
                spacing 20
                xalign 0.5
                textbutton "Seguir jugando" style "boton_vn_compacto" text_style "boton_vn_text" action Hide("arena_confirmar_salida") default_focus True
                textbutton "Salir" style "boton_vn_compacto" text_style "boton_vn_text" action [Hide("arena_confirmar_salida"), Return(False)]

screen arena_sala(c):
    $ est = c.estado or {"jugadores": [], "listos": []}
    $ yo = arena_yo()
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xsize 1500
        vbox:
            spacing 14
            text "SALA DE LA ARENA" style "arena_titulo"
            if AS.servidor:
                text "Este equipo es el servidor. Los demás eligen «Unirse» y escriben: %s  (puerto %d)" % (", ".join(AS.servidor.direcciones_lan()), AP.PUERTO) style "arena_texto"
            else:
                text "Conectado a la sala. Espera a que el anfitrión empiece." style "arena_texto"
            null height 6
            for j in est["jugadores"]:
                hbox:
                    spacing 20
                    add circulo(ARENA_COLOR_ROL[j["rol"]] if j["conectado"] else "#d9d2e9", "#ffffff", 12) yalign 0.5
                    text j["nombre"] size 26 bold True color "#2b2440" min_width 360 yalign 0.5
                    text j["rol_nombre"] size 24 color ARENA_COLOR_ROL[j["rol"]] min_width 300 yalign 0.5
                    text ("Anfitrión" if j["id"] == est.get("anfitrion") else ("Listo" if j["id"] in est["listos"] else "Esperando…")) size 22 color "#5b4f72" yalign 0.5
            for k in range(4 - len(est["jugadores"])):
                text "Puesto libre" size 22 color "#8b84a8"
            null height 6
            $ jugadores_sala, faltan_sala = arena_sala_info()
            if AS.empezar_pendiente:
                text "Preparando la partida: esperando a que todos estén listos…" size 26 bold True color "#2f9e8f"
            elif len(jugadores_sala) < AR.MIN_JUGADORES:
                text ("Esperando jugadores: falta al menos 1 para empezar. Pide a los demás que se unan con la IP de arriba, o juega con jugadores automáticos." if AS.servidor else "Esperando a más jugadores…") size 24 bold True color "#c58a1b"
            elif faltan_sala:
                text "Esperando a que marquen «Estoy listo»: %s" % ", ".join(faltan_sala) size 24 bold True color "#c58a1b"
            elif c.soy_anfitrion():
                text "Todo listo: pulsa «Empezar»." size 24 bold True color "#2f9e8f"
            if est.get("modo_torneo"):
                text "Torneo %s: Consejo Cívico (%d rondas) + 5 pruebas: %s. Al final, la elección." % ("Feria" if est["modo_torneo"] == "feria" else "completo", est["total_rondas"], " · ".join(ARENA_NOMBRE_PRUEBA[k] for k in ARENA_PRUEBAS)) style "arena_nota"
            text "Se necesitan de 2 a 4 jugadores. Con 2 o 3, los roles que falten no juegan, pero los 4 candidatos siguen en la elección." style "arena_nota"
            hbox:
                spacing 20
                xalign 0.5
                if c.soy_anfitrion():
                    textbutton ("Jugar con jugadores automáticos" if len(jugadores_sala) < AR.MIN_JUGADORES and AS.servidor else "Empezar"):
                        style "boton_vn_compacto"
                        text_style "boton_vn_text"
                        xsize 460
                        ysize 86
                        action Function(arena_empezar)
                        default_focus True
                    if AS.servidor and len(est["jugadores"]) < 4:
                        textbutton "Añadir jugador automático" style "boton_vn_compacto" text_style "boton_vn_text" xsize 420 ysize 86 action Function(arena_agregar_bot)
                elif yo:
                    textbutton ("Listo (pulsa para cancelar)" if yo["id"] in est["listos"] else "Estoy listo") style "boton_vn" text_style "boton_vn_text" action Function(c.enviar, "listo", listo=yo["id"] not in est["listos"]) default_focus True
                textbutton "Salir" style "boton_vn" text_style "boton_vn_text" action Return(False)
            if c.error:
                text c.error style "arena_texto" color "#c0392b" xalign 0.5

screen arena_cabecera(c):
    $ est = c.estado
    $ ind = est["indicadores"]
    $ delta = c.resultado["delta_indicadores"] if c.resultado else {}
    frame:
        style "arena_barra"
        xfill True
        ypos 0
        hbox:
            spacing 26
            vbox:
                text "ARENA CIVITAS" size 30 bold True color "#fbf6ee"
                text "Ronda %d de %d" % (est["ronda"], est["total_rondas"]) size 22 color "#c9b8d8"
            grid 4 2:
                spacing 8
                for k in AR.INDICADORES:
                    hbox:
                        spacing 8
                        xsize 372
                        text AR.NOMBRE_INDICADOR[k] size 17 color ("#f4b6c2" if k in AR.NEGATIVOS else "#c9f2ea") min_width 200 yalign 0.5
                        bar value StaticValue(ind[k], 100) xsize 70 ysize 12 yalign 0.5 left_bar Solid("#e86a7e" if k in AR.NEGATIVOS else "#5eead4") right_bar Solid("#3a3350")
                        text "%d" % ind[k] size 17 color "#fbf6ee" yalign 0.5 min_width 34
                        text (("%+d" % delta[k]) if delta.get(k) else "") size 17 bold True color ("#5eead4" if (delta.get(k, 0) > 0) != (k in AR.NEGATIVOS) else "#f4b6c2") yalign 0.5
            textbutton "AYUDA" style "arena_link_claro" yalign 0.5 action Show("ayuda_civitas", pestana="arena")

screen arena_ronda(c):
    $ r = c.ronda
    $ pub = r["publicacion"] if r else None
    $ nodo = arena_nodo()
    $ restante = c.restante()
    $ yo = arena_yo()
    if r:
        frame:
            style "arena_panel"
            xpos 30
            ypos 150
            xsize 720
            vbox:
                spacing 12
                text r["evento"].upper() size 22 bold True color "#c0392b"
                frame:
                    style "arena_publicacion"
                    xfill True
                    vbox:
                        spacing 6
                        text pub["autor"] size 20 bold True color "#5b4f72"
                        text pub["texto"] size 30 bold True color "#2b2440"
                        text "Zona: %s%s" % (pub["zona_nombre"], ("  ·  Sobre: " + pub["candidato"]) if pub["candidato"] else "") size 18 color "#8b84a8"
                if restante is not None:
                    $ pausado = c.estado and c.estado.get("pausado")
                    hbox:
                        spacing 12
                        text ("En pausa" if pausado else "Tiempo restante: %d s" % int(restante + 0.99)) size 28 bold True color ("#c0392b" if restante <= 5 and not pausado else "#2b2440")
                        bar value StaticValue(restante, max(1, r["segundos"])) xsize 260 ysize 16 yalign 0.5 left_bar Solid("#c0392b" if restante <= 5 else "#5b5bd6") right_bar Solid("#d9d2e9")
                if c.ya_decidi():
                    text "Decisión enviada. Esperando al resto de la sala…" size 24 color "#2f9e8f"
                elif nodo:
                    text nodo["texto"] size 22 color "#2b2440"
                    for i, h in enumerate(nodo["hijos"]):
                        ## Una rama con hijos se presenta por su nombre ("Verificar"): lo que se averigua
                        ## solo aparece despues de elegirla.
                        textbutton (h["etiqueta"].capitalize() if h["hijos"] else h["texto"]):
                            style "arena_opcion"
                            text_style "arena_opcion_texto"
                            action Function(arena_elegir, i)
                            default_focus (i == 0)
                    if AS.ruta:
                        textbutton "« Volver a las opciones" style "arena_link" action Function(arena_volver)
                if yo:
                    text "Tu rol: %s. %s" % (yo["rol_nombre"], AR.DESCRIPCION_ROL[yo["rol"]]) style "arena_nota"
                if c.soy_anfitrion():
                    textbutton ("Reanudar" if c.estado.get("pausado") else "Pausar ronda") style "arena_link" action Function(c.enviar, "pausa", pausar=not c.estado.get("pausado"))
        ## Ciudad: zona de la publicacion en el grafo de la ciudad + quien ya decidio.
        use arena_mapa(pub["zona"] if pub else None, {}, {}, pub["autor"] if pub else None, "La publicación aparece en %s. Así se conecta Ciudad Nova:" % (pub["zona_nombre"] if pub else ""))

screen arena_mapa(zona_activa, estados, resaltadas, autor, titulo):
    $ g, pos = arena_grafo_ronda(autor)
    $ zonas_g = AR.construir_grafo_ciudad()
    text titulo size 22 color "#fbf6ee" xpos 780 ypos 116
    add capa_aristas(zonas_g, ARENA_CENTRO_ZONA, {(a, b): "#facc15" for a, b in AR.CALLES if zona_activa in (a, b)}, (), 1920)
    for z, (x, y) in ARENA_CENTRO_ZONA.items():
        frame:
            pos (x, y - 128)
            xanchor 0.5
            background Frame(Solid("#facc15" if z == zona_activa else "#3a3350"), 0, 0)
            padding (14, 4)
            text AR.NOMBRE_ZONA[z].upper() size 18 bold True color ("#1b1426" if z == zona_activa else "#fbf6ee")
    if g:
        ## Las cuentas de jugadores y candidatos se atenuan: lo que importa ver es por donde corre la publicacion.
        use grafo_red(g, pos, estados, resaltadas=resaltadas, atenuar=[n for n in g.lista_nodos() if g.tipo(n) != "ciudadano"], ancho=1920)

screen arena_resultado(c):
    $ res = c.resultado
    $ mio = arena_mi_resultado()
    $ estados, resaltadas = arena_estados(res)
    $ pub = res["publicacion"]
    frame:
        style "arena_panel"
        xpos 30
        ypos 150
        xsize 720
        vbox:
            spacing 10
            text {"falsa": "ERA FALSA", "verdadera": "ERA VERDADERA", "opinion": "ERA UNA OPINIÓN"}[pub["tipo"]] size 30 bold True color {"falsa": "#c0392b", "verdadera": "#2f9e8f", "opinion": "#c58a1b"}[pub["tipo"]]
            text pub["texto"] size 22 bold True color "#2b2440"
            text pub["fuente"] size 18 color "#5b4f72"
            text "Llegó a %d de %d ciudadanos en %d %s (%.1f por salto)%s." % (res["n_alcanzados"], len(AR.CIUDADANOS), res["saltos"], "salto" if res["saltos"] == 1 else "saltos", res["velocidad"], ("; %d quedaron protegidos" % len(res["protegidos"])) if res["protegidos"] else "") size 20 color "#2b2440"
            if res["desmentida"]:
                text "Rumor desmentido a tiempo." size 20 bold True color "#2f9e8f"
            if res["retirada"]:
                text "Civitas retiró la publicación por los reportes." size 20 color "#2f9e8f"
            null height 4
            for a in res["acciones"]:
                hbox:
                    spacing 10
                    text a["nombre"] size 20 bold True color ARENA_COLOR_ROL[a["rol"]] min_width 170
                    text "%s  (%+d)" % (a["texto_accion"], a["puntos"]) size 19 color ("#2f9e8f" if a["puntos"] > 0 else "#c0392b")
            if mio:
                frame:
                    style "arena_publicacion"
                    xfill True
                    vbox:
                        text mio["nota"] size 22 bold True color ("#2f9e8f" if mio["puntos"] > 0 else "#c0392b")
                        for l in mio["logros_nuevos"]:
                            text "¡Logro desbloqueado: %s!" % l size 22 bold True color "#c58a1b"
            if c.soy_anfitrion():
                textbutton "Siguiente ronda ›" style "boton_vn_compacto" text_style "boton_vn_text" action Function(c.enviar, "continuar") default_focus True
    use arena_mapa(pub["zona"], estados, resaltadas, pub["autor"], "Propagación por el grafo social (BFS desde el autor y quienes compartieron):")
    hbox:
        xpos 780
        ypos 1046
        spacing 22
        for est_, txt in (("origen", "Fuente"), ("infectado", "Recibió el rumor"), ("verificado", "Recibió información verificada"), ("activo", "Recibió la opinión"), ("contenido", "Protegido por un reporte")):
            hbox:
                spacing 6
                add circulo(COLOR_ESTADO[est_], "#ffffff", 10) yalign 0.5
                text txt size 17 color "#fbf6ee"

screen arena_marcador(c):
    hbox:
        xpos 30
        ypos 990
        spacing 14
        for j in c.estado["jugadores"]:
            frame:
                background Frame(Solid(ARENA_COLOR_ROL[j["rol"]] + ("ff" if j["id"] == c.jugador_id else "aa")), 0, 0)
                padding (12, 6)
                vbox:
                    text "%s · %s" % (j["nombre"], j["rol_nombre"]) size 17 bold True color "#ffffff"
                    text "%d pts · rep %d%s%s" % (j["puntos"], j["reputacion"], ("  · decidió" if j["id"] in c.estado["decidieron"] else ""), ("" if j["conectado"] else "  (desconectado)")) size 16 color "#ffffff"

screen arena_final(c):
    $ f = c.final
    $ total = max(1, sum(f["votos"].values()))
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xsize 1700
        hbox:
            spacing 40
            vbox:
                xsize 820
                spacing 12
                text "ELECCIÓN DE ALCALDE" style "arena_titulo"
                text "Gana %s" % f["ganador_nombre"] size 44 bold True color "#8c2f4b"
                for cid, nombre in AR.CANDIDATOS:
                    hbox:
                        spacing 12
                        text nombre size 22 bold (cid == f["ganador"]) color "#2b2440" min_width 220 yalign 0.5
                        bar value StaticValue(f["votos"][cid], total) xsize 380 ysize 22 yalign 0.5 left_bar Solid("#8c2f4b" if cid == f["ganador"] else "#a7a5f2") right_bar Solid("#ece6f5")
                        text ("1 voto" if f["votos"][cid] == 1 else "%d votos" % f["votos"][cid]) size 20 color "#2b2440" yalign 0.5
                text "Abstención: %d ciudadanos" % f["abstencion"] style "arena_nota"
                text "¿Por qué ganó?" size 24 bold True color "#2b2440"
                for e in f["explicacion"]:
                    text "· " + e size 19 color "#2b2440"
            vbox:
                spacing 12
                text "RESULTADO DE LA CIUDAD" style "arena_titulo"
                text "%s  (%d/100)" % (f["ciudad"]["titulo"], f["ciudad"]["indice"]) size 32 bold True color "#2f9e8f"
                text f["ciudad"]["texto"] style "arena_texto"
                text "PUNTUACIÓN INDIVIDUAL" size 24 bold True color "#2b2440"
                for k, j in enumerate(f["ranking"]):
                    vbox:
                        text "%d. %s (%s): %d puntos, reputación %d" % (k + 1, j["nombre"], j["rol_nombre"], j["puntos"], j["reputacion"]) size 21 color ARENA_COLOR_ROL[j["rol"]] bold True
                        if j["logros"]:
                            text "   Logros: " + ", ".join(j["logros"]) size 18 color "#c58a1b"
                null height 10
                textbutton "Volver al menú" style "boton_vn" text_style "boton_vn_text" action Return(False) default_focus True

style arena_panel:
    background Frame("gui/frame.png", 30, 30)
    padding (40, 30)
style arena_barra:
    background Solid("#1b1426f2")
    padding (30, 14)
style arena_publicacion:
    background Frame(Solid("#ffffff"), 0, 0)
    padding (20, 14)
style arena_titulo is default:
    size 36
    bold True
    color "#8c2f4b"
style arena_texto is default:
    size 22
    color "#2b2440"
style arena_nota is default:
    size 18
    italic True
    color "#5b4f72"
style arena_campo:
    background Frame(Solid("#ffffff"), 0, 0)
    hover_background Frame(Solid("#f3eefe"), 0, 0)
    padding (14, 8)
    xsize 460
style arena_input is default:
    size 24
    color "#2b2440"
style arena_rol:
    xsize 340
    padding (18, 14)
style arena_opcion:
    background Frame("gui/boton_menu_idle.png", 34, 24)
    hover_background Frame("gui/boton_menu_hover.png", 34, 24)
    xfill True
    padding (28, 16)
    hover_sound "assets/audio/sfx/menu_hover.ogg"
style arena_opcion_texto is default:
    size 24
    bold True
    color "#2b2440"
style arena_link is default:
    padding (6, 4)
style arena_link_text is default:
    size 20
    color "#5b5bd6"
    hover_color "#8c2f4b"
    underline True
style arena_link_claro is arena_link
style arena_link_claro_text is arena_link_text:
    color "#facc15"
    hover_color "#ffffff"
