## QA: recorre el guion REAL de forma automatica con un perfil de jugador.
## Inerte salvo con la variable de entorno ALCALDE_QA=<perfil>. No entra en las builds (ver options.rpy).
##   ALCALDE_QA=investigador|prudente|impulsivo|casual|dividido
##   ALCALDE_QA_MODO=historia|feria     ALCALDE_QA_SALIDA=<ruta.json>
## Los minijuegos se sustituyen por resultados fijos del perfil (sus clases ya tienen pruebas propias).

init -10 python:
    import os as _qa_os
    QA_PERFIL = _qa_os.environ.get("ALCALDE_QA")
    QA_MODO = _qa_os.environ.get("ALCALDE_QA_MODO", "historia")
    QA_SALIDA = _qa_os.environ.get("ALCALDE_QA_SALIDA", "qa_resultado.json")
    QA_VISUAL = _qa_os.environ.get("ALCALDE_QA_VISUAL")

    def qa_ajustar_ventana():
        """ALCALDE_QA_TAM=1366x768 fija el tamano fisico de la ventana (las capturas salen a ese tamano)."""
        tam = _qa_os.environ.get("ALCALDE_QA_TAM")
        if tam:
            w, h = [int(v) for v in tam.lower().split("x")]
            _preferences.fullscreen = False
            renpy.set_physical_size((w, h))

screen qa_auto_foto():
    zorder 1000
    timer 0.15 repeat True action Function(qa_foto_linea)

init 999 python:
    if QA_PERFIL:
        import json as _qa_json
        import renpy.exports as _qa_ex

        # Prioridad de opciones por perfil: se elige la primera que contenga alguno de estos textos.
        QA_PREFERENCIAS = {
            "investigador": ["Intentarlo de nuevo", "Pedir los análisis", "Ayúdame", "arreglémoslo", "Te equivocaste",
                             "Vine a escucharte", "Esa periodista", "le debes algo", "Alguien del barrio",
                             "Rodrigo: que hable", "Publícalo", "Desmentirlo", "Claudia, en la redacción",
                             "Ganemos o perdamos", "No voy a usar mentiras", "Resonancia Consultores.",
                             "Publicar el expediente completo", "Analítico", "¿Trabajas para Resonancia"],
            "prudente": ["Intentarlo de nuevo", "Pedir los análisis", "Ayúdame", "arreglémoslo", "Te equivocaste",
                         "Vine a escucharte", "En 2019 la alcaldía", "Alguien del barrio", "Claudia: la investigación",
                         "Recházalo", "Desmentirlo", "Tomás Vega, a tomar", "Trato hecho", "No voy a usar mentiras",
                         "Todavía no lo sabemos", "Cercano"],
            "impulsivo": ["Seguir adelante", "Publicar un desmentido", "Repartir botellas", "Una pregunta con",
                          "no puedo responder", "Eso fue otra", "Martina: el live", "Acéptalo", "Compartirlo",
                          "Martina, en su estudio", "Tus números", "Es tarde", "Lo que la gente crea", "Tomás Vega, para",
                          "Mediático"],
            "casual": ["Seguir adelante", "Ignorarlo", "Ignorarlo y hablar", "Una pregunta con", "no puedo responder",
                       "Todos hemos", "Eso fue otra", "Seguir con la visita", "Martina: el live", "Es tu decisión",
                       "No tocarlo", "Nadie. Quedarme", "Lo que la gente crea", "NOVA, por su cuenta", "Político"],
            "dividido": ["Seguir adelante", "Publicar un desmentido", "Ignorarlo y hablar", "Entonces arreglémoslo",
                         "Todos hemos", "Vine a escucharte", "Seguir con la visita", "Martina: el live",
                         "Recházalo", "No tocarlo", "Rodrigo, en el Barrio Sur", "Cuídense", "No voy a usar mentiras",
                         "Todavía no lo sabemos", "Cercano"],
        }
        # Resultado de cada minijuego por perfil: (exito, calificacion).
        QA_MINIJUEGOS = {
            "investigador": {"moderador": (True, "S"), "contencion": (True, "S"), "rastreador": (True, "S"), "viralizacion": (True, "A"), "ritmo": (True, "S")},
            "prudente": {"moderador": (True, "A"), "contencion": (True, "A"), "rastreador": (True, "B"), "viralizacion": (True, "A"), "ritmo": (True, "A")},
            "impulsivo": {"moderador": (True, "B"), "contencion": (True, "B"), "rastreador": (True, "C"), "viralizacion": (True, "B"), "ritmo": (True, "B")},
            "casual": {"moderador": (False, "D"), "contencion": (False, "D"), "rastreador": (False, "D"), "viralizacion": (False, "D"), "ritmo": (False, "D")},
            "dividido": {"moderador": (True, "B"), "contencion": (False, "D"), "rastreador": (True, "C"), "viralizacion": (False, "D"), "ritmo": (False, "D")},
        }
        QA_TELEFONO = {"investigador": "verificar", "prudente": "verificar", "impulsivo": "compartir",
                       "casual": "ignorar", "dividido": "mixto"}
        QA_CONSECUENCIA = {
            "moderador": ({"desinformacion": -6, "info_verificada": 4, "confianza": 2, "puntos": 20},
                          {"desinformacion": 4, "confianza": -2}),
            "contencion": ({"desinformacion": -7, "confianza": 4, "conflictos": -3, "puntos": 14},
                           {"desinformacion": 7, "conflictos": 4, "confianza": -4}),
            "viralizacion": ({"desinformacion": -7, "confianza": 4, "conflictos": -3, "puntos": 14},
                             {"desinformacion": 7, "conflictos": 4, "confianza": -4}),
            "rastreador": ({"desinformacion": -8, "confianza": 5, "info_verificada": 5, "reputacion": 8, "puntos": 16},
                           {"desinformacion": 4, "confianza": -3, "reputacion": -4}),
            "ritmo": ({"desinformacion": -5, "confianza": 4, "info_verificada": 3, "puntos": 12},
                      {"desinformacion": 2, "confianza": -1}),
        }
        qa_log = {"menus": [], "telefono": [], "lineas": []}

        def qa_contar_linea(who, *args, **kwargs):
            ctx = renpy.game.context()
            qa_log["lineas"].append(ctx.translate_identifier or ctx.deferred_translate_identifier or "")
            return args, kwargs

        config.say_arguments_callback = qa_contar_linea
        qa_pub_n = [0]

        def _qa_valor(v):
            return getattr(v, "value", v)

        def qa_menu(items, **kwargs):
            opciones = [(l, _qa_valor(v)) for l, v in items if v is not None]
            for preferida in QA_PREFERENCIAS[QA_PERFIL]:
                for etiqueta, valor in opciones:
                    if preferida in etiqueta:
                        qa_log["menus"].append(etiqueta)
                        return valor
            qa_log["menus"].append(opciones[0][0])
            return opciones[0][1]

        def qa_telefono(sesion):
            pub = sesion.publicacion
            if sesion.actual is pub.arbol.raiz:
                politica = QA_TELEFONO[QA_PERFIL]
                if politica == "mixto":
                    qa_pub_n[0] += 1
                    politica = ("verificar", "compartir", "ignorar")[qa_pub_n[0] % 3]
                return {"compartir": 0, "verificar": 1, "ignorar": 2}[politica]
            return 1 if pub.es_falsa else 0

        def qa_call_screen(nombre, *args, **kwargs):
            if nombre == "telefono_civitas":
                return qa_telefono(kwargs["sesion"])
            if nombre == "civitasnet" and QA_PERFIL == "investigador":
                for post in inv.feed_visible(mem()):
                    if post["pista"]:
                        dar_pista(post["pista"], aviso=False)
            if nombre == "elegir_alias":
                return True
            if nombre == "pantalla_resultados":
                final, resultado = args[0], args[1]
                datos = {"perfil": QA_PERFIL, "modo": QA_MODO, "final": final, "resultado": resultado,
                         "hechos": list(mem()["hechos"]), "pistas": dict(mem()["pistas"]),
                         "afinidad": dict(afinidad), "indicadores": indicadores_ciudad(),
                         "reputacion": jugador.get_reputacion(), "aliado": aliado_domingo(),
                         "estado_envio": estado_envio, "menus": qa_log["menus"], "lineas": qa_log["lineas"],
                         "voces": qa_log.get("voces", []),
                         "minijuegos": {k: v.get("exito") for k, v in registro_minijuegos.items()}}
                with open(QA_SALIDA, "w", encoding="utf-8") as f:
                    _qa_json.dump(datos, f, ensure_ascii=False, indent=1)
                renpy.quit()
            return None

        def qa_excepcion(corto, completo, traceback_fn):
            with open(QA_SALIDA, "w", encoding="utf-8") as f:
                _qa_json.dump({"perfil": QA_PERFIL, "modo": QA_MODO, "error": corto, "menus": qa_log["menus"]},
                              f, ensure_ascii=False, indent=1)
            _qa_os._exit(3)

        config.exception_handler = qa_excepcion

        def qa_aislar_guardado():
            """Ren'Py tambien guarda en game/saves; en QA solo se escribe en el --savedir aislado."""
            loc = renpy.loadsave.location
            if loc is None:
                return
            destino = _qa_os.path.normcase(_qa_os.path.abspath(renpy.config.savedir))
            loc.locations = [l for l in loc.locations
                             if _qa_os.path.normcase(_qa_os.path.abspath(l.directory)) == destino]
        qa_call_screen_original = _qa_ex.call_screen
        # Solo los perfiles de recorrido sustituyen pantallas y menus; capturas y mando usan las reales.
        if QA_PERFIL in QA_PREFERENCIAS:
            _qa_ex.call_screen = qa_call_screen
            renpy.call_screen = qa_call_screen
            menu = qa_menu

        def qa_resultado_minijuego(clave, aplicar):
            exito, nota = QA_MINIJUEGOS[QA_PERFIL][clave]
            r = {"minijuego": clave, "exito": exito, "calificacion": nota, "perfecto": nota == "S",
                 "inferencia": exito and nota in ("S", "A"),
                 "consecuencia": dict(QA_CONSECUENCIA[clave][0 if exito else 1])}
            return registrar_minijuego(r, aplicar)

        # Modo visual: el guion corre a velocidad de lectura rapida (sin skip) y se fotografia cada linea.
        qa_vis = {"linea": None, "desde": 0.0, "hecha": None, "n": 0}

        def qa_contar_linea_visual(who, *args, **kwargs):
            qa_contar_linea(who, *args, **kwargs)
            import time as _t
            qa_vis["n"] += 1
            qa_vis["linea"] = "%04d_%s" % (qa_vis["n"], renpy.game.context().current[1] if renpy.game.context().current else "")
            qa_vis["desde"] = _t.time()
            return args, kwargs

        def qa_foto_linea():
            import time as _t
            if qa_vis["linea"] and qa_vis["linea"] != qa_vis["hecha"] and _t.time() - qa_vis["desde"] > 0.45:
                qa_vis["hecha"] = qa_vis["linea"]
                nombre = "%04d_%s" % (qa_vis["n"], str(renpy.game.context().current[0]).replace("/", "_").replace(".rpy", "").replace(":", "_")[-40:])
                renpy.screenshot(_qa_os.path.join(QA_VISUAL, nombre + ".png"))
                qa_log.setdefault("voces", []).append((nombre, renpy.music.get_playing(channel="voice")))

        def qa_modo_visual():
            if not _qa_os.path.isdir(QA_VISUAL):
                _qa_os.makedirs(QA_VISUAL)
            config.say_arguments_callback = qa_contar_linea_visual
            renpy.config.skipping = None
            _preferences.transitions = 2
            _preferences.text_cps = 0
            _preferences.wait_voice = False
            _preferences.set_mute("voice", not _qa_os.environ.get("ALCALDE_QA_VOZ"))
            _preferences.set_mute("music", True)
            _preferences.set_mute("sfx", True)
            config.afm_characters = 10 ** 6
            config.afm_bonus = 10 ** 6
            _preferences.afm_time = 1.1
            _preferences.afm_enable = True
            renpy.game.preferences.afm_after_click = False
            renpy.show_screen("qa_auto_foto")

        if QA_PERFIL in QA_PREFERENCIAS:
          config.label_overrides.update({
            "minijuego_moderador": "qa_moderador", "minijuego_contencion": "qa_contencion",
            "minijuego_rastreador": "qa_rastreador", "evento_gran_viralizacion": "qa_viralizacion",
            "minijuego_ritmo": "qa_ritmo",
        })

label qa_moderador(aplicar=True, **kwargs):
    return qa_resultado_minijuego("moderador", aplicar)
label qa_contencion(aplicar=True, **kwargs):
    return qa_resultado_minijuego("contencion", aplicar)
label qa_rastreador(aplicar=True, **kwargs):
    return qa_resultado_minijuego("rastreador", aplicar)
label qa_viralizacion(aplicar=True, **kwargs):
    return qa_resultado_minijuego("viralizacion", aplicar)
label qa_ritmo(aplicar=True, **kwargs):
    return qa_resultado_minijuego("ritmo", aplicar)

label splashscreen:
    if not QA_PERFIL:
        return
    if QA_PERFIL != "limpiar":
        $ qa_aislar_guardado()
    if QA_PERFIL == "limpiar":
        # Deshace lo que escribieron recorridos de QA hechos sin --savedir.
        $ persistent.envios_pendientes = []
        $ persistent.top_cache = {}
        $ persistent.mejor_local = {}
        $ persistent.alias = None
        $ persistent.jugador_id = None
        $ persistent.finales_vistos.discard("mandato")
        $ renpy.save_persistent()
        $ renpy.quit()
    $ qa_ajustar_ventana()
    $ _preferences.skip_unseen = True
    $ _preferences.skip_after_choices = True
    $ _preferences.transitions = 0
    $ renpy.config.skipping = "fast"
    if QA_VISUAL and QA_PERFIL in QA_PREFERENCIAS:
        $ qa_modo_visual()
    if QA_PERFIL == "ritmo":
        $ renpy.config.skipping = None
        jump qa_ritmo_motor
    if QA_PERFIL == "mando":
        $ renpy.config.skipping = None
        jump qa_mando
    if QA_PERFIL == "galeria":
        $ _preferences.transitions = 2
        $ renpy.config.skipping = None
        jump qa_galeria
    if QA_PERFIL == "capturas":
        $ _preferences.transitions = 2
        $ renpy.config.skipping = None
        jump qa_capturas
    if QA_MODO == "feria":
        jump modo_feria
    jump start
