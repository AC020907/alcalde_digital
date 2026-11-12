## QA de mando: inyecta eventos de gamepad sinteticos (los mismos que crea renpy.display.controller
## para un mando real) en el mapa y en los minijuegos REALES y registra si responden.
## No sustituye la prueba con un mando fisico. Inerte salvo con ALCALDE_QA=mando.

init -10 python:
    import json as _qam_json
    qa_pad_cola = []
    qa_pad_obs = {}

    def qa_pad_evento(control, estado):
        if control.startswith("clic:"):
            x, y = [int(v) for v in control[5:].split(",")]
            pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (x, y), "rel": (0, 0), "buttons": (0, 0, 0)}))
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (x, y), "button": 1}))
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (x, y), "button": 1}))
            return
        if control.startswith("key:"):
            tecla = getattr(pygame, control[4:])
            for tipo in (pygame.KEYDOWN, pygame.KEYUP):
                pygame.event.post(pygame.event.Event(tipo, {"key": tecla, "mod": 0, "unicode": "", "scancode": 0, "repeat": False}))
            return
        nombre = "pad_%s_%s" % (control, estado)
        nombres = [nombre] + list(config.pad_bindings.get(nombre, ()))
        ev = pygame.event.Event(renpy.display.core.EVENTNAME, {"eventnames": nombres, "controller": nombre, "up": False})
        pygame.event.post(ev)

    def qa_pad_programar(pasos):
        """pasos: lista de (segundos_de_espera, control, estado); control None = solo esperar."""
        del qa_pad_cola[:]
        qa_pad_cola.extend(pasos)
        store.qa_pad_espera = 0.0

    def qa_pad_volcar():
        with open(QA_SALIDA, "w", encoding="utf-8") as f:
            _qam_json.dump(qa_pad_obs, f, ensure_ascii=False, indent=1)

    def qa_pad_tick(dt=0.1):
        qa_pad_obs["t"] = qa_pad_obs.get("t", 0.0) + dt
        if qa_pad_obs["t"] > store.qa_pad_limite:
            qa_pad_obs["vigilante"] = "tiempo agotado en etapa %s" % qa_pad_obs.get("etapa")
            qa_pad_volcar()
            _qa_os._exit(4)
        store.qa_pad_espera -= dt
        while qa_pad_cola and store.qa_pad_espera <= 0:
            espera, control, estado = qa_pad_cola.pop(0)
            if callable(control):
                control()
            elif control and control.startswith("foto:"):
                qa_gal_foto(control[5:])
            elif control:
                qa_pad_evento(control, estado)
            store.qa_pad_espera = espera
        qa_pad_observar()

    def qa_pad_observar():
        if renpy.get_screen("choice") is not None:
            qa_pad_obs.setdefault("menus", {})["ultimo_evento"] = str(renpy.display.interface.last_event)[:80] if hasattr(renpy.display.interface, "last_event") else None
            qa_pad_obs["menus"]["interaccion"] = str(renpy.game.context().interacting)
            qa_pad_obs.setdefault("menus", {})["foco_en_eleccion"] = qa_foco_nombre()
            fl = renpy.display.focus.focus_list
            qa_pad_obs["menus"]["focus_list"] = [(type(f.widget).__name__, bool(f.widget.style.keyboard_focus), str(f.screen)) for f in fl][:12]
            qa_pad_obs["menus"]["grab"] = str(renpy.display.focus.get_grab())
        arcade = renpy.get_screen("arcade_ui")
        if arcade is not None:
            vista = arcade.scope.get("vista")
            if vista is not None:
                qa_pad_obs.setdefault("arcade_mira", []).append(list(vista.mouse))
        puzzle = renpy.get_screen("puzzle_rastreo_ui")
        if puzzle is not None:
            p = puzzle.scope.get("p")
            if p is not None:
                if p.seleccionada:
                    qa_pad_obs["rastreador_selecciono"] = True
                qa_pad_obs["rastreador_estado"] = [p.estado, p.fase, round(p.transcurrido, 1), p.empezado, p.conclusion]
                foco = renpy.display.focus.get_focused()
                qa_pad_obs["foco"] = type(foco).__name__ + ":" + str(getattr(foco, "drag_name", "") or getattr(getattr(foco, "action", None), "__class__", type(None)).__name__)
                qa_pad_obs.setdefault("focos_vistos", [])
                if qa_pad_obs["foco"] not in qa_pad_obs["focos_vistos"]:
                    qa_pad_obs["focos_vistos"].append(qa_pad_obs["foco"])
                colocadas = sum(1 for s in p.slots if s is not None)
                qa_pad_obs["rastreador_colocadas"] = max(colocadas, qa_pad_obs.get("rastreador_colocadas", 0))

    def qa_pad_repetir(control, veces, espera):
        return [(espera, control, "press") for _i in range(veces)]

default qa_pad_espera = 0.0
default qa_pad_limite = 170

screen qa_pad_inyector():
    zorder 999
    timer 0.1 repeat True action Function(qa_pad_tick, 0.1)

screen qa_espera(segundos):
    zorder 998
    timer segundos action Return()

init python:
    def qa_pad_vigilante_hilo(segundos=80):
        import threading
        def disparar():
            try:
                qa_pad_obs["vigilante_hilo"] = "bloqueado"
                qa_pad_obs["pantallas"] = sorted(str(t) for t in renpy.exports.get_showing_tags("screens"))
                qa_pad_obs["cola_restante"] = len(qa_pad_cola)
                try:
                    qa_pad_obs["foco"] = qa_foco_nombre()
                except Exception as e:
                    qa_pad_obs["foco"] = repr(e)
                ctxs = renpy.game.contexts
                qa_pad_obs["contextos"] = len(ctxs)
                qa_pad_obs["nodos"] = [str(getattr(c, "current", None)) for c in ctxs]
                try:
                    qa_pad_obs["pantallas_ctx"] = [sorted(str(t) for t in c.scene_lists.get_all_displayables and [] or [])
                                                   for c in ctxs]
                except Exception as e:
                    qa_pad_obs["pantallas_ctx"] = repr(e)
                qa_pad_volcar()
            finally:
                _qa_os._exit(5)
        t = threading.Timer(segundos, disparar)
        t.daemon = True
        t.start()

label qa_mando:
    $ qa_pad_vigilante_hilo(85 if _qa_os.environ.get("ALCALDE_QA_ETAPA") else 200)
    $ preparar_partida(feria=True)
    show screen qa_pad_inyector
    $ qa_solo = _qa_os.environ.get("ALCALDE_QA_ETAPA")
    if qa_solo == "rastreador":
        jump qa_mando_rastreador
    if qa_solo == "menus":
        jump qa_mando_menus

    $ qa_pad_obs["etapa"] = "mapa"
    $ qa_pad_volcar()
    ## 1. Mapa: mantener la cruceta a la derecha y luego abajo debe mover el carro.
    show screen mapa_ciudad
    $ qa_call_screen_original("qa_espera", 0.5)
    $ qa_mapa_antes = renpy.get_screen("mapa_ciudad").scope["vista"].carro.estado()
    $ qa_pad_programar([(0.3, None, None), (1.6, "dpright", "press"), (0.2, "dpright", "release"),
                        (1.6, "dpdown", "press"), (0.2, "dpdown", "release")])
    $ qa_call_screen_original("qa_espera", 4.5)
    $ qa_pad_obs["mapa_antes"] = qa_mapa_antes
    $ qa_pad_obs["mapa_despues"] = renpy.get_screen("mapa_ciudad").scope["vista"].carro.estado()
    hide screen mapa_ciudad

    $ qa_pad_obs["etapa"] = "moderador"
    $ qa_pad_volcar()
    ## 2. Moderador: izquierda/derecha moderan; A en CONTINUAR termina.
    $ qa_pad_programar([(4.0, None, None)] + [(0.7, ("dpleft" if i % 2 else "dpright"), "press") for i in range(10)]
                       + qa_pad_repetir("a", 40, 1.0))
    call minijuego_moderador(aplicar=False, cantidad=6)
    $ qa_pad_obs["moderador"] = {k: _return.get(k) for k in ("exito", "aciertos", "errores")}

    $ qa_pad_obs["etapa"] = "contencion"
    $ qa_pad_volcar()
    ## 3. Caza-Rumores: mover la mira, disparar con A, onda con X; A en CONTINUAR termina.
    $ qa_pad_programar([(3.5, None, None), (0.8, "dpright", "press"), (0.1, "dpright", "release"),
                        (0.8, "dpup", "press"), (0.1, "dpup", "release")]
                       + qa_pad_repetir("a", 10, 0.3) + [(0.3, "x", "press")] + qa_pad_repetir("a", 60, 1.0))
    call minijuego_contencion(aplicar=False, ajustes={"duracion": 14.0})
    $ qa_pad_obs["contencion"] = {k: _return.get(k) for k in ("exito", "calificacion", "interceptados")}

    $ qa_pad_obs["etapa"] = "rastreador"
    $ qa_pad_volcar()
label qa_mando_rastreador:
    ## 4. Rastreador: la cruceta mueve el foco entre fichas y huecos; A elige y coloca.
    $ qa_variante = _qa_os.environ.get("ALCALDE_QA_PASOS", "mix")
    $ pasos_rastreo = [(2.0, None, None)]
    if qa_variante == "a":
        $ pasos_rastreo += qa_pad_repetir("a", 8, 0.5)
    elif qa_variante == "dpad":
        $ pasos_rastreo += [(0.4, d, "press") for d in ("dpdown", "dpright", "dpup", "dpleft") * 3]
    elif qa_variante == "colocar":
        $ pasos_rastreo += [(0.6, "a", "press")]
        $ pasos_rastreo += ([(0.4, "dpdown", "press")] * 3 + [(0.4, "a", "press")] + [(0.4, "dpup", "press")] * 3
                            + [(0.4, "a", "press")] + [(0.4, "dpright", "press")]) * 3
    elif qa_variante == "y":
        $ pasos_rastreo += [(0.5, "y", "press")] * 3
    else:
        $ pasos_rastreo += [(0.35, "dpdown", "press"), (0.35, "a", "press"), (0.35, "dpup", "press"), (0.35, "a", "press"),
                            (0.35, "dpright", "press"), (0.35, "a", "press"), (0.35, "dpdown", "press"), (0.35, "a", "press")] * 4
        $ pasos_rastreo += [(0.5, "y", "press")]
    $ pasos_rastreo += qa_pad_repetir("a", 60, 1.0)
    $ qa_pad_programar(pasos_rastreo)
    call minijuego_rastreador(aplicar=False, ajustes=dict(FERIA_RASTREO, tiempo=25.0))
    $ qa_pad_obs["rastreador"] = {k: _return.get(k) for k in ("exito", "calificacion", "pistas")}

    hide screen qa_pad_inyector
    python:
        with open(QA_SALIDA, "w", encoding="utf-8") as f:
            _qam_json.dump(qa_pad_obs, f, ensure_ascii=False, indent=1)
    $ renpy.quit()


## ---------------- Menus, dialogo, decisiones y pantallas ----------------
init python:
    def qa_foco_nombre():
        f = renpy.display.focus.get_focused()
        if f is None:
            return None
        texto = getattr(f, "child", None)
        return type(f).__name__ + ":" + str(getattr(getattr(texto, "text", None), "__str__", lambda: "")())[:30]

    def qa_registrar(clave, valor):
        qa_pad_obs.setdefault("menus", {})[clave] = valor
        qa_pad_volcar()

label qa_cerrar_con(pantalla, *args, boton="a", espera=1.2, **kwargs):
    $ renpy.show_screen(pantalla, *args, **kwargs)
    $ qa_pad_programar([(0.6, None, None), (0.4, boton, "press")])
    $ qa_call_screen_original("qa_espera", espera)
    $ qa_registrar(pantalla + "_cerrada_con_" + boton, renpy.get_screen(pantalla) is None)
    $ renpy.hide_screen(pantalla)
    return

label qa_mando_menus:
    $ qa_pad_obs["etapa"] = "menus"

    ## Menu principal: la cruceta debe llevar el foco a un boton.
    show screen main_menu
    $ qa_pad_programar([(0.5, None, None), (0.4, "dpdown", "press"), (0.4, "dpdown", "press")])
    $ qa_call_screen_original("qa_espera", 1.6)
    $ qa_registrar("menu_principal_foco", qa_foco_nombre())
    hide screen main_menu

    ## Pantallas con default_focus: A cierra. Expediente y CivitasNet: B (menu) cierra.
    call qa_cerrar_con("archivo_destinos")
    call qa_cerrar_con("leaderboard_pantalla")
    call qa_cerrar_con("expediente", boton="b")
    $ avanzar_momento(inv.MIERCOLES)
    call qa_cerrar_con("civitasnet", boton="b")

    ## CivitasNet: la cruceta recorre el feed (el foco baja por las publicaciones).
    show screen civitasnet
    $ qa_pad_programar([(0.6, None, None)] + [(0.3, "dpdown", "press")] * 8)
    $ qa_call_screen_original("qa_espera", 3.4)
    $ qa_registrar("civitasnet_foco", qa_foco_nombre())
    $ qa_registrar("civitasnet_scroll", round(renpy.get_screen("civitasnet").scope["feed_adj"].value, 1))
    hide screen civitasnet

    ## Dialogo: A avanza. Decision: cruceta + A elige la segunda opcion.
    if _qa_os.environ.get("ALCALDE_QA_PASOS") == "raton":
        $ qa_pad_programar([(0.8, "key:K_RETURN", None), (1.8, None, None), (0.8, "clic:960,%d" % 460, None), (1.0, "clic:960,%d" % 400, None)])
    elif _qa_os.environ.get("ALCALDE_QA_PASOS") == "teclado":
        $ qa_pad_programar([(0.8, "key:K_RETURN", None), (1.8, None, None), (0.8, "key:K_DOWN", None), (0.8, "key:K_RETURN", None)])
    else:
        $ qa_pad_programar([(0.8, "a", "press"), (1.8, None, None), (0.8, "dpdown", "press"), (0.8, "dpdown", "press"), (0.8, "a", "press")])
    "QA: esta línea debe avanzar con A."
    menu:
        "Primera opción":
            $ qa_registrar("decision", "primera")
        "Segunda opción":
            $ qa_registrar("decision", "segunda")
    $ qa_registrar("dialogo_avanza_con_a", True)

    ## Telefono de Civitas: cruceta + A recorren el arbol de decisiones hasta el final.
    $ qa_vistas_antes = publicaciones_vistas
    $ qa_pad_programar([(1.0, None, None)] + [(0.5, "dpdown", "press"), (0.5, "a", "press")] * 6 + qa_pad_repetir("a", 10, 0.8))
    call nueva_publicacion
    $ qa_registrar("telefono_completado", publicaciones_vistas > qa_vistas_antes and ultima_accion is not None)
    $ qa_registrar("telefono_accion", ultima_accion)

    ## Alias y resultados: A en el boton enfocado por defecto.
    $ qa_pad_programar([(0.8, "a", "press")])
    $ qa_alias = qa_call_screen_original("elegir_alias")
    $ qa_registrar("alias_acepta_con_a", qa_alias is True)
    $ qa_pad_programar([(1.5, "a", "press")])
    $ qa_call_screen_original("pantalla_resultados", "informada", {"verificacion": 1, "decisiones": 1, "minijuegos": 1, "investigacion": 1, "ciudad": 1, "total": 5}, False)
    $ qa_registrar("resultados_vuelve_con_a", True)

    hide screen qa_pad_inyector
    $ qa_pad_volcar()
    $ renpy.quit()
