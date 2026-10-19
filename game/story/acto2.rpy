## ACTO 2 - Miercoles: el Barrio Sur. Presenta a Rodrigo y Caza-Rumores.

label acto2:
    call screen titulo_acto("ACTO II  -  MIÉRCOLES", "El Barrio Sur", "Un rumor no necesita ser cierto. Solo necesita ser rápido.")
    $ avanzar_momento(inv.MIERCOLES)
    "Miércoles, 8:15 a.m. Antes de salir, revisas CivitasNet."
    call abrir_civitasnet("net_nos_mintieron" if hay("desmintio_sin_datos") else ("net_acueducto_informe" if hay("pidio_analisis") else None))

    scene bg barrio_sur at paneo with negro
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.5 if_changed
    show screen hud_ciudad
    show screen tarjeta_lugar("MIÉRCOLES  -  10:20 A.M.", "Barrio Sur")
    "Visitas el Barrio Sur. Las calles están tranquilas.{w=0.3} Demasiado tranquilas para un miércoles."

    scene bg barrio_sur conversacion with suave
    show rodrigo enojada at escena("rodrigo") with suave
    $ reaccionar("rodrigo", "temblor")
    r enojada "¿Ahora sí viene el alcalde? ¿Ahora que todos dicen que nos van a cortar el agua?"
    r "Soy Rodrigo. Tengo una tienda en esta esquina hace quince años. Hoy vendí cero, porque la gente no sale."
    r seria "Mi hermana dice que lo leyó en Civitas. Mi vecino también. ¿Quién miente aquí?"
    if hay("desmintio_sin_datos"):
        r enojada "Y usted dijo el lunes que el agua era cien por ciento segura. Después salió que el Acueducto seguía revisando."
    elif hay("pidio_analisis"):
        r "Por lo menos usted pidió los análisis antes de hablar. Eso se comenta en el grupo del barrio."

    menu:
        "Nadie de la alcaldía ha dicho eso, Rodrigo. Mírame a los ojos.":
            $ subir_afinidad("rodrigo", 1)
            show rodrigo seria
            r seria "...Bueno. Por lo menos vino en persona. Eso ya es más que los de antes."
        "Entiendo que tengas miedo, pero no puedo responder cada chisme.":
            $ subir_afinidad("rodrigo", -1)
            show rodrigo enojada
            r enojada "¿Chisme? Para usted es un chisme. Para mí es el arriendo de este mes."

    menu:
        "¿Alguien del barrio sabe qué pasó de verdad con el agua?":
            show rodrigo seria
            r seria "Mi primo trabaja en el Acueducto. Dice que el papel ese decía 'repetir análisis', por una tubería rota en la calle 9."
            r "Nada de veneno. Pero eso no lo comparte nadie: no da miedo."
            $ dar_pista("testimonio_acueducto")
            $ subir_afinidad("rodrigo", 1, aviso=False)
        "Seguir con la visita.":
            pass

    call nueva_publicacion
    call comentario("rodrigo")
    call nueva_publicacion
    call comentario("rodrigo")
    call eventos_momento(inv.MIERCOLES)

    play sound "assets/audio/sfx/alarma_viral.wav"
    $ interferencia()
    show rodrigo sorprendida
    $ reaccionar("rodrigo", "sobresalto")
    r sorprendida "¡Mire! Mi teléfono... todos mis grupos están mandando lo mismo."
    "Un nuevo rumor explota en el Barrio Sur. Esta vez se mueve más rápido que cualquier desmentido."
    hide rodrigo with suave

    scene bg crisis with destello
    play music "assets/audio/music/tema_tension.wav" fadein 0.5
    "Si no lo frenas ahora, mañana estará en toda la ciudad."

    call minijuego_con_reintento("minijuego_contencion")
    $ resultado_contencion = _return

    scene bg barrio_sur conversacion with negro
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.5
    if resultado_contencion["exito"]:
        show rodrigo feliz at escena("rodrigo") with suave
        $ reaccionar("rodrigo", "salto")
        r feliz "Ya casi nadie lo está compartiendo. Mi hermana hasta borró lo que había mandado."
        r "No sé qué hizo, pero lo hizo rápido. Gracias, alcalde."
        $ subir_afinidad("rodrigo", 1)
    else:
        show rodrigo triste at escena("rodrigo") with suave
        r triste "Ya llegó a todos lados. Hay gente haciendo fila en el supermercado por agua."
        r "No es su culpa entera... pero alguien tiene que hacer algo antes del domingo."

    hide rodrigo with suave
    scene bg operaciones with negro
    show screen tarjeta_lugar("MIÉRCOLES  -  6:00 P.M.", "Centro de Operaciones")
    "Claudia reúne a todos en el centro de operaciones. Hay que decidir cómo responder antes de que caiga la noche."
    show rodrigo seria at escena("rodrigo", 0.83, 0.84) with suave
    show claudia seria at escena("claudia", 0.17, 0.84) with suave
    c "Alcalde, tengo datos: el rumor salió de las mismas cinco cuentas de siempre. Puedo publicar una investigación hoy."
    show martina seria at escena("martina", 0.5, 0.84) with suave
    m seria "Una investigación de veinte párrafos no la lee nadie. Déjenme hacer un live. En diez minutos lo ven cien mil."
    r seria "Yo solo quiero que alguien le hable claro a la gente del barrio."

    menu:
        "Claudia: la investigación con pruebas va primero.":
            $ confio_en = "claudia"
            $ hecho("confio_claudia")
            $ subir_afinidad("claudia", 1)
            $ aplicar_consecuencia({"info_verificada": 4, "confianza": 2})
            c feliz "Gracias. Lo voy a hacer corto y con capturas. Hasta Martina lo va a poder compartir."
            m triste "Ok... pero si nadie lo lee, después no me echen la culpa."
        "Martina: el live llega más rápido.":
            $ confio_en = "martina"
            $ hecho("confio_martina")
            $ subir_afinidad("martina", 1)
            $ aplicar_consecuencia({"desinformacion": -4, "confianza": 1})
            m feliz "¡Sí! Voy a mostrar el comunicado en pantalla y responder preguntas en vivo."
            c seria "Rápido no siempre es exacto. Voy a estar viendo, Martina."
        "Rodrigo: que hable el barrio, con su propia voz.":
            $ confio_en = "rodrigo"
            $ hecho("confio_rodrigo")
            $ subir_afinidad("rodrigo", 2)
            $ aplicar_consecuencia({"convivencia": 4, "confianza": 2})
            r sorprendida "¿Yo? ¿En Civitas? Bueno... si usted me pasa los datos, yo se los explico a mis vecinos."
            c feliz "Eso no lo había pensado. Una voz del barrio vale más que diez comunicados."

    if tiene_pista("foto_2019"):
        r triste "Y la foto de la inundación... era de 2019. Yo la reenvié a medio barrio. Qué vergüenza."
        $ aplicar_consecuencia({"conflictos": -3})
    hide claudia
    hide martina
    hide rodrigo
    with suave
    call nueva_publicacion
    return
