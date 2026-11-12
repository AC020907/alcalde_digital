## ACTO 2 - Miercoles: el Barrio Sur.
## Rodrigo y su tienda (la familia de la foto de 2019), Caza-Rumores, el encuentro con Claudia
## y, de noche, la oferta de Resonancia a Martina (cambia el domingo y el expediente).

label acto2:
    call screen titulo_acto("ACTO II  -  MIÉRCOLES", "El Barrio Sur", "Un rumor no necesita ser cierto. Solo necesita ser rápido.")
    $ avanzar_momento(inv.MIERCOLES)
    "Miércoles, 8:15 a.m. Antes de salir, revisas CivitasNet."
    call abrir_civitasnet("net_nos_mintieron" if hay("desmintio_sin_datos") else ("net_acueducto_informe" if hay("pidio_analisis") else None))

    call viajar_a_mision("mie_barrio_sur")
    scene bg barrio_sur at paneo with negro
    $ musica("conversacion")
    show screen hud_ciudad
    show screen tarjeta_lugar("MIÉRCOLES  -  10:20 A.M.", "Barrio Sur")
    "Las calles del Barrio Sur están tranquilas.{w=0.3} Demasiado tranquilas para un miércoles."

    scene bg barrio_sur conversacion with suave
    show rodrigo enojada at escena("rodrigo") with suave
    $ reaccionar("rodrigo", "temblor")
    r enojada "¿Ahora sí viene el alcalde? ¿Ahora que todos dicen que nos van a cortar el agua?"
    r "Rodrigo. Tengo la tienda de esta esquina hace quince años. Hoy vendí cero, porque la gente no sale de la casa."
    r seria "Mi hermana dice que lo leyó en Civitas. Mi vecino también. ¿Quién miente aquí?"
    if hay("desmintio_sin_datos"):
        r enojada "Y usted dijo el lunes que el agua era cien por ciento segura. Después salió que el Acueducto seguía revisando."
    elif hay("pidio_analisis"):
        r "Por lo menos usted pidió los análisis antes de hablar. Eso se comenta en el grupo del barrio."

    menu:
        "Nadie de la alcaldía ha dicho eso, Rodrigo. Vine a escucharte.":
            $ subir_afinidad("rodrigo", 1)
            show rodrigo seria
            r seria "...Bueno. Por lo menos vino en persona. Eso ya es más que los de antes."
        "Entiendo que tengas miedo, pero no puedo responder cada chisme.":
            $ subir_afinidad("rodrigo", -1)
            show rodrigo enojada
            r enojada "¿Chisme? Para usted es un chisme. Para mí es el arriendo de este mes."

    ## Escena de calma: la tienda, el cafe y la foto de 2019.
    $ musica("calma", fadein=2.0)
    "Rodrigo levanta la persiana a medias y te hace pasar. Huele a café recalentado y a cartón mojado."
    show rodrigo neutral
    r neutral "Siéntese. Tinto no le puedo negar a nadie, ni al alcalde."
    r "Mi hija Lucía dice que todo lo de Civitas hay que revisarlo. Tiene diecisiete. Me manda capturas con círculos rojos."
    r triste "Yo no confío en la alcaldía desde 2019. En la inundación nos dejaron solos tres días."
    r "Y encima una periodista publicó una foto de mi esposa y de Lucía en un techo, diciendo que estaban atrapadas ese día."
    r "La foto era vieja. Pero a ellas las insultaron durante meses. Que eran actrices. Que pedían plata."

    menu:
        "Esa periodista... se llama Claudia Reyes, ¿verdad?" if hay("claudia_conto_2019"):
            show rodrigo sorprendida
            $ reaccionar("rodrigo", "sobresalto")
            r sorprendida "¿Usted la conoce?"
            tu "Trabaja conmigo esta semana. Me lo contó anoche. Nunca se lo perdonó."
            r seria "...Nunca se lo perdonó. Mire usted. Nosotros tampoco."
            $ hecho("rodrigo_disculpa_2019")
        "En 2019 la alcaldía les falló. Lo siento, de verdad.":
            $ subir_afinidad("rodrigo", 1)
            $ calidad_decision("mie_rodrigo", 1.0)
            show rodrigo seria
            r seria "Nadie de allá arriba me había dicho eso en cinco años."
        "Eso fue otra administración.":
            $ subir_afinidad("rodrigo", -1)
            $ calidad_decision("mie_rodrigo", 0.3)
            show rodrigo enojada
            r enojada "Para nosotros la alcaldía es una sola. Cambian los afiches, no los huecos."

    show rodrigo seria
    menu:
        "¿Alguien del barrio sabe qué pasó de verdad con el agua?":
            r seria "Mi primo trabaja en el Acueducto. Dice que el papel ese decía 'repetir análisis', por una tubería rota en la calle 9."
            r "Nada de veneno. Pero eso no lo comparte nadie: no da miedo."
            $ dar_pista("testimonio_acueducto")
            $ subir_afinidad("rodrigo", 1, aviso=False)
        "Seguir con la visita.":
            pass

    $ musica("conversacion")
    call nueva_publicacion
    call comentario("rodrigo")
    call nueva_publicacion
    call comentario("rodrigo")
    call eventos_momento(inv.MIERCOLES)

    $ sfx("alarma")
    $ interferencia()
    show rodrigo sorprendida
    $ reaccionar("rodrigo", "sobresalto")
    r sorprendida "¡Mire! El teléfono de Lucía... todos sus grupos están mandando lo mismo."
    "Un nuevo rumor explota en el Barrio Sur. Esta vez se mueve más rápido que cualquier desmentido."
    hide rodrigo with suave

    scene bg crisis with destello
    $ musica("crisis", fadein=0.5)
    "Si no lo frenas ahora, mañana estará en toda la ciudad."

    call minijuego_con_reintento("minijuego_contencion")
    $ resultado_contencion = _return
    $ completar_mision("mie_barrio_sur")

    scene bg barrio_sur conversacion with negro
    $ musica("conversacion")
    if resultado_contencion["exito"]:
        show rodrigo feliz at escena("rodrigo") with suave
        $ reaccionar("rodrigo", "salto")
        r feliz "Ya casi nadie lo está compartiendo. Mi hermana hasta borró lo que había mandado."
        r "Lucía dice que usted 'cortó la cadena'. No sé qué significa, pero lo dijo con orgullo."
        $ subir_afinidad("rodrigo", 1)
    else:
        show rodrigo triste at escena("rodrigo") with suave
        r triste "Ya llegó a todos lados. Hay gente haciendo fila en el supermercado por agua."
        r "No es su culpa entera... pero alguien tiene que hacer algo antes del domingo."

    hide rodrigo with suave
    call viajar_a_mision("mie_operaciones")
    scene bg operaciones with negro
    show screen tarjeta_lugar("MIÉRCOLES  -  6:00 P.M.", "Centro de Operaciones")
    "Claudia reúne a todos en el centro de operaciones. Hay que decidir cómo responder antes de que caiga la noche."
    show rodrigo seria at escena("rodrigo", 0.83, 0.84) with suave
    show claudia seria at escena("claudia", 0.17, 0.84) with suave

    if hay("rodrigo_disculpa_2019"):
        $ musica("calma")
        "Rodrigo y Claudia se reconocen en el mismo instante. Nadie dice nada durante un rato largo."
        c triste "Usted es el señor de la tienda. El esposo de..."
        r seria "De la mujer del techo. Sí."
        menu:
            "Claudia, creo que le debes algo a Rodrigo.":
                c triste "Cinco años tarde. Perdóneme, Rodrigo. Publiqué la foto de su familia sin comprobar nada. Lo que vino después fue culpa mía."
                r triste "...Lucía todavía guarda los mensajes. Se los voy a enseñar algún día, para que sepa lo que hizo."
                r seria "Pero esta semana usted pidió pruebas antes que nadie. Eso también se lo voy a contar."
                $ subir_afinidad("claudia", 1)
                $ subir_afinidad("rodrigo", 1)
                $ calidad_decision("mie_reencuentro", 1.0)
            "No es el momento. Tenemos un rumor que frenar.":
                c seria "Tiene razón. Después hablamos, Rodrigo. Se lo debo."
                r seria "Después. Siempre después."
                $ calidad_decision("mie_reencuentro", 0.5)
        $ musica("conversacion")

    c "Alcalde, tengo datos: el rumor salió de las mismas cinco cuentas de siempre. Puedo publicar una investigación hoy."
    show martina seria at escena("martina", 0.5, 0.84) with suave
    m seria "Una investigación de veinte párrafos no la lee nadie. Déjenme hacer un live. En diez minutos lo ven cien mil."
    r seria "Yo solo quiero que alguien le hable claro a la gente del barrio."

    menu:
        "Claudia: la investigación con pruebas va primero.":
            $ confio_en = "claudia"
            $ hecho("confio_claudia")
            $ calidad_decision("mie_operaciones", 0.9)
            $ subir_afinidad("claudia", 1)
            $ aplicar_consecuencia({"info_verificada": 4, "confianza": 2})
            c feliz "Gracias. Lo voy a hacer corto y con capturas. Hasta Martina lo va a poder compartir."
            m triste "Ok... pero si nadie lo lee, después no me echen la culpa."
        "Martina: el live llega más rápido.":
            $ confio_en = "martina"
            $ hecho("confio_martina")
            $ calidad_decision("mie_operaciones", 0.8)
            $ subir_afinidad("martina", 1)
            $ aplicar_consecuencia({"desinformacion": -4, "confianza": 1})
            m feliz "¡Sí! Voy a mostrar el comunicado en pantalla y responder preguntas en vivo."
            c seria "Rápido no siempre es exacto. Voy a estar viendo, Martina."
        "Rodrigo: que hable el barrio, con su propia voz.":
            $ confio_en = "rodrigo"
            $ hecho("confio_rodrigo")
            $ calidad_decision("mie_operaciones", 1.0)
            $ subir_afinidad("rodrigo", 2)
            $ aplicar_consecuencia({"convivencia": 4, "confianza": 2})
            r sorprendida "¿Yo? ¿En Civitas? Bueno... si usted me pasa los datos, Lucía me ayuda con el teléfono."
            c feliz "Eso no lo había pensado. Una voz del barrio vale más que diez comunicados."

    if tiene_pista("foto_2019"):
        r triste "Y la foto de la inundación que circuló hoy... era de 2019. Yo la reenvié a medio barrio sin mirarla."
        if hay("claudia_conto_2019"):
            c triste "Es la misma foto. La mía. Alguien la guardó cinco años para volver a usarla."
        $ aplicar_consecuencia({"conflictos": -3})
    hide claudia
    hide martina
    hide rodrigo
    with suave
    call nueva_publicacion
    $ completar_mision("mie_operaciones")

    call oferta_resonancia
    return


## Miercoles de noche: Resonancia le ofrece dinero a Martina. Su respuesta cambia el domingo.
label oferta_resonancia(corto=False):
    scene bg ciudad noche at paneo with negro
    $ musica("calma", fadein=2.0)
    show screen tarjeta_lugar("MIÉRCOLES  -  9:40 P.M.", "Videollamada")
    "Tu teléfono vibra. Videollamada de @martina.sol. Está sin maquillaje y sin el aro de luz."
    show martina seria at escena("martina") with suave
    m seria "Perdón por la hora. No sabía a quién más llamar."
    m "Me escribió una consultora, Resonancia. Me ofrecen cuatro millones por promocionar su 'servicio de verificación'."
    m "Solo tengo que decir que ellos revisan las noticias por mí... y usar la etiqueta #AntesDeQueLoBorren en los videos."
    if tiene_pista("anuncio_resonancia"):
        tu "Es la misma etiqueta de todos los rumores. Y la misma consultora que se anuncia una hora después de cada crisis."
        m sorprendida "¿Qué? ¿Está seguro?"
    if not corto:
        m triste "Cuatro millones es el arriendo del estudio de un año. Esta semana perdí veinte mil seguidores."
        m "No soy tonta. Sé que algo huele raro. Pero también sé que nadie me va a pagar por decir la verdad."

    menu:
        "Publícalo, Martina. Con la captura y el remitente.":
            $ hecho("martina_rechazo_resonancia")
            $ hecho("martina_expuso_oferta")
            $ calidad_decision("mie_oferta", 1.0)
            $ subir_afinidad("martina", 2)
            show martina sorprendida
            m sorprendida "¿Exponerlos? Me van a llenar de bots hasta el lunes."
            show martina seria
            m seria "...Pero si me van a llenar de bots igual, por lo menos que sea por algo que valga la pena."
            m feliz "Ok. Subo la captura completa, con el correo y todo. Que la gente lo vea."
            $ dar_pista("oferta_resonancia")
        "Recházalo, pero no hagas ruido. No te expongas.":
            $ hecho("martina_rechazo_resonancia")
            $ calidad_decision("mie_oferta", 0.7)
            $ subir_afinidad("martina", 1)
            show martina seria
            m seria "Ok. Les digo que no y borro el mensaje. Ojalá no me arrepienta."
        "Es tu decisión. Es tu trabajo, no el mío.":
            $ calidad_decision("mie_oferta", 0.4)
            if afinidad.get("martina", 0) >= 2:
                $ hecho("martina_rechazo_resonancia")
                show martina seria
                m seria "Mi decisión... Entonces es no. Usted me hizo pensar esta semana, aunque no quiera admitirlo."
            else:
                $ hecho("martina_acepto_resonancia")
                show martina triste
                m triste "Ya. Gracias por nada, entonces."
                m "Voy a aceptar. Por lo menos ellos sí contestan los mensajes."
        "Acéptalo. Vamos a necesitar ese alcance el domingo.":
            $ hecho("martina_acepto_resonancia")
            $ calidad_decision("mie_oferta", 0.0)
            $ subir_afinidad("martina", -1)
            show martina triste
            m triste "...Sí. Supongo que todos usamos a todos, ¿no?"
            m "Buenas noches, alcalde."

    hide martina with suave
    return
