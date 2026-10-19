## ACTO 3 - Viernes: el origen. Rastreador y la revelacion de NOVA.

label acto3:
    call screen titulo_acto("ACTO III  -  VIERNES", "El origen", "Todo rumor empezó en algún lugar.")
    $ avanzar_momento(inv.VIERNES)

    scene bg barrio_prensa at paneo with negro
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.5 if_changed
    show screen hud_ciudad
    show screen tarjeta_lugar("VIERNES  -  4:05 P.M.", "Distrito de Prensa")
    pause 1.2
    scene bg redaccion with suave
    show screen tarjeta_lugar("VIERNES  -  4:20 P.M.", "Redacción de Noticias Nova")
    show claudia seria at escena("claudia") with suave
    c "Alcalde, encontré el patrón. Todos los rumores de esta semana salen de una misma red."
    c "Cada mensaje rebota por tres o cuatro cuentas antes de llegar a la gente real. Así parece que lo dice todo el mundo."
    c "Si seguimos la cadena hacia atrás, llegamos a quien la empezó. Pero hay que hacerlo mientras el rumor sigue vivo."
    call eventos_momento(inv.VIERNES)

    call nueva_publicacion
    call comentario("claudia")

    c seria "Y el rumor del agua volvió a la tendencia. Esta vez lo vamos a rastrear hasta el principio."
    scene bg operaciones with suave
    show screen tarjeta_lugar("VIERNES  -  4:45 P.M.", "Centro de Operaciones")
    show claudia neutral at escena("claudia") with suave
    "Claudia te lleva al centro de operaciones. Sobre la mesa hay fichas impresas de cada cuenta que tocó el rumor."
    c "Hora de publicación, a quién sigue cada cuenta, cuántos seguidores tiene. La cadena está ahí: solo hay que ordenarla."
    c seria "Cuidado: algunas fichas son de cuentas que solo comentaron. No todas forman parte de la cadena."
    hide claudia with suave

    call minijuego_con_reintento("minijuego_rastreador", ajustes=PUZZLE_HISTORIA)
    $ resultado_rastreo = _return

    if resultado_rastreo["exito"]:
        $ nova_descubierto = True
        jump .revelacion
    else:
        scene bg operaciones with negro
        show claudia triste at escena("claudia") with suave
        c triste "Lo perdimos. La cuenta se borró justo cuando estábamos cerca."
        c seria "Pero vi algo: todas las cuentas usaban la misma etiqueta, #AntesDeQueLoBorren. Es una sola mano."
        jump .final_acto

label .revelacion:
    call giro_nova
    call abrir_civitasnet("net_nova_intervenida")
    scene bg operaciones with negro
    play music "assets/audio/music/tema_final.wav" fadein 2.0
    show claudia seria at escena("claudia") with suave
    c "Ya sabemos qué es: no inventa, amplifica. Y sabemos cuándo va a atacar."
    $ subir_afinidad("claudia", 1)
    $ aplicar_consecuencia({"info_verificada": 4, "desinformacion": -3})

label .final_acto:
    hide claudia with suave
    scene bg ciudad tarde at paneo with lento
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.5 if_changed
    call nueva_publicacion
    call nueva_publicacion
    "El viernes termina con la ciudad en vilo. Faltan dos días."
    return
