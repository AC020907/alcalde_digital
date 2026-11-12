## QA visual por etapas con el motor real: pantallas del sistema, escenas, CivitasNet/expediente y los cinco
## minijuegos jugados con entradas simuladas (mando) o jugadores automaticos. Inerte salvo con ALCALDE_QA=galeria.
##   ALCALDE_QA_ETAPA = menus | escenas | minijuegos | ritmo | finales     ALCALDE_QA_CAPTURAS = carpeta

init python:
    qa_gal = {"fotos": [], "eventos": []}

    def qa_gal_foto(nombre):
        qa_gal["fotos"].append(nombre)
        qa_captura(nombre)

    def qa_gal_volcar(**extra):
        qa_gal.update(extra)
        if qar_obs.get("muestras"):
            qa_gal["ritmo_muestras"] = qar_obs["muestras"]
        with open(QA_SALIDA, "w", encoding="utf-8") as f:
            _qam_json.dump({"galeria": qa_gal}, f, ensure_ascii=False, indent=1)

    def qa_gal_sim():
        s = renpy.get_screen("arcade_ui")
        return s.scope.get("sim") if s is not None else None

    def qa_gal_interceptar():
        sim = qa_gal_sim()
        if sim is not None and sim.jugando() and sim.paquetes:
            sim.interceptar(sim.paquetes[0])
            renpy.restart_interaction()

    def qa_gal_puzzle():
        s = renpy.get_screen("puzzle_rastreo_ui")
        return s.scope.get("p") if s is not None else None

    def qa_gal_puzzle_mal():
        p = qa_gal_puzzle()
        if p is None:
            return
        p.empezar()
        senuelos = [c for c in p.cartas if c not in p.solucion]
        cartas = (senuelos + list(p.solucion))[:p.eslabones]
        for i, c in enumerate(cartas):
            p.colocar(c, i)
        p.elegir_conclusion(p.opciones_conclusion[0])
        p.comprobar()
        renpy.restart_interaction()

    def qa_gal_puzzle_bien():
        p = qa_gal_puzzle()
        if p is None:
            return
        for i, c in enumerate(p.solucion):
            p.colocar(c, i)
        p.elegir_conclusion(p.tipo_origen())
        p.comprobar()
        if p.fase == "inferencia":
            for clave in p.opciones_inferencia:
                p.elegir_inferencia(clave) if hasattr(p, "elegir_inferencia") else None
                if p.inferencia_ok or not p.jugando():
                    break
        renpy.restart_interaction()

    def qa_gal_pasos_arcade(prefijo, ganar):
        pasos = [(1.5, "foto:%s_1_intro" % prefijo, None), (2.5, "a", "press"), (4.0, None, None),
                 (0.1, "foto:%s_2_juego" % prefijo, None)]
        if ganar:
            pasos += [(0.25, qa_gal_interceptar, None)] * 30
            pasos += [(0.1, "foto:%s_3_acierto" % prefijo, None)]
            pasos += [(0.25, qa_gal_interceptar, None)] * 80
        else:
            pasos += [(12.0, None, None), (0.1, "foto:%s_3_presion" % prefijo, None), (40.0, None, None)]
        return pasos

init python:
    def qa_gal_abandonar_duelo():
        s = renpy.get_screen("duelo_pantalla")
        if s is not None:
            s.scope["vista"].abandonar()

screen qa_gal_mirar_fin(nombre):
    zorder 1001
    timer 0.5 repeat True action If(qa_gal_sim() is not None and qa_gal_sim().terminado() and nombre not in qa_gal["fotos"],
                                    [Function(qa_gal_foto, nombre)])

label qa_galeria:
    # El QA arranca desde el splashscreen, donde Ren'Py desactiva historial y menu del juego: se restauran
    # como en una partida real.
    $ _history = True
    $ _game_menu_screen = "save"
    $ etapa_gal = _qa_os.environ.get("ALCALDE_QA_ETAPA", "menus")
    $ qa_pad_vigilante_hilo(500)
    $ qa_pad_limite = 450
    $ preparar_partida(feria=True)
    $ persistent.alias = "Vecina-2048"
    show screen qa_pad_inyector
    if etapa_gal == "menus":
        jump qa_gal_menus
    if etapa_gal == "escenas":
        jump qa_gal_escenas
    if etapa_gal == "minijuegos":
        jump qa_gal_minijuegos
    if etapa_gal == "ritmo":
        jump qa_gal_ritmo
    if etapa_gal == "finales":
        jump qa_gal_finales
    if etapa_gal == "arena_solo":
        jump qa_gal_arena_solo
    if etapa_gal in ("arena", "arena_cliente"):
        jump qa_gal_arena
    if etapa_gal == "dialogo":
        jump qa_gal_dialogo
    if etapa_gal == "personajes":
        jump qa_gal_personajes
    $ renpy.quit()

## ---------------- Pantallas del sistema ----------------
label qa_gal_menus:
    $ persistent.finales_vistos = set()
    scene bg despacho
    show claudia neutral at escena("claudia")
    # Texto instantaneo: con texto animado la primera A completa la linea y la segunda avanza.
    $ cps_previo = _preferences.text_cps
    $ _preferences.text_cps = 0
    $ qa_pad_programar([(1.0, "a", "press"), (1.0, "a", "press"), (1.0, "foto:m02_dialogo", None), (0.6, "a", "press")])
    c neutral "Alcalde. ¿Ya vio Civitas?"
    c seria "Una cuenta dice que el agua de Ciudad Nova está envenenada. Cuarenta mil reposts."
    c neutral "Claudia Reyes, de Noticias Nova. Esta semana trabajo con usted: alguien está fabricando miedo y quiero saber quién."
    $ _preferences.text_cps = cps_previo
    $ qa_gal["historial"] = [h.what[:40] for h in _history_list]
    $ renpy.show_screen("preferences")
    call qa_foto("m03_preferencias", 1.4)
    $ renpy.hide_screen("preferences")
    $ renpy.show_screen("save")
    call qa_foto("m04_guardar", 1.2)
    $ renpy.hide_screen("save")
    $ renpy.show_screen("load")
    call qa_foto("m05_cargar", 1.2)
    $ renpy.hide_screen("load")
    $ renpy.show_screen("history")
    call qa_foto("m06_historial", 1.2)
    $ renpy.hide_screen("history")
    $ renpy.show_screen("help")
    call qa_foto("m07_ayuda", 1.2)
    $ renpy.hide_screen("help")
    $ renpy.show_screen("about")
    call qa_foto("m08_creditos", 1.2)
    $ renpy.hide_screen("about")
    show screen confirm("¿Seguro que quieres salir?", NullAction(), NullAction())
    call qa_foto("m09_confirmar", 1.0)
    hide screen confirm
    hide claudia
    show screen archivo_destinos(None)
    call qa_foto("m10_archivo_vacio", 1.4)
    hide screen archivo_destinos
    $ persistent.finales_vistos = {"informada", "mandato"}
    show screen archivo_destinos("mandato")
    call qa_foto("m11_archivo_parcial", 1.6)
    hide screen archivo_destinos
    $ persistent.finales_vistos = set(destinos.FINALES)
    show screen archivo_destinos(None)
    call qa_foto("m12_archivo_completo", 1.6)
    hide screen archivo_destinos
    $ persistent.top_cache = {}
    $ persistent.mejor_local = {}
    show screen leaderboard_pantalla
    call qa_foto("m13_clasificacion_sin_conexion", 2.5)
    hide screen leaderboard_pantalla
    $ persistent.top_cache = {"historia": [
        {"rank": i + 1, "alias": a, "score": s, "final_title": t} for i, (a, s, t) in enumerate([
            ("Cronista-1180", 962, "Fuente Abierta"), ("Vecina-2048", 834, "Ciudad Informada"),
            ("Testigo-7731", 512, "Mandato Prestado"), ("Ciudadano-0042", 488, "Ciudad Dividida"),
            ("Lector-9001", 301, "Ciudad en Caos")])]}
    $ persistent.mejor_local = {"historia": {"score": 834, "final": "informada"}}
    show screen leaderboard_pantalla
    call qa_foto("m14_clasificacion", 2.5)
    hide screen leaderboard_pantalla
    show screen elegir_alias
    call qa_foto("m15_alias", 1.2)
    hide screen elegir_alias
    show screen ayuda_mando
    call qa_foto("m16_ayuda_mando", 1.2)
    hide screen ayuda_mando
    ## Al final: el menu principal nunca se muestra dentro de una partida en el juego real.
    show screen main_menu
    call qa_foto("m01_menu_principal", 2.0)
    hide screen main_menu
    $ qa_gal_volcar(etapa="menus", ok=True)
    $ renpy.quit()

## ---------------- Escenas, telefono, CivitasNet, expediente, mapa ----------------
label qa_gal_escenas:
    show screen titulo_acto("ACTO II  -  MIÉRCOLES", "El Barrio Sur", "Un rumor no necesita ser cierto. Solo necesita ser rápido.")
    call qa_foto("e01_titulo_acto", 1.6)
    hide screen titulo_acto
    scene bg barrio_sur at paneo
    show screen tarjeta_lugar("MIÉRCOLES  -  10:20 A.M.", "Barrio Sur")
    call qa_foto("e02_barrio_establecimiento", 1.4)
    scene bg barrio_sur conversacion
    show screen hud_ciudad
    show rodrigo enojada at escena("rodrigo")
    show screen qa_disparo("e03_barrio_conversacion", 1.0)
    r enojada "¡Alcalde! Todo el barrio dice que mañana cierran el hospital.{w=1.5}{nw}"
    hide screen qa_disparo
    hide screen tarjeta_lugar
    scene bg crisis
    show nova feliz at escena("nova", 0.78)
    show claudia triste at escena("claudia", 0.22)
    show screen qa_disparo("e04_crisis_dos_personajes", 1.0)
    n feliz "{cps=0}Todas las cuentas despiertan al mismo tiempo.{/cps}{w=1.5}{nw}"
    hide screen qa_disparo
    hide nova
    hide claudia
    scene bg operaciones
    $ sesion_gal = SesionPublicacion(banco.siguiente())
    show screen telefono_civitas(sesion=sesion_gal)
    call qa_foto("e05_telefono_publicacion", 1.6)
    hide screen telefono_civitas
    $ sesion_gal.elegir(1)
    show screen telefono_civitas(sesion=sesion_gal)
    call qa_foto("e06_telefono_verificar", 1.4)
    hide screen telefono_civitas
    show screen civitasnet()
    call qa_foto("e07_civitasnet_lunes", 1.6)
    hide screen civitasnet
    $ store.inv_mem_vacia = dict(mem()["pistas"])
    $ mem()["pistas"].clear()
    show screen expediente
    call qa_foto("e08_expediente_vacio", 1.4)
    hide screen expediente
    $ avanzar_momento(inv.MIERCOLES)
    $ [dar_pista(p, aviso=False) for p in list(inv.PISTAS)[:4]]
    show screen expediente
    call qa_foto("e09_expediente_parcial", 1.4)
    hide screen expediente
    $ avanzar_momento(inv.VIERNES)
    $ avanzar_momento(inv.DOMINGO)
    $ [dar_pista(p, aviso=False) for p in inv.PISTAS]
    show screen expediente
    call qa_foto("e10_expediente_completo", 1.4)
    hide screen expediente
    show screen civitasnet(llamada=True, destacar="net_audio_tomas")
    call qa_foto("e11_civitasnet_domingo", 1.6)
    hide screen civitasnet
    show screen misiones_ciudad
    call qa_foto("e12_misiones", 1.4)
    hide screen misiones_ciudad
    $ renpy.notify("Nueva pista: El audio de Tomás Vega")
    call qa_foto("e13_notificacion", 0.6)
    show screen mapa_viaje("barrio_sur")
    call qa_foto("e14_mapa_viaje", 2.0)
    $ qa_pad_programar([(0.2, "dpright", "press"), (1.5, "dpright", "release"), (0.1, "dpdown", "press"), (1.0, "dpdown", "release")])
    call qa_foto("e15_mapa_conduciendo", 2.8)
    hide screen mapa_viaje
    $ qa_gal_volcar(etapa="escenas", ok=True)
    $ renpy.quit()

## ---------------- Minijuegos 1-4 ----------------
label qa_gal_minijuegos:
    scene bg operaciones
    ## Moderacion: alterna borrar/aprobar para ver acierto y error.
    $ qa_pad_programar([(1.5, "foto:j01_moderador_inicio", None), (0.3, pausar_minijuego, None), (0.8, "foto:j01b_moderador_pausa", None),
                        (0.2, reanudar_minijuego, None), (1.0, "dpleft", "press"), (0.25, "foto:j02_moderador_feedback_a", None),
                        (1.2, "dpright", "press"), (0.25, "foto:j03_moderador_feedback_b", None)]
                       + [(0.9, ("dpleft" if i % 2 else "dpright"), "press") for i in range(8)]
                       + [(1.2, "foto:j04_moderador_resultado", None)] + qa_pad_repetir("a", 30, 1.0))
    call minijuego_moderador(aplicar=False, cantidad=6)
    $ qa_gal["eventos"].append(("moderador", _return.get("exito"), _return.get("calificacion")))
    ## Caza-Rumores: victoria con jugador automatico.
    show screen qa_gal_mirar_fin("j08_contencion_resultado_victoria")
    $ qa_pad_programar(qa_gal_pasos_arcade("j05_contencion", True) + qa_pad_repetir("a", 60, 1.0))
    call minijuego_contencion(aplicar=False, ajustes={"duracion": 20.0})
    hide screen qa_gal_mirar_fin
    $ qa_gal["eventos"].append(("contencion", _return.get("exito"), _return.get("calificacion")))
    ## Ruta de la Verdad (plataformero): tutorial, juego con piloto automatico y resultado.
    $ qa_plataformas_auto = 0.9
    $ qa_pad_programar([(1.5, "foto:j09_plataformas_tutorial", None), (0.3, "a", "press"), (1.6, "foto:j10_plataformas_cuenta", None),
                        (3.0, "foto:j11_plataformas_juego_a", None), (3.0, "foto:j11_plataformas_juego_b", None),
                        (3.0, "foto:j11_plataformas_juego_c", None), (6.5, "foto:j11_plataformas_victoria", None), (2.5, "foto:j12_plataformas_resultado", None)]
                       + qa_pad_repetir("a", 60, 1.0))
    call evento_gran_viralizacion(aplicar=False, ajustes={"nivel": "feria"})
    $ qa_plataformas_auto = None
    $ qa_gal["eventos"].append(("plataformas_fps", vista_plataformas.fps(), plataformas.tick, round(vista_plataformas.st - vista_plataformas.st0, 1)))
    $ qa_gal["eventos"].append(("viralizacion", _return.get("exito"), _return.get("calificacion")))
    ## Rastreador: tutorial, error con explicacion y victoria.
    $ qa_pad_programar([(1.5, "foto:j13_rastreador_tutorial", None), (0.5, qa_gal_puzzle_mal, None),
                        (1.0, "foto:j14_rastreador_error", None), (0.5, qa_gal_puzzle_bien, None),
                        (1.2, "foto:j15_rastreador_siguiente", None), (0.5, qa_gal_puzzle_bien, None),
                        (1.5, "foto:j16_rastreador_resultado", None)] + qa_pad_repetir("a", 40, 1.0))
    call minijuego_rastreador(aplicar=False, ajustes=FERIA_RASTREO)
    $ qa_gal["eventos"].append(("rastreador", _return.get("exito"), _return.get("calificacion")))
    $ qa_gal_volcar(etapa="minijuegos", ok=True)
    $ renpy.quit()

## ---------------- Duelo de Frecuencias ----------------
label qa_gal_ritmo:
    $ perfil_qar = _qa_os.environ.get("ALCALDE_QA_PASOS", "perfecto")
    $ qar_instalar("nada" if perfil_qar == "nada" else "perfecto")
    scene bg operaciones
    $ p_ = "r_%s_" % perfil_qar
    $ salida_pausa = [(0.5, qa_gal_abandonar_duelo, None), (1.5, "foto:%s06_resultados" % p_, None)] if perfil_qar == "abandonar" else [
        (0.5, "a", "press"), (6.0, "foto:%s05_juego_combo" % p_, None), (40.0, None, None), (1.0, "foto:%s06_resultados" % p_, None)]
    $ qa_pad_programar([(1.5, "foto:%s01_tutorial" % p_, None), (0.5, "a", "press"), (1.2, "foto:%s02_cuenta_atras" % p_, None),
                        (9.0, "foto:%s03_juego" % p_, None), (0.3, "start", "press"), (1.0, "foto:%s04_pausa" % p_, None)]
                       + salida_pausa + qa_pad_repetir("a", 20, 1.0))
    call minijuego_ritmo(modo="feria", aplicar=False, aliado="claudia")
    $ qa_gal["eventos"].append(("ritmo", _return.get("exito"), _return.get("calificacion"), _return.get("precision")))
    $ qa_gal_volcar(etapa="ritmo", ok=True)
    $ renpy.quit()

## ---------------- Pantallas de final ----------------
label qa_gal_finales:
    $ resultado_qa = {"verificacion": 260, "decisiones": 210, "minijuegos": 170, "investigacion": 120, "ciudad": 74, "total": 834}
    $ registro_minijuegos.update({"moderador": {"exito": True, "calificacion": "S"}, "contencion": {"exito": True, "calificacion": "A"},
                                  "rastreador": {"exito": True, "calificacion": "B"}, "viralizacion": {"exito": False, "calificacion": "D"},
                                  "ritmo": {"exito": True, "calificacion": "A"}})
    $ modo_feria_activo = True
    $ envios_gal = [("ok", "Puesto 3 en la clasificación (Vecina-2048)"),
                    ("pendiente", "Sin conexión con la clasificación. Lo enviaremos en tu próxima partida."),
                    ("pendiente", "Resultado guardado como no verificado: no entra en la tabla pública."),
                    ("error", "El servidor no aceptó este resultado."),
                    ("local", "Clasificación online no configurada. Tu récord se guardó en este equipo.")]
    $ i_gal = 0
    while i_gal < len(destinos.FINALES):
        $ final_gal = destinos.FINALES[i_gal]
        $ estado_envio = envios_gal[i_gal]
        $ ind_gal = {"info_verificada": 70 - i_gal * 10, "confianza": 72 - i_gal * 11, "convivencia": 60, "bienestar": 60,
                     "desinformacion": 20 + i_gal * 14, "conflictos": 15 + i_gal * 12}
        $ from clases.Eleccion import escrutinio_historia as _esc_gal
        show screen escrutinio_historia(_esc_gal(final_gal, ind_gal, 70 - i_gal * 8, 1))
        call qa_foto("f%02d_escrutinio_%s" % (i_gal + 1, final_gal), 1.6)
        hide screen escrutinio_historia
        show screen pantalla_resultados(final_gal, resultado_qa, i_gal % 2 == 0)
        call qa_foto("f%02d_resultados_%s" % (i_gal + 1, final_gal), 2.4)
        hide screen pantalla_resultados
        $ i_gal += 1
    $ qa_gal_volcar(etapa="finales", ok=True)
    $ renpy.quit()

## ---------------- Avance de dialogo con A (narrador y personaje) ----------------
label qa_gal_dialogo:
    $ qa_pad_vigilante_hilo(60)
    scene bg despacho
    $ variante_dlg = _qa_os.environ.get("ALCALDE_QA_PASOS", "")
    if variante_dlg == "w":
        ## Como el prologo: pausas {w} dentro de la linea; A salta cada pausa y luego avanza.
        $ qa_pad_programar([(1.0, "a", "press")] * 6)
        c "Una cuenta dice que el agua está envenenada.{w=0.4} Cuarenta mil reposts.{w=0.4} En una hora."
        $ qa_gal["eventos"].append("w_ok")
    elif variante_dlg == "nw":
        c neutral "Línea que se cierra sola.{w=0.3}{nw}"
        $ qa_gal["eventos"].append("nw_ok")
    $ qa_pad_programar([(1.5, "a", "press"), (1.5, "a", "press"), (1.5, "a", "press")])
    "Línea de narración: A debe avanzar."
    $ qa_gal["eventos"].append("narrador_ok")
    $ qa_gal_volcar(etapa="dialogo")
    show claudia neutral at escena("claudia")
    c neutral "Línea de Claudia: A debe avanzar."
    $ qa_gal["eventos"].append("claudia_ok")
    $ qa_gal["historial"] = [h.what[:40] for h in _history_list]
    $ qa_gal["diag"] = {"_history": _history, "contextos": len(renpy.game.contexts), "history_length": config.history_length,
                        "label_cb": str(config.history_callbacks)[:200]}
    $ qa_gal_volcar(etapa="dialogo", ok=True)
    $ renpy.quit()


## ---------------- Arena Civitas en red (anfitrion o cliente) ----------------
## ALCALDE_QA_ETAPA=arena (crea la sala) | arena_cliente (se une a 127.0.0.1). El resto de la sala la
## completan otros procesos (otro Ren'Py y tests/arena_bot.py), lanzados por tests/qa_visual.py.
init python:
    def qa_gal_modo_arena():
        import os as _o
        return _o.environ.get("ALCALDE_QA_ARENA_MODO", "feria")

    qa_ar = {"fotos_ronda": set(), "fotos_res": set(), "ultimo": 0.0, "final": False}

    def elegir_ruta_qa(arbol):
        from clases.arena.bot import elegir_ruta
        import random as _r
        return elegir_ruta(arbol, "responsable", _r.Random(0))

    def qa_arena_auto():
        import time as _t
        c = AS.cliente
        if c is None:
            return None
        ahora = _t.time()
        pref = "a_%s_" % ("host" if AS.servidor else "cliente")
        est = c.estado or {}
        if not est or est.get("fase") == "lobby":
            if not AS.servidor and est and c.jugador_id not in est.get("listos", []) and ahora - qa_ar["ultimo"] > 1:
                c.enviar("listo", listo=True)
                qa_ar["ultimo"] = ahora
            n = len(est.get("jugadores", []))
            if AS.servidor and n >= 4 and len(est.get("listos", [])) >= 3 and "sala" not in qa_ar["fotos_ronda"]:
                qa_ar["fotos_ronda"].add("sala")
                qa_gal_foto(pref + "02_sala_completa")
                c.enviar("empezar")
            elif not AS.servidor and n >= 2 and "sala" not in qa_ar["fotos_ronda"]:
                qa_ar["fotos_ronda"].add("sala")
                qa_gal_foto(pref + "02_sala")
            return None
        if c.prueba and AS.prueba_jugada != c.prueba["indice"]:
            k = "prueba%d" % c.prueba["indice"]
            if k not in qa_ar["fotos_res"]:
                qa_ar["fotos_res"].add(k)
                qa_ar["ultimo"] = ahora
            elif ahora - qa_ar["ultimo"] > 1.5:
                qa_gal_foto(pref + "%02d_prueba_%s" % (60 + c.prueba["indice"] * 4, c.prueba["clave"]))
                return "prueba"
            return None
        if c.prueba and c.mi_resultado and ("espera%d" % c.prueba["indice"]) not in qa_ar["fotos_res"]:
            qa_ar["fotos_res"].add("espera%d" % c.prueba["indice"])
            qa_gal_foto(pref + "%02d_espera_%s" % (61 + c.prueba["indice"] * 4, c.prueba["clave"]))
            return None
        if c.resumen and not c.final:
            k = "resumen%d" % c.resumen["indice"]
            if k not in qa_ar["fotos_res"]:
                qa_ar["fotos_res"].add(k)
                qa_ar["ultimo"] = ahora
            elif ahora - qa_ar["ultimo"] > 1.5 and ("f" + k) not in qa_ar["fotos_res"]:
                qa_ar["fotos_res"].add("f" + k)
                qa_gal_foto(pref + "%02d_resumen_%s" % (62 + c.resumen["indice"] * 4, c.resumen["clave"]))
                qa_gal["eventos"].append(("resumen", c.resumen["clave"], c.resumen["ganador"],
                                          {j: r["normalizado"] for j, r in c.resumen["resultados"].items()}))
                if AS.servidor:
                    c.enviar("continuar")
            return None
        if c.final:
            if not qa_ar["final"]:
                qa_ar["final"] = ahora
            elif ahora - qa_ar["final"] > 1.5 and "final" not in qa_ar["fotos_res"]:
                qa_ar["fotos_res"].add("final")
                qa_gal_foto(pref + "90_eleccion_final")
                qa_gal["eventos"].append(("final", c.final["ganador"], c.final["votos"], c.final["ciudad"]["indice"],
                                          (c.final.get("torneo") or {}).get("campeon")))
                return False
            return None
        if c.ronda and not c.ya_decidi():
            n = c.ronda["ronda"]
            if n not in qa_ar["fotos_ronda"]:
                qa_ar["fotos_ronda"].add(n)
                qa_ar["ultimo"] = ahora
                qa_ar["ruta_pendiente"] = None
                return None
            if ahora - qa_ar["ultimo"] > 1.6 and ("p%d" % n) not in qa_ar["fotos_ronda"]:
                qa_ar["fotos_ronda"].add("p%d" % n)
                qa_gal_foto(pref + "%02d_ronda" % (10 + n * 10))
                ruta = elegir_ruta_qa(c.arbol)
                qa_ar["ruta_pendiente"] = ruta[1:]
                qa_ar["ultimo"] = ahora
                arena_elegir(ruta[0])            # se navega el arbol como una persona: primero la rama...
            elif qa_ar.get("ruta_pendiente") and ahora - qa_ar["ultimo"] > 1.2:
                if ("v%d" % n) not in qa_ar["fotos_ronda"]:
                    qa_ar["fotos_ronda"].add("v%d" % n)
                    qa_gal_foto(pref + "%02d_verificar" % (11 + n * 10))
                arena_elegir(qa_ar["ruta_pendiente"].pop(0))   # ...y luego la respuesta
            return None
        if c.resultado:
            n = c.resultado["ronda"]
            if n not in qa_ar["fotos_res"]:
                qa_ar["fotos_res"].add(n)
                qa_ar["ultimo"] = ahora
            elif ahora - qa_ar["ultimo"] > 1.5 and ("f%d" % n) not in qa_ar["fotos_res"]:
                qa_ar["fotos_res"].add("f%d" % n)
                qa_gal_foto(pref + "%02d_resultado" % (15 + n * 10))
                qa_gal["eventos"].append(("resultado", n, c.resultado["n_alcanzados"], c.resultado["publicacion"]["tipo"]))
                if AS.servidor:
                    c.enviar("continuar")
        return None

screen qa_arena_auto():
    zorder 1001
    timer 0.25 repeat True action Function(qa_arena_auto)

label qa_gal_arena:
    $ qa_pad_limite = 900
    $ qa_pad_vigilante_hilo(400)
    $ anfitrion_qa = etapa_gal == "arena"
    $ qa_arena_torneo_auto = True   # las pruebas se entregan con decisiones de bot (el servidor las puntua igual)
    $ AS.modo = qa_gal_modo_arena()
    $ persistent.avisos_sonido = not anfitrion_qa
    $ pref_qa = "a_%s_" % ("host" if anfitrion_qa else "cliente")
    show screen arena_inicio
    call qa_foto(pref_qa + "01_inicio", 1.4)
    hide screen arena_inicio
    if anfitrion_qa:
        $ ok_qa = arena_crear("Ana", "ciudadano")
    else:
        $ ok_qa = None
        $ intentos_qa = 0
        while ok_qa is not True and intentos_qa < 60:
            $ ok_qa = arena_conectar("127.0.0.1", "Beto", "periodista")
            if ok_qa is not True:
                $ qa_call_screen_original("qa_espera", 0.5)
            $ intentos_qa += 1
    $ qa_gal["eventos"].append(("conectado", ok_qa is True))
    show screen qa_arena_auto
    $ arena_seguir = True
    while arena_seguir:
        call screen arena_partida
        if _return == "prueba":
            call arena_jugar_prueba
        else:
            $ arena_seguir = False
    hide screen qa_arena_auto
    $ renpy.show_screen("ayuda_civitas", pestana="arena")
    call qa_foto(pref_qa + "95_ayuda_arena", 1.0)
    $ renpy.hide_screen("ayuda_civitas")
    $ renpy.show_screen("ayuda_civitas", pestana="indicadores")
    call qa_foto(pref_qa + "96_ayuda_indicadores", 1.0)
    $ arena_salir()
    $ qa_gal_volcar(etapa="arena", ok=True)
    $ renpy.quit()


## ---------------- Arena: anfitrion solo pulsa Empezar (reproduce lo que vio el usuario) ----------------
init python:
    def qa_solo_empezar():
        AS.cliente.enviar("empezar")

    def qa_solo_fin():
        arena_salir()
        qa_gal_volcar(etapa="arena_solo", ok=True)
        renpy.quit()

    def qa_solo_estado():
        c = AS.cliente
        c.procesar()
        qa_gal["eventos"].append(("estado", (c.estado or {}).get("fase"), len((c.estado or {}).get("jugadores", [])), c.error))

label qa_gal_arena_solo:
    $ qa_pad_limite = 300
    $ ok_qa = arena_crear("Ana", "ciudadano")
    $ qa_pad_programar([(2.0, "foto:s00_solo_antes", None), (0.1, arena_empezar, None), (0.8, "foto:s01_preparando", None),
                        (0.1, qa_solo_estado, None), (8.0, "foto:s02_partida_iniciada", None), (0.1, qa_solo_estado, None),
                        (0.5, qa_solo_fin, None)])
    call screen arena_partida
    $ arena_salir()
    $ qa_gal_volcar(etapa="arena_solo", ok=True)
    $ renpy.quit()


## ---------------- Personajes: cada sprite en escena real y hoja de contacto ----------------
## Comprueba los sprites oficiales (y Tomas): escala, linea base, que no salten al cambiar de expresion,
## recortes, transparencias, retrato lateral y que no quede arte antiguo por error.
screen qa_hoja_personaje(nombre):
    add Solid("#3a3150")
    text "%s: 6 expresiones (alias: %s)" % (nombre.upper(), ", ".join("%s=%s" % (e, expresion_real(nombre, e)) for e in EXPRESIONES if expresion_real(nombre, e) != e) or "ninguno") size 26 color "#fbf6ee" xpos 30 ypos 20
    for i, e in enumerate(EXPRESIONES):
        fixed:
            xpos 20 + i * 315
            ypos 80
            xysize (310, 640)
            add Solid("#2b2440")
            add retrato_escena(nombre, e) xalign 0.5 yalign 1.0 zoom 0.55
            text e size 22 color "#facc15" xalign 0.5 yalign 0.0
        add retrato_lado(nombre, e) xpos 60 + i * 315 ypos 760
    text "Línea guía: base común de los sprites" size 18 color "#c9b8d8" xpos 30 ypos 1020

label qa_gal_personajes:
    $ qa_pad_limite = 300
    window show
    $ quick_menu = False
    python:
        hablantes = {"claudia": c, "martina": m, "rodrigo": r, "tomas": t, "nova": n}
    $ i_qa = 0
    while i_qa < len(PERSONAJES):
        $ nombre_qa = PERSONAJES[i_qa]
        window hide
        $ renpy.show_screen("qa_hoja_personaje", nombre=nombre_qa)
        call qa_foto("p_%s_hoja" % nombre_qa, 1.2)
        $ renpy.hide_screen("qa_hoja_personaje")
        scene bg operaciones
        $ j_qa = 0
        while j_qa < len(EXPRESIONES):
            $ expr_qa = EXPRESIONES[j_qa]
            $ renpy.show((nombre_qa, expr_qa), at_list=[escena(nombre_qa)])
            $ store.hablante = nombre_qa
            show screen qa_disparo("p_%s_%s" % (nombre_qa, expr_qa), 0.9)
            $ hablantes[nombre_qa]("Prueba de sprite: %s · %s.{w=1.2}{nw}" % (nombre_qa, expr_qa))
            hide screen qa_disparo
            $ j_qa += 1
        $ renpy.hide(nombre_qa)
        $ i_qa += 1
    ## Dos personajes a la vez (foco/atenuado) y retrato lateral cuando habla alguien fuera de escena.
    scene bg barrio_sur conversacion
    show rodrigo enojada at escena("rodrigo", 0.78)
    show claudia triste at escena("claudia", 0.22)
    show screen qa_disparo("p_dos_personajes", 1.0)
    r enojada "¡Alcalde! Todo el barrio dice que mañana cierran el hospital.{w=1.4}{nw}"
    hide screen qa_disparo
    scene bg crisis
    show screen qa_disparo("p_lateral_nova", 1.0)
    n feliz "Todas las cuentas despiertan al mismo tiempo.{w=1.4}{nw}"
    hide screen qa_disparo
    $ qa_gal_volcar(etapa="personajes", ok=True)
    $ renpy.quit()
