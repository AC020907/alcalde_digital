## ACTO 1 - Lunes: el rumor del agua. Presenta a Martina y el Moderador.

label acto1:
    call screen titulo_acto("ACTO I  -  LUNES", "El rumor del agua", "Los comentarios también son una ciudad.")
    $ avanzar_momento(inv.LUNES)

    scene bg ciudad at paneo with negro
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.5 if_changed
    show screen hud_ciudad
    show screen tarjeta_lugar("LUNES  -  9:10 A.M.", "Plaza de la Alcaldía")
    "La plaza está más llena que de costumbre. Medio Ciudad Nova mira su teléfono al mismo tiempo."

    call nueva_publicacion
    call comentario("claudia")

    scene bg estudio_martina with negro
    show screen tarjeta_lugar("LUNES  -  11:30 A.M.", "Estudio de Martina")
    "Un mensaje directo te cita en un estudio lleno de luces, cámaras y peluches."
    show martina feliz at escena("martina") with suave
    m feliz "¡Alcalde! Por fin. Soy Martina, @martina.sol. Seguro me ha visto en Civitas."
    m "Trescientos mil seguidores. Si yo digo que el agua está bien, la ciudad se calma en una hora."
    show martina seria
    m seria "El problema... es que ayer subí una historia preguntando si era cierto lo del agua."
    m "Solo una pregunta. Pero ahora mis comentarios son un basurero de bots y la gente cree que yo confirmé el rumor."

    menu:
        "Una pregunta con trescientos mil seguidores no es solo una pregunta.":
            $ subir_afinidad("martina", -1)
            show martina triste
            m triste "...Lo sé. Por eso vine. No es fácil admitirlo frente al alcalde."
        "Entonces arreglémoslo juntos.":
            $ subir_afinidad("martina", 1)
            show martina feliz
            $ reaccionar("martina", "salto")
            m feliz "¿En serio? Ok. Me cae mejor de lo que dicen en Twitter... digo, en Civitas."

    m "Tengo acceso de moderador para mi equipo. Si me ayuda a limpiar los comentarios, publico un desmentido con datos."
    m seria "Pero ojo: hay gente que me critica de verdad. Si borramos eso, nos acusan de censura y el rumor gana."
    call eventos_momento(inv.LUNES)

    call minijuego_con_reintento("minijuego_moderador")
    $ resultado_moderador = _return
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.0 if_changed

    if resultado_moderador["exito"]:
        show martina feliz at escena("martina") with suave
        $ reaccionar("martina", "salto")
        m feliz "¡Mira eso! Comentarios limpios y nadie puede decir que censuramos críticas."
        m "Ya subí el desmentido con el comunicado del acueducto. Tres mil reposts y subiendo."
        $ subir_afinidad("martina", 1)
    else:
        show martina triste at escena("martina") with suave
        m triste "Se nos colaron demasiados... y borramos a gente real. Ya hay capturas diciendo que censuro."
        m "Voy a pedir disculpas en vivo. No es el lunes que quería."

    hide martina with suave
    call nueva_publicacion
    call comentario("martina")
    call nueva_publicacion

    scene bg ciudad noche at paneo with lento
    play music "assets/audio/music/tema_final.wav" fadein 2.0
    show screen tarjeta_lugar("LUNES  -  11:48 P.M.", "Balcón de la Alcaldía")
    show claudia seria at escena("claudia") with suave
    c "Primer día. Seguimos vivos."
    c "Revisé la cuenta @verdad.oculta otra vez. Publica cada siete minutos exactos.{w=0.3} Ni un segundo más, ni uno menos."
    tu "Nadie escribe así."
    c "No.{w=0.4} Nadie humano."
    $ dar_pista("intervalo_7min")
    if hay("moderacion_fallida"):
        c seria "Y mire CivitasNet: las cuentas de NOVA ya usan las capturas de los comentarios borrados de Martina."
    elif hay("moderacion_limpia"):
        c "Lo de Martina ayudó. Su desmentido tiene más reposts que el rumor. Eso casi nunca pasa."
    hide claudia with suave
    return
