## Cliente del leaderboard online (backend en leaderboard/). Nunca bloquea la partida:
## si el servidor no responde, el resultado queda en una cola y se reintenta mas tarde.
## La URL del servidor va en game/leaderboard_url.txt (una linea, https://...), o en la variable de
## entorno CIVITAS_API para QA. Sin URL, el juego guarda los records solo en el equipo.

define LEADERBOARD_URL = ""
define LEADERBOARD_VERSION = "2.0"

default persistent.jugador_id = None
default persistent.alias = None
default persistent.envios_pendientes = []
default persistent.mejor_local = {}
default persistent.top_cache = {}
default run_id = None
default run_verificable = False
default inicio_partida = 0.0
default estado_envio = None

init -1 python:
    import uuid
    import time
    import json as _json

    ALIAS_PREFIJOS = ("Ciudadano", "Vecina", "Lector", "Verificadora", "Testigo", "Cronista", "Brigadista")

    def _url_archivo():
        if not renpy.loadable("leaderboard_url.txt"):
            return ""
        with renpy.open_file("leaderboard_url.txt", encoding="utf-8") as f:
            return f.read().strip()

    LEADERBOARD_URL_ARCHIVO = _url_archivo()

    def url_api():
        if os.environ.get("ALCALDE_QA") and not os.environ.get("CIVITAS_API"):
            return ""  # los recorridos de QA nunca escriben en el servidor de produccion
        return (os.environ.get("CIVITAS_API") or LEADERBOARD_URL or LEADERBOARD_URL_ARCHIVO or "").rstrip("/")

    def leaderboard_activo():
        return bool(url_api())

    def plataforma():
        return "web" if renpy.emscripten else "pc"

    def asegurar_identidad():
        if not persistent.jugador_id:
            persistent.jugador_id = str(uuid.uuid4())
        if not persistent.alias:
            persistent.alias = alias_anonimo()

    def alias_anonimo():
        return "%s-%04d" % (renpy.random.choice(ALIAS_PREFIJOS), renpy.random.randint(1000, 9999))

    def _api(metodo, ruta, cuerpo=None, timeout=5):
        """Devuelve el JSON de la respuesta o lanza Exception; nunca se llama sin URL configurada."""
        datos = renpy.fetch(url_api() + ruta, method=metodo, json=cuerpo, timeout=timeout, result="text")
        return _json.loads(datos) if datos else {}

    def iniciar_run(modo):
        """Al empezar: id de partida del servidor (duracion verificable) o uno local si no hay red."""
        if modo == "feria":
            # En el stand cada partida es un visitante distinto: no comparten entrada en la tabla.
            persistent.jugador_id = str(uuid.uuid4())
            persistent.alias = alias_anonimo()
        asegurar_identidad()
        store.inicio_partida = time.time()
        store.run_id = str(uuid.uuid4())
        store.run_verificable = False
        store.estado_envio = None
        if not leaderboard_activo():
            return
        try:
            r = _api("POST", "/api/runs/start", {"player_id": persistent.jugador_id, "mode": modo,
                                                  "platform": plataforma(), "version": LEADERBOARD_VERSION}, timeout=6)
            store.run_id = r["run_id"]
            store.run_verificable = True
        except Exception:
            pass

    def _guardar_mejor_local(modo, final, total):
        mejor = persistent.mejor_local.get(modo)
        if not mejor or total > mejor["score"]:
            persistent.mejor_local[modo] = {"score": total, "final": final}

    def duracion_partida():
        qa = os.environ.get("ALCALDE_QA_DURACION")
        if qa and os.environ.get("ALCALDE_QA"):
            return int(qa)
        return int(max(0, time.time() - (store.inicio_partida or time.time())))

    def _cuerpo_envio(final, resultado):
        modo = "feria" if store.modo_feria_activo else "historia"
        componentes = {k: resultado[k] for k in puntuacion.MAXIMOS}
        return {
            "run_id": store.run_id or str(uuid.uuid4()),
            "player_id": persistent.jugador_id,
            "alias": persistent.alias,
            "platform": plataforma(),
            "mode": modo,
            "final": final,
            "score": resultado["total"],
            "components": componentes,
            "evidencias": sum(inv.grupos_clave(store.memoria).values()),
            "duration_s": duracion_partida(),
            "finales_desbloqueados": finales_descubiertos(),
            "version": LEADERBOARD_VERSION,
        }

    def _enviar(cuerpo, timeout=6):
        return _api("POST", "/api/scores", cuerpo, timeout=timeout)

    def reintentar_pendientes(maximo=3):
        if not leaderboard_activo():
            return
        quedan = []
        for i, cuerpo in enumerate(list(persistent.envios_pendientes)):
            if i >= maximo:
                quedan.append(cuerpo)
                continue
            try:
                _enviar(cuerpo, timeout=4)
            except Exception as e:
                # Un 4xx es un envio invalido: reintentarlo no lo arregla.
                if getattr(e, "status_code", None) not in (400, 409, 410, 413, 422):
                    quedan.append(cuerpo)
        persistent.envios_pendientes = quedan

    def enviar_resultado_partida(final, resultado):
        asegurar_identidad()
        cuerpo = _cuerpo_envio(final, resultado)
        _guardar_mejor_local(cuerpo["mode"], final, resultado["total"])
        if not leaderboard_activo():
            store.estado_envio = ("local", "Clasificación online no configurada. Tu récord se guardó en este equipo.")
            return
        reintentar_pendientes()
        try:
            r = _enviar(cuerpo)
            if r.get("ranked", r.get("verified", True)):
                store.estado_envio = ("ok", "Puesto %d en la clasificación (%s)" % (r.get("rank", 0), cuerpo["alias"]))
            else:
                store.estado_envio = ("pendiente", "Resultado guardado como no verificado: no entra en la tabla pública.")
            persistent.top_cache[cuerpo["mode"]] = r.get("top", [])
        except Exception as e:
            if getattr(e, "status_code", None) in (400, 409, 410, 413, 422):
                store.estado_envio = ("error", "El servidor no aceptó este resultado.")
            else:
                persistent.envios_pendientes.append(cuerpo)
                store.estado_envio = ("pendiente", "Sin conexión con la clasificación. Lo enviaremos en tu próxima partida.")

    def actualizar_top(modo):
        """Llamada desde un boton: congela la pantalla como mucho unos segundos."""
        if not leaderboard_activo():
            return
        try:
            r = _api("GET", "/api/leaderboard?mode=%s&limit=10" % modo, timeout=4)
            persistent.top_cache[modo] = r.get("entries", [])
            store.top_error = None
        except Exception:
            store.top_error = "No se pudo conectar. Mostrando la última clasificación guardada."
        renpy.restart_interaction()

default top_error = None


## ---------------- Alias antes de enviar el resultado ----------------

screen elegir_alias():
    modal True
    zorder 120
    default editando = False
    add Solid("#1b1426cc")
    frame:
        align (0.5, 0.5)
        xsize 1240
        background Frame("gui/frame.png", 30, 30)
        padding (60, 44)
        has vbox
        spacing 22
        xfill True
        text "¿Con qué nombre apareces en la clasificación?" size 34 bold True color "#2b2440" xalign 0.5 text_align 0.5
        text "No uses tu nombre real si no quieres. Solo guardamos el alias, la puntuación y el final." size 21 color "#5b4f72" xalign 0.5 text_align 0.5
        if editando:
            frame:
                xalign 0.5
                xsize 600
                background Solid("#fbf6ee")
                padding (20, 12)
                input value FieldInputValue(persistent, "alias") length 20 allow "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZáéíóúÁÉÍÓÚñÑüÜ0123456789 _-." size 34 color "#2b2440"
        else:
            text "[persistent.alias]" size 44 bold True color "#5b5bd6" xalign 0.5
        hbox:
            xalign 0.5
            spacing 24
            textbutton "Usar este":
                style "boton_vn"
                text_style "boton_vn_text"
                xsize 330
                action If(len((persistent.alias or "").strip()) >= 3, Return(True))
                default_focus True
            textbutton "Otro anónimo":
                style "boton_vn"
                text_style "boton_vn_text"
                xsize 330
                action [SetField(persistent, "alias", alias_anonimo()), SetScreenVariable("editando", False)]
            textbutton ("Listo" if editando else "Escribir"):
                style "boton_vn"
                text_style "boton_vn_text"
                xsize 330
                action ToggleScreenVariable("editando")
    key "K_RETURN" action If(len((persistent.alias or "").strip()) >= 3, Return(True))


screen estado_envio_leaderboard():
    if estado_envio:
        $ tipo, mensaje = estado_envio
        text mensaje size 20 xalign 0.5 color {"ok": "#2f9e8f", "pendiente": "#d97706", "error": "#c0392b"}.get(tipo, "#8b84a8")


## ---------------- Pantalla de clasificacion ----------------

# Tres botones de 406 px no caben en el marco de 1100 px utiles: version estrecha que estira la imagen.
style boton_pestana_top is boton_vn:
    background Frame("gui/boton_menu_idle.png", 40, 20)
    hover_background Frame("gui/boton_menu_hover.png", 40, 20)
    xysize (340, 80)

screen leaderboard_pantalla():
    modal True
    zorder 130
    default modo = "feria" if modo_feria_activo else "historia"
    key "game_menu" action Hide("leaderboard_pantalla")
    add Solid("#1b1426e6")
    frame:
        align (0.5, 0.5)
        xsize 1200
        ysize 940
        background Frame("gui/frame.png", 30, 30)
        padding (50, 36)
        has vbox
        spacing 14
        xfill True
        text "CLASIFICACIÓN CÍVICA" size 40 bold True color "#2b2440" xalign 0.5 kerning 3
        hbox:
            xalign 0.5
            spacing 20
            textbutton ("» Historia «" if modo == "historia" else "Historia") style "boton_pestana_top" text_style "boton_vn_text" action SetScreenVariable("modo", "historia")
            textbutton ("» Modo Feria «" if modo == "feria" else "Modo Feria") style "boton_pestana_top" text_style "boton_vn_text" action SetScreenVariable("modo", "feria")
            if leaderboard_activo():
                textbutton "Actualizar" style "boton_pestana_top" text_style "boton_vn_text" action Function(actualizar_top, modo)
        if not leaderboard_activo():
            text "La clasificación online todavía no está configurada. Se muestran tus récords locales." size 20 color "#8b84a8" xalign 0.5
        elif top_error:
            text top_error size 20 color "#d97706" xalign 0.5
        $ entradas = persistent.top_cache.get(modo, [])
        frame:
            xfill True
            ysize 500
            background Solid("#fbf6ee")
            padding (30, 20)
            if entradas:
                vbox:
                    spacing 8
                    for e in entradas[:10]:
                        hbox:
                            xfill True
                            text ("%d." % e.get("rank", 0)) size 28 bold True color "#8c2f4b" min_width 70
                            text e.get("alias", "?") size 28 color "#2b2440" min_width 420
                            text e.get("final_title", "") size 22 color "#5b4f72" min_width 320 yalign 0.5
                            text str(e.get("score", 0)) size 30 bold True color "#5b5bd6" xalign 1.0
            else:
                text "Todavía no hay resultados guardados para este modo." size 24 color "#8b84a8" align (0.5, 0.5)
        $ mejor = persistent.mejor_local.get(modo)
        text (("Tu récord en este equipo: %d (%s)  -  alias: %s" % (mejor["score"], TITULO_FINAL.get(mejor["final"], ""), persistent.alias)) if mejor else "Aún no tienes récord en este modo.") size 22 color "#2b2440" xalign 0.5
        text ("Destinos descubiertos: %d de %d" % (len(finales_descubiertos()), len(destinos.FINALES))) size 20 color "#8c2f4b" xalign 0.5
        textbutton "CERRAR" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Hide("leaderboard_pantalla") default_focus True
