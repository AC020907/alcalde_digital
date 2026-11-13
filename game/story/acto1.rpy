## ACTO 1 - Lunes: el rumor del agua.
## Presenta a Tomas (rival), a Martina y el Moderador, y cierra con una escena de calma:
## Claudia cuenta lo que le paso en 2019 (se paga el miercoles con Rodrigo).

label acto1:
    call screen titulo_acto("ACTO I  -  LUNES", "El rumor del agua", "Los comentarios también son una ciudad.")
    $ avanzar_momento(inv.LUNES)

    call viajar_a_mision("lunes_plaza")
    scene bg ciudad at paneo with negro
    $ musica("conversacion")
    show screen hud_ciudad
    show screen tarjeta_lugar("LUNES  -  9:10 A.M.", "Plaza de la Alcaldía")
    "La plaza está más llena que de costumbre. Medio Ciudad Nova mira su teléfono al mismo tiempo."
    "En la esquina, alguien reparte botellas de agua con una calcomanía de campaña."

    show tomas seria at escena("tomas") with suave
    t seria "Alcalde. Buenos días, si es que lo son."
    t "Tomás Vega. Nos vamos a ver mucho esta semana, en los debates y en los afiches."
    t "La gente me pregunta por el agua. Yo no tengo respuesta, así que les doy agua. ¿Usted qué les da?"

    menu:
        "Ayúdame: digamos juntos que estamos esperando los análisis.":
            $ hecho("tomas_saludo")
            $ calidad_decision("lunes_tomas", 1.0)
            $ subir_afinidad("tomas", 1)
            show tomas sorprendida
            t sorprendida "¿Juntos? A seis días de la elección."
            t seria "...No le prometo nada. Pero no voy a decir que el agua está envenenada. Eso sí se lo prometo."
        "Repartir botellas le da la razón al rumor, Tomás.":
            $ hecho("tomas_desaire")
            $ calidad_decision("lunes_tomas", 0.6)
            $ subir_afinidad("tomas", -1)
            show tomas enojada
            $ reaccionar("tomas", "temblor")
            t enojada "Puede que tenga razón."
            t seria "Pero dígamelo en privado, no delante de los vecinos. Así no vamos a llegar lejos, usted y yo."
        "Ignorarlo y hablar con la gente de la fila.":
            $ calidad_decision("lunes_tomas", 0.5)
            show tomas seria
            t "Ya veo. Cada quien con su público."

    hide tomas with suave
    call nueva_publicacion
    call comentario("claudia")
    $ completar_mision("lunes_plaza")

    call viajar_a_mision("lunes_martina")
    scene bg estudio_martina with negro
    show screen tarjeta_lugar("LUNES  -  11:30 A.M.", "Estudio de Martina")
    "Un mensaje directo te cita en un estudio lleno de luces de anillo, cámaras y peluches."
    show martina feliz at escena("martina") with suave
    m feliz "¡Alcalde! Pase, pase. No pise el cable, que se cae el aro de luz y me muero."
    m "Soy Martina, @martina.sol. Trescientos mil seguidores. Si yo digo que el agua está bien, la ciudad se calma en una hora."
    show martina seria
    m seria "El problema... es que anoche subí una historia preguntando si era cierto lo del agua."
    m "Solo una pregunta, con un emoji. Ahora mis comentarios son un basurero de bots y la gente cree que yo lo confirmé."
    m triste "Mi mamá me escribió a las cinco de la mañana para preguntarme si podía bañar a mi hermanito."

    menu:
        "Una pregunta con trescientos mil seguidores no es solo una pregunta.":
            $ subir_afinidad("martina", -1)
            show martina triste
            m triste "...Lo sé. Por eso lo llamé. No es fácil admitirlo frente al alcalde."
        "Entonces arreglémoslo juntos.":
            $ subir_afinidad("martina", 1)
            show martina feliz
            $ reaccionar("martina", "salto")
            m feliz "¿En serio? Ok. Me cae mejor de lo que dicen en los comentarios."

    m seria "Tengo acceso de moderadora para mi equipo. Si me ayuda a limpiar esto, publico un desmentido con datos."
    m "Pero ojo: hay gente que me critica de verdad. Si borramos eso, nos acusan de censura y el rumor gana."
    call eventos_momento(inv.LUNES)

    call minijuego_con_reintento("minijuego_moderador")
    $ resultado_moderador = _return
    $ completar_mision("lunes_martina")
    $ musica("conversacion")

    if resultado_moderador["exito"]:
        show martina feliz at escena("martina") with suave
        $ reaccionar("martina", "salto")
        m feliz "¡Mire eso! Comentarios limpios y nadie puede decir que censuramos a nadie."
        m "Ya subí el desmentido con el comunicado del Acueducto. Tres mil reposts y subiendo."
        m seria "Es raro. Es la primera vez que algo mío se comparte porque es verdad y no porque da rabia."
        $ subir_afinidad("martina", 1)
    else:
        show martina triste at escena("martina") with suave
        m triste "Se nos colaron demasiados... y borramos a gente real. Ya hay capturas diciendo que censuro."
        m "Voy a pedir disculpas en vivo. No es el lunes que quería."

    hide martina with suave
    call nueva_publicacion
    call comentario("martina")
    call nueva_publicacion

    call viajar_a_mision("lunes_noche")
    scene bg ciudad noche at paneo with lento
    $ musica("calma", fadein=2.5)
    show screen tarjeta_lugar("LUNES  -  11:48 P.M.", "Balcón de la Alcaldía")
    "Desde el balcón, Ciudad Nova parece tranquila. Las ventanas encendidas son pantallas de teléfono."
    show claudia seria at escena("claudia") with suave
    c "Primer día. Seguimos vivos."
    c "Revisé la cuenta @verdad.oculta otra vez. Publica cada siete minutos exactos.{w=0.3} Ni un segundo más, ni uno menos."
    tu "Nadie escribe así."
    c "No.{w=0.4} Nadie humano."
    $ dar_pista("intervalo_7min")
    if hay("moderacion_fallida"):
        c seria "Y las cuentas de NOVA ya usan las capturas de los comentarios borrados de Martina. Nada se desperdicia con ellos."
    elif hay("moderacion_limpia"):
        c "Lo de Martina ayudó. Su desmentido tiene más reposts que el rumor. Eso casi nunca pasa."

    pause 0.6
    show claudia neutral
    c neutral "El lunes le dije que acepté ayudarlo para saber quién está detrás. No era toda la verdad."
    c "En 2019, durante la inundación, yo trabajaba en el turno de noche de Noticias Nova."
    c "Llegó una foto: una familia del Barrio Sur en un techo, rodeada de agua. Cuarenta mil personas la compartían. La publiqué en diez minutos."
    c triste "La foto era de otro año, de otra ciudad. Esa familia existía, pero nunca estuvo en ese techo."
    c "Les escribieron durante meses. Que eran actores. Que pedían plata. Que mentían para robar ayudas."
    c "{cps=24}Desde entonces no publico nada que no haya comprobado dos veces. Ni un 'buenos días'.{/cps}"
    $ hecho("claudia_conto_2019")
    $ dar_pista("archivo_2019")

    menu:
        "Te equivocaste. Y desde entonces verificas como nadie en esta ciudad.":
            $ subir_afinidad("claudia", 1)
            show claudia feliz
            c feliz "...No esperaba que me lo dijera así. Gracias."
            c seria "Pero no me lo diga muy seguido. Me vuelvo insoportable."
        "Todos hemos compartido algo sin revisar alguna vez.":
            show claudia seria
            c seria "Sí. Pero no todos tenían cuarenta mil lectores esa noche."
            c "No se lo cuento para que me consuele. Se lo cuento para que sepa por qué voy a ser dura con usted."
        "¿Supiste algo más de esa familia?":
            $ subir_afinidad("claudia", 1, aviso=False)
            show claudia triste
            c triste "Les escribí una carta. Nunca contestaron."
            c "El padre tenía una tienda, creo. En el Barrio Sur. Nunca me animé a ir."

    c neutral "Váyase a dormir, alcalde. Mañana el rumor va a tener hambre otra vez."
    hide claudia with suave
    $ completar_mision("lunes_noche")
    return
