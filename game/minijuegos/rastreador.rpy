## Minijuego 1 - Rastreador: tablero de evidencias (puzzle drag & drop).
## Uso:  call minijuego_rastreador                     (semilla aleatoria)
##       call minijuego_rastreador(semilla=7)          (partida reproducible)
##       call minijuego_rastreador(ajustes=FERIA_RASTREO) (version corta)
## Retorna (en _return) el dict de PuzzleEvidencias.resultado().
## La version arcade anterior sigue disponible como minijuego_rastreador_vivo (laboratorio).

init python:
    import time
    from clases.PuzzleEvidencias import PuzzleEvidencias, CONCLUSIONES, INFERENCIAS

    PUZZLE_NORMAL = {"eslabones": 3, "senuelos": 3, "tiempo": 120.0}
    # Caso narrativo: el rumor del agua, que empieza en @verdad.oculta a las 06:09 (prologo).
    CASO_AGUA = {"rumor": 0, "hora_base": 6 * 60 + 9, "candidatos": ["@verdad.oculta"]}
    PUZZLE_HISTORIA = dict(PUZZLE_NORMAL, inferencia=True, **CASO_AGUA)
    PUZZLE_CARTA = (290, 200)
    PUZZLE_HUECO = (310, 214)
    PUZZLE_SEPARACION = 70
    PUZZLE_FILA_Y = 210
    PUZZLE_MESA_Y = 650

    def puzzle_x_cadena(p, posicion):
        total = (p.eslabones + 1) * PUZZLE_HUECO[0] + p.eslabones * PUZZLE_SEPARACION
        return (1920 - total) // 2 + posicion * (PUZZLE_HUECO[0] + PUZZLE_SEPARACION)

    def puzzle_x_hueco(p, indice):
        # El origen queda a la izquierda y la publicacion viral a la derecha.
        return puzzle_x_cadena(p, p.eslabones - 1 - indice)

    def puzzle_pos_carta(p, carta):
        if carta in p.slots:
            x = puzzle_x_hueco(p, p.slots.index(carta))
            return x + (PUZZLE_HUECO[0] - PUZZLE_CARTA[0]) // 2, PUZZLE_FILA_Y + (PUZZLE_HUECO[1] - PUZZLE_CARTA[1]) // 2
        n = len(p.cartas)
        ancho = n * PUZZLE_CARTA[0] + (n - 1) * 18
        return (1920 - ancho) // 2 + p.cartas.index(carta) * (PUZZLE_CARTA[0] + 18), PUZZLE_MESA_Y

    def puzzle_procesar_eventos(p):
        while p.eventos:
            tipo, dato = p.eventos.pop(0)
            if tipo == "victoria":
                sonar(SONIDO_EXITO)
            elif tipo == "derrota":
                sonar(SONIDO_FALLO)
            elif tipo == "pista":
                sonar(SONIDO_AVISO["info"])
                renpy.show_screen("puzzle_feedback", texto="PISTA: el rumor pasó por %s" % dato, correcto=True)
            elif tipo == "pista1":
                sonar(SONIDO_AVISO["info"])
                renpy.show_screen("puzzle_feedback", texto="PISTA: ¿a quién sigue %s y quién publicó antes?" % dato, correcto=True)
            elif tipo == "pista_conclusion":
                sonar(SONIDO_AVISO["info"])
                renpy.show_screen("puzzle_feedback", texto="PISTA: la cadena está bien; mira la ficha del origen", correcto=True)
            elif tipo == "inferencia":
                sonar(SONIDO_AVISO["bueno"])
            elif tipo == "error_inferencia":
                sonar(SONIDO_FALLO)
            elif tipo == "error":
                sonar(SONIDO_FALLO)
                if dato == p.eslabones:
                    texto = "La cadena está bien, pero la conclusión no encaja"
                else:
                    texto = "%d de %d eslabones correctos" % (dato, p.eslabones)
                renpy.show_screen("puzzle_feedback", texto=texto, correcto=False)

    def puzzle_tick(p):
        p.tick_reloj(time.time())
        puzzle_procesar_eventos(p)

    def puzzle_comprobar(p):
        p.comprobar()
        puzzle_procesar_eventos(p)

    def puzzle_pista(p):
        p.pedir_pista()
        puzzle_procesar_eventos(p)

    def puzzle_soltar(drags, drop):
        p = store.puzzle_rastreo
        carta = drags[0].drag_name
        if drop is not None:
            p.colocar(carta, int(drop.drag_name[5:]))
            sonar(SONIDO_AVISO["info"])
        else:
            p.quitar(carta)
        renpy.restart_interaction()
        return None

    def puzzle_inferencia(p, clave):
        p.responder_inferencia(clave)
        puzzle_procesar_eventos(p)

    def puzzle_tecla_carta(p, numero):
        if 0 <= numero < len(p.cartas):
            puzzle_click_carta(p, p.cartas[numero])

    def puzzle_tecla_hueco(p, posicion):
        # Las teclas van de izquierda (origen) a derecha, como se ve el tablero.
        puzzle_click_hueco(p, p.eslabones - 1 - posicion)

    TECLAS_HUECO = ("K_z", "K_x", "K_c")

    def puzzle_click_carta(p, carta):
        if not p.jugando() or p.fase != "cadena":
            return
        if carta in p.slots:
            p.quitar(carta)
        elif p.seleccionada == carta:
            p.seleccionada = None
        else:
            p.seleccionada = carta
            libre = [i for i, s in enumerate(p.slots) if s is None]
            if len(libre) == 1:
                p.colocar(carta, libre[0])
                sonar(SONIDO_AVISO["info"])
        renpy.restart_interaction()

    def puzzle_click_hueco(p, indice):
        if p.jugando() and p.seleccionada and 0 <= indice < p.eslabones:
            p.colocar(p.seleccionada, indice)
            sonar(SONIDO_AVISO["info"])
            renpy.restart_interaction()


screen puzzle_feedback(texto, correcto):
    zorder 120
    text texto at feedback_moderador:
        xalign 0.5
        ypos 118
        size 34
        bold True
        color ("#2f9e8f" if correcto else "#e04f5f")
        outlines [(4, "#fbf6ee", 0, 0)]
    timer 1.4 action Hide("puzzle_feedback")

transform pista_brillo:
    alpha 1.0
    linear 0.5 alpha 0.35
    linear 0.5 alpha 1.0
    repeat

screen tarjeta_evidencia(p, nodo, cabecera=None, color_borde="#00000000"):
    $ ficha = p.ficha(nodo)
    $ fuentes = p.sigue_a(nodo)
    fixed:
        xysize PUZZLE_CARTA
        add Solid(color_borde) xysize PUZZLE_CARTA
        if nodo == p.pista_carta and nodo not in p.slots:
            add Solid("#22c55e") xysize PUZZLE_CARTA at pista_brillo
        elif nodo in p.candidatos_pista and nodo not in p.slots:
            add Solid("#facc15") xysize PUZZLE_CARTA at pista_brillo
        frame:
            xysize (PUZZLE_CARTA[0] - 10, PUZZLE_CARTA[1] - 10)
            align (0.5, 0.5)
            background Frame("gui/frame.png", 30, 30)
            padding (16, 12)
            vbox:
                spacing 4
                if cabecera:
                    text cabecera size 15 bold True color "#c0392b"
                hbox:
                    spacing 10
                    add Transform(icono_aparente(p.grafo, nodo, False), xysize=(46, 46)) yalign 0.5
                    vbox:
                        yalign 0.5
                        text nodo size 21 bold True color "#2b2440"
                        text "Publicó a las " + p.hora(nodo) size 19 bold True color "#8c2f4b"
                text ("Sigue a: " + ", ".join(fuentes) if fuentes else "No sigue a nadie del tablero") size 15 color "#4a4060"
                text "%s seguidores · creada %s%s" % (formato_num(ficha["seguidores"]), ficha["creada"], " · verificada" if ficha["verificada"] else "") size 14 color "#8b84a8"

screen puzzle_rastreo_ui(p, rumor):
    modal True
    zorder 40

    add "bg operaciones"
    add Solid("#1b1426c8")

    # ---- Cabecera ----
    vbox:
        xpos 60
        ypos 28
        spacing 4
        text "TABLERO DE EVIDENCIAS" size 40 bold True color "#fbf6ee"
        text "Rumor: " + rumor size 20 color "#f4b6c2"
        text "Cada cuenta recibió el rumor de alguien a quien SIGUE y que publicó ANTES." size 20 color "#c9b8d8"

    hbox:
        xalign 0.97
        ypos 34
        spacing 40
        vbox:
            text "TIEMPO" size 16 color "#a7a5f2"
            bar:
                xsize 260
                ysize 18
                value StaticValue(p.restante(), p.tiempo_total)
                left_bar Solid("#e86a7e" if p.restante() < 20 else "#a7a5f2")
                right_bar Solid("#3a3350")
            text "%d s" % int(p.restante()) size 26 bold True color "#fbf6ee"
        vbox:
            text "COMPROBACIONES" size 16 color "#a7a5f2"
            hbox:
                spacing 8
                for i in range(p.comprobaciones):
                    add circulo("#facc15" if i < p.comprobaciones_restantes() else "#3a3350", "#fbf6ee", 13)

    # ---- Cadena: origen -> difusion -> publicacion viral ----
    for i in range(p.eslabones):
        $ x_hueco = puzzle_x_hueco(p, i)
        text ("ORIGEN (publicó primero)" if i == p.eslabones - 1 else "DIFUSIÓN %d" % (p.eslabones - 1 - i)):
            xpos x_hueco + PUZZLE_HUECO[0] // 2
            xanchor 0.5
            ypos PUZZLE_FILA_Y - 34
            size 20
            bold True
            color ("#facc15" if i == p.eslabones - 1 else "#c9b8d8")
        $ estado_flecha = p.revision[i]
        $ color_flecha = "#2f9e8f" if estado_flecha else "#e04f5f" if estado_flecha is False else "#fbf6ee"
        fixed:
            xpos x_hueco + PUZZLE_HUECO[0] + 10
            ypos PUZZLE_FILA_Y + PUZZLE_HUECO[1] // 2 - 30
            xysize (PUZZLE_SEPARACION - 20, 60)
            add Solid(color_flecha) xysize (PUZZLE_SEPARACION - 34, 8) yalign 0.5
            text ">" size 48 bold True color color_flecha xalign 1.0 yalign 0.5

    $ x_viral = puzzle_x_cadena(p, p.eslabones)
    text "PUBLICACIÓN VIRAL":
        xpos x_viral + PUZZLE_HUECO[0] // 2
        xanchor 0.5
        ypos PUZZLE_FILA_Y - 34
        size 20
        bold True
        color "#f4b6c2"
    fixed:
        xpos x_viral + (PUZZLE_HUECO[0] - PUZZLE_CARTA[0]) // 2
        ypos PUZZLE_FILA_Y + (PUZZLE_HUECO[1] - PUZZLE_CARTA[1]) // 2
        xysize PUZZLE_CARTA
        use tarjeta_evidencia(p, p.inicio, "SE HIZO VIRAL", "#e86a7e")

    draggroup:
        for i in range(p.eslabones):
            $ revision_hueco = p.revision[i]
            drag:
                drag_name "hueco%d" % i
                draggable False
                droppable True
                xpos puzzle_x_hueco(p, i)
                ypos PUZZLE_FILA_Y
                clicked Function(puzzle_click_hueco, p, i)
                fixed:
                    xysize PUZZLE_HUECO
                    add Solid("#2f9e8f" if revision_hueco else "#e04f5f" if revision_hueco is False else "#a7a5f2" if p.seleccionada else "#fbf6ee66") xysize PUZZLE_HUECO
                    add Solid("#2a2238") xysize (PUZZLE_HUECO[0] - 8, PUZZLE_HUECO[1] - 8) align (0.5, 0.5)
                    if p.slots[i] is None:
                        text ("Suelta aquí" if not p.seleccionada else "Colocar aquí") size 22 color "#8b84a8" align (0.5, 0.5)

        for carta index (carta, p.version) in p.cartas:
            $ x_carta, y_carta = puzzle_pos_carta(p, carta)
            drag:
                drag_name carta
                droppable False
                draggable p.jugando()
                drag_raise True
                dragged puzzle_soltar
                clicked Function(puzzle_click_carta, p, carta)
                xpos x_carta
                ypos y_carta
                fixed:
                    xysize PUZZLE_CARTA
                    use tarjeta_evidencia(p, carta, None, "#facc15" if p.seleccionada == carta else "#00000000")

    # ---- Conclusion ----
    text "CONCLUSIÓN: ¿quién empezó el rumor?":
        xalign 0.5
        ypos 458
        size 22
        bold True
        color "#fbf6ee"
    hbox:
        xalign 0.5
        ypos 500
        spacing 24
        for clave in p.opciones_conclusion:
            $ elegida = p.conclusion == clave
            textbutton CONCLUSIONES[clave]:
                xsize 470
                ysize 70
                background Frame("gui/telefono_boton_hover.png" if elegida else "gui/telefono_boton.png", 30, 30)
                hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                text_size 21
                text_bold elegida
                text_color ("#fde68a" if elegida and p.conclusion_ok is False else "#fbf6ee")
                text_xalign 0.5
                text_yalign 0.5
                hover_sound "assets/audio/sfx/ui_hover.wav"
                sensitive p.jugando()
                action Function(p.elegir_conclusion, clave)
    if p.explicaciones and p.jugando():
        vbox:
            xalign 0.5
            ypos 560
            for linea in p.explicaciones[:2]:
                text linea size 19 bold True color "#fca5a5" xalign 0.5 outlines [(2, "#1b1426", 0, 0)]

    text "EVIDENCIAS SOBRE LA MESA  -  arrástralas a la cadena (o haz clic en una cuenta y luego en un hueco)":
        xalign 0.5
        ypos PUZZLE_MESA_Y - 30
        size 17
        color "#c9b8d8"

    # ---- Acciones ----
    hbox:
        xalign 0.5
        ypos 900
        spacing 40
        textbutton "PISTA  (-%d s)" % int(p.costo_siguiente_pista()):
            xsize 340
            ysize 84
            background Frame("gui/telefono_boton.png", 30, 30)
            hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
            text_size 26
            text_bold True
            text_color "#fbf6ee"
            text_xalign 0.5
            text_yalign 0.5
            sensitive p.jugando() and p.fase == "cadena"
            action Function(puzzle_pista, p)
        textbutton "COMPROBAR CADENA":
            xsize 440
            ysize 84
            background Frame("gui/telefono_boton.png", 30, 30)
            hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
            insensitive_background Frame("gui/telefono_boton.png", 30, 30)
            text_size 28
            text_bold True
            text_color "#fbf6ee"
            text_insensitive_color "#8b84a8"
            text_xalign 0.5
            text_yalign 0.5
            hover_sound "assets/audio/sfx/ui_hover.wav"
            sensitive p.jugando() and p.listo()
            action Function(puzzle_comprobar, p)
    if p.jugando() and not p.listo() and p.fase == "cadena":
        text "Completa la cadena y elige una conclusión para comprobar." size 18 color "#8b84a8" xalign 0.5 ypos 992
    text "Teclado: 1-%d elige ficha  ·  Z X C colocan de izquierda a derecha  ·  H pista  ·  Enter comprueba" % len(p.cartas):
        xalign 0.5
        ypos 1030
        size 16
        color "#8b84a8"

    if p.jugando() and p.fase == "cadena":
        for i in range(len(p.cartas)):
            key "K_%d" % (i + 1) action Function(puzzle_tecla_carta, p, i)
        for i in range(p.eslabones):
            key TECLAS_HUECO[i] action Function(puzzle_tecla_hueco, p, i)
        key "K_h" action Function(puzzle_pista, p)
        if p.listo():
            key "K_RETURN" action Function(puzzle_comprobar, p)
            key "K_KP_ENTER" action Function(puzzle_comprobar, p)

    # ---- Inferencia final: de donde salio la captura viral ----
    if p.jugando() and p.fase == "inferencia":
        add Solid("#000000c0")
        frame:
            align (0.5, 0.5)
            xsize 1500
            background Frame("gui/frame.png", 30, 30)
            padding (50, 40)
            vbox:
                spacing 18
                xfill True
                text "ÚLTIMO PASO: ¿DE DÓNDE SALIÓ?" size 40 bold True color "#8c2f4b" xalign 0.5
                text "La cadena es correcta. El origen adjuntó una captura. Compárala con lo que publicó antes una fuente confiable." size 22 color "#2b2440" xalign 0.5 textalign 0.5
                hbox:
                    xalign 0.5
                    spacing 40
                    frame:
                        xsize 640
                        background Solid("#eef6f3")
                        padding (26, 20)
                        vbox:
                            spacing 8
                            text "PUBLICACIÓN ORIGINAL" size 16 bold True color "#2f9e8f" kerning 2
                            text "%s  ·  %s" % (p.caso["autor"], p.hora_fuente_real()) size 20 bold True color "#2b2440"
                            text p.caso["real"] size 22 color "#2b2440"
                    frame:
                        xsize 640
                        background Solid("#fbeef0")
                        padding (26, 20)
                        vbox:
                            spacing 8
                            text "CAPTURA QUE ADJUNTÓ EL ORIGEN" size 16 bold True color "#c0392b" kerning 2
                            text "%s  ·  %s" % (p.origen, p.hora(p.origen)) size 20 bold True color "#2b2440"
                            text p.caso["viral"] size 22 color "#2b2440"
                            text "Misma tipografía que %s. El borde inferior está cortado." % p.caso["autor"] size 17 italic True color "#8b84a8"
                text "¿Qué hizo la cuenta de origen?" size 26 bold True color "#2b2440" xalign 0.5
                hbox:
                    xalign 0.5
                    spacing 20
                    for clave in p.opciones_inferencia:
                        textbutton INFERENCIAS[clave]:
                            xsize 440
                            ysize 80
                            background Frame("gui/telefono_boton.png", 30, 30)
                            hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                            text_size 20
                            text_color "#fbf6ee"
                            text_xalign 0.5
                            text_yalign 0.5
                            text_textalign 0.5
                            hover_sound "assets/audio/sfx/ui_hover.wav"
                            action Function(puzzle_inferencia, p, clave)
                if p.explicacion_inferencia:
                    text p.explicacion_inferencia size 21 bold True color "#c0392b" xalign 0.5 textalign 0.5
                else:
                    text "Sin límite de tiempo: piénsalo con calma." size 18 color "#8b84a8" xalign 0.5

    if modo_sustentacion:
        frame:
            xpos 24
            ypos 1000
            background "#0b1324e0"
            padding (14, 8)
            text "DFS inverso desde %s: %s" % (p.inicio, "  <-  ".join(p.ruta_desde(p.inicio)[1:])) size 16 color "#93c5fd"

    # Por encima del draggroup: los drags no deben tragarse los eventos del timer.
    if p.jugando():
        timer 0.1 repeat True action Function(puzzle_tick, p)

    # ---- Intro ----
    if not p.empezado:
        add Solid("#000000b8")
        frame:
            align (0.5, 0.5)
            xsize 1040
            background Frame("gui/frame.png", 30, 30)
            padding (56, 44)
            vbox:
                spacing 16
                xfill True
                text "RASTREA EL ORIGEN DEL RUMOR" size 44 bold True color "#8c2f4b" xalign 0.5
                text "Una publicación falsa se hizo viral. Reconstruye cómo llegó hasta ahí." size 24 color "#2b2440" xalign 0.5 textalign 0.5
                null height 4
                text "1. Arrastra cuentas desde la mesa a la cadena, de derecha a izquierda (o clic, o teclado)." size 22 color "#2b2440"
                text "2. Cada cuenta debe SEGUIR a la siguiente y haber publicado ANTES que ella." size 22 color "#2b2440"
                text "3. El origen es la cuenta que publicó primero. Su ficha dice qué tipo de cuenta es." size 22 color "#2b2440"
                if p.inferencia_activa:
                    text "4. Al final, compara la captura viral con su fuente original." size 22 color "#2b2440"
                text "Tienes %d s y %d comprobaciones. Hay cuentas señuelo." % (int(p.tiempo_total), p.comprobaciones) size 22 bold True color "#c0392b" xalign 0.5
                null height 6
                textbutton "EMPEZAR":
                    style "grafo_button"
                    text_style "grafo_button_text"
                    xalign 0.5
                    xsize 360
                    text_xalign 0.5
                    action Function(p.empezar)

    # ---- Resultado ----
    if p.terminado():
        $ nota = p.calificacion()
        $ color_nota = {"S": "#facc15", "A": "#22c55e", "B": "#38bdf8", "C": "#a78bfa", "D": "#ef4444"}[nota]
        add Solid("#000000b0")
        frame:
            align (0.5, 0.5)
            xsize 980
            background ("#0b1324f5")
            padding (50, 36)
            vbox:
                spacing 12
                xfill True
                text ("¡ORIGEN ENCONTRADO!" if p.exito() else "SE PERDIÓ EL RASTRO") size 56 bold True color ("#22c55e" if p.exito() else "#ef4444") xalign 0.5
                text nota size 150 bold True color color_nota xalign 0.5 at nota_golpe
                text p.motivo_fin size 24 color "#f1f5f9" xalign 0.5 textalign 0.5
                if p.exito():
                    text "Conclusión: " + CONCLUSIONES[p.tipo_origen()] size 22 color "#fde68a" xalign 0.5
                    text "Metadato del origen: publicada desde el panel 'RSN-Scheduler', una entrada cada 7 minutos." size 19 color "#93c5fd" xalign 0.5 textalign 0.5
                    if p.inferencia_ok:
                        text "La captura viral era una publicación real de %s, recortada." % p.caso["autor"] size 19 color "#93c5fd" xalign 0.5
                else:
                    text "La historia continúa aunque el rastro se pierda." size 19 color "#cbd5e1" xalign 0.5
                hbox:
                    xalign 0.5
                    spacing 60
                    vbox:
                        text "COMPROBACIONES" size 16 color "#94a3b8" xalign 0.5
                        text "[p.comprobaciones_usadas]" size 34 bold True color "#f8fafc" xalign 0.5
                    vbox:
                        text "PISTAS" size 16 color "#94a3b8" xalign 0.5
                        text "[p.pistas_usadas]" size 34 bold True color "#f8fafc" xalign 0.5
                    vbox:
                        text "TIEMPO" size 16 color "#94a3b8" xalign 0.5
                        text "%d s" % int(min(p.transcurrido, p.tiempo_total)) size 34 bold True color "#f8fafc" xalign 0.5
                null height 8
                textbutton "CONTINUAR":
                    style "grafo_button"
                    text_style "grafo_button_text"
                    xalign 0.5
                    xsize 360
                    text_xalign 0.5
                    action Return()


label minijuego_rastreador(semilla=None, aplicar=True, ajustes=None):
    $ semilla_rastreo = semilla if semilla is not None else renpy.random.randint(1, 999999)
    $ parametros_puzzle = dict(PUZZLE_NORMAL, **(ajustes or {}))
    $ puzzle_rastreo = PuzzleEvidencias(red_civitas, semilla_rastreo, **parametros_puzzle)
    $ hud_estaba_visible = renpy.get_screen("hud_ciudad") is not None
    $ ocultar_avisos_juego()
    hide screen hud_ciudad
    $ quick_menu_previo = quick_menu
    $ quick_menu = False
    window hide
    $ renpy.block_rollback()
    call screen puzzle_rastreo_ui(puzzle_rastreo, puzzle_rastreo.caso["viral"])
    $ quick_menu = quick_menu_previo
    if hud_estaba_visible:
        show screen hud_ciudad
    $ resultado_minijuego = registrar_minijuego(puzzle_rastreo.resultado(), aplicar)
    $ renpy.block_rollback()
    return resultado_minijuego


label minijuego_rastreador_vivo(semilla=None, aplicar=True, ajustes=None):
    $ semilla_rastreo = semilla if semilla is not None else renpy.random.randint(1, 999999)
    $ rastreo = RastreoEnVivo(red_civitas, semilla_rastreo, config=ajustes)
    call jugar_arcade(rastreo, "RASTREADOR", RUMORES[semilla_rastreo % len(RUMORES)])
    $ resultado_minijuego = registrar_minijuego(rastreo.resultado(), aplicar)
    return resultado_minijuego
