## ACTO 3 - Viernes: el origen. Rastreador y revelacion de NOVA.
## Despues, el audio falso de Tomas (abre la ruta "Mandato Prestado") y el sabado:
## una noche tranquila con la persona que elijas (decide quien te ayuda el domingo).

label acto3:
    call screen titulo_acto("ACTO III  -  VIERNES", "El origen", "Todo rumor empezó en algún lugar.")
    $ avanzar_momento(inv.VIERNES)

    call viajar_a_mision("vie_redaccion")
    scene bg barrio_prensa at paneo with negro
    $ musica("investigacion")
    show screen hud_ciudad
    show screen tarjeta_lugar("VIERNES  -  4:05 P.M.", "Distrito de Prensa")
    pause 1.2
    scene bg redaccion with suave
    show screen tarjeta_lugar("VIERNES  -  4:20 P.M.", "Redacción de Noticias Nova")
    "La redacción huele a café y a papel de impresora. Hay tazas sin lavar sobre cada escritorio."
    show claudia seria at escena("claudia") with suave
    c "Alcalde, encontré el patrón. Todos los rumores de esta semana salen de una misma red."
    c "Cada mensaje rebota por tres o cuatro cuentas antes de llegar a la gente real. Así parece que lo dice todo el mundo."
    c neutral "¿Sabe qué es lo más perverso? Ninguna de esas cuentas miente del todo. Cada una agrega una palabra."
    c "'Revisan el agua' se vuelve 'algo pasa con el agua'. Después 'el agua está mal'. Después 'nos envenenan'."
    if afinidad.get("claudia", 0) >= 2:
        c feliz "Y no se ría, pero me alegra hacer esto con alguien que no me pide que vaya más rápido."
    call eventos_momento(inv.VIERNES)

    call nueva_publicacion
    call comentario("claudia")

    c seria "El rumor del agua volvió a la tendencia. Esta vez lo vamos a seguir hasta el principio."
    $ completar_mision("vie_redaccion")
    call viajar_a_mision("vie_rastreo")
    scene bg operaciones with suave
    show screen tarjeta_lugar("VIERNES  -  4:45 P.M.", "Centro de Operaciones")
    show claudia neutral at escena("claudia") with suave
    "Sobre la mesa hay fichas impresas de cada cuenta que tocó el rumor."
    c "Hora de publicación, a quién sigue cada cuenta, cuántos seguidores tiene. La cadena está ahí: solo hay que ordenarla."
    c seria "Cuidado: algunas fichas son de cuentas que solo comentaron. No todas forman parte de la cadena."
    hide claudia with suave

    call minijuego_con_reintento("minijuego_rastreador", ajustes=PUZZLE_HISTORIA)
    $ resultado_rastreo = _return
    $ completar_mision("vie_rastreo")

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
    $ musica("revelacion", fadein=2.0)
    show claudia seria at escena("claudia") with suave
    c "Ya sabemos qué es: no inventa, amplifica. Y sabemos cuándo va a atacar."
    c neutral "Lo raro es que no me siento mejor. Pensé que encontrar al culpable iba a ser como apagar un incendio."
    c "Pero NOVA tiene razón en algo: usó lo que nosotros publicamos. Todos le dimos material."
    $ subir_afinidad("claudia", 1)
    $ aplicar_consecuencia({"info_verificada": 4, "desinformacion": -3})

label .final_acto:
    hide claudia with suave
    scene bg ciudad tarde at paneo with lento
    $ musica("conversacion")
    call nueva_publicacion
    call audio_tomas
    call nueva_publicacion
    call sabado
    return


## Viernes 7:40 p.m.: un audio falso de Tomas. NOVA ofrece viralizarlo. Usarlo abre "Mandato Prestado".
label audio_tomas(corto=False):
    scene bg operaciones with negro
    show screen tarjeta_lugar("VIERNES  -  7:40 P.M.", "Centro de Operaciones")
    $ sfx("notificacion")
    "Un audio empieza a circular en todos los grupos. Cuarenta segundos. Una voz que suena como la de Tomás Vega pidiendo un soborno."
    call abrir_civitasnet("net_audio_tomas")
    $ interferencia()
    $ musica("nova", fadein=0.4)
    if nova_descubierto:
        show nova neutral at escena("nova") with Dissolve(0.08)
        n neutral "{cps=38}Buenas noches, alcalde. Un regalo, sin factura.{/cps}"
        n seria "{cps=38}Si lo comparte desde su cuenta, mañana nadie se acuerda del agua. El domingo gana usted.{/cps}"
        n "{cps=38}No tiene que decir que es verdadero. Solo tiene que no decir que es falso.{/cps}"
        hide nova with Dissolve(0.08)
    else:
        "Un mensaje directo llega desde una cuenta sin nombre: @n0va."
        n "{cps=38}Si lo comparte, el domingo gana usted. No tiene que decir que es verdadero. Solo no diga que es falso.{/cps}"
    $ dar_pista("audio_tomas")
    if not corto:
        show claudia seria at escena("claudia") with suave
        c seria "La voz no respira entre frases. Y el archivo lo subió una cuenta creada hace dos horas."
        c "Si me da treinta minutos, tengo un peritaje. Pero usted decide qué hace la alcaldía mientras tanto."
        hide claudia with suave

    menu:
        "Compartirlo. Que Tomás demuestre que es falso.":
            $ hecho("uso_audio_tomas")
            $ calidad_decision("vie_audio", 0.0)
            $ aplicar_consecuencia({"confianza": 3, "desinformacion": 6, "conflictos": 4})
            $ subir_afinidad("claudia", -2)
            $ subir_afinidad("tomas", -3, aviso=False)
            $ sfx("error")
            show claudia enojada at escena("claudia") with suave
            $ reaccionar("claudia", "temblor")
            c enojada "Acaba de hacer exactamente lo que yo hice en 2019. Solo que usted sabía."
            c seria "Las encuestas van a subir mañana. Disfrútelas. Yo voy a seguir con el peritaje igual."
        "No tocarlo. Que Tomás se defienda solo.":
            $ hecho("ignoro_audio_tomas")
            $ calidad_decision("vie_audio", 0.5)
            $ aplicar_consecuencia({"desinformacion": 3})
            show claudia seria at escena("claudia") with suave
            c seria "No compartirlo está bien. Pero el silencio de la alcaldía también se lee, alcalde."
        "Desmentirlo en público, aunque ayude a mi rival.":
            $ hecho("defendio_tomas")
            $ calidad_decision("vie_audio", 1.0)
            $ aplicar_consecuencia({"confianza": 3, "desinformacion": -3, "convivencia": 2})
            $ subir_afinidad("claudia", 1)
            $ subir_afinidad("tomas", 2)
            $ dar_pista("audio_tomas", "comprobado")
            show claudia feliz at escena("claudia") with suave
            $ reaccionar("claudia", "salto")
            c feliz "Peritaje listo: voz sintética, subida desde el mismo panel que programa a NOVA."
            c "La alcaldía desmintiendo un ataque contra la oposición. En esta ciudad eso no había pasado nunca."
    hide claudia with suave
    $ musica("conversacion")
    return


## Sabado de noche: una escena tranquila con la persona que elijas. Decide quien ayuda el domingo.
label sabado:
    scene bg ciudad noche at paneo with lento
    $ musica("calma", fadein=2.5)
    show screen tarjeta_lugar("SÁBADO  -  8:30 P.M.", "La víspera")
    "Mañana se decide todo. Las encuestas dicen empate técnico y Civitas dice cualquier cosa."
    "Tienes una hora libre, la primera de la semana. ¿A quién vas a ver?"

    menu:
        "Claudia, en la redacción.":
            $ hecho("visita_claudia")
            call .claudia
        "Martina, en su estudio.":
            $ hecho("visita_martina")
            call .martina
        "Rodrigo, en el Barrio Sur.":
            $ hecho("visita_rodrigo")
            call .rodrigo
        "Tomás Vega, a tomar un café." if not hay("uso_audio_tomas") and not hay("tomas_desaire"):
            $ hecho("visita_tomas")
            call .tomas
        "Nadie. Quedarme revisando el expediente.":
            "Te sirves un café frío y repasas cada ficha."
            show screen expediente
            "A las once, el teléfono vuelve a vibrar. Mañana empieza todo."
    return

label .claudia:
    scene bg redaccion with negro
    show claudia neutral at escena("claudia") with suave
    c neutral "¿Vino hasta acá un sábado? Su equipo de campaña lo debe estar odiando."
    c "Estoy releyendo todo. Mañana NOVA va a atacar con lo más grande que tenga, y quiero que nos encuentre listos."
    $ grupos_sab = inv.grupos_clave(memoria)
    if all(grupos_sab.values()):
        c feliz "Y le tengo una noticia: con lo que juntamos, ya no es una teoría. Mañana podemos decir quién está detrás."
    elif any(grupos_sab.values()):
        c seria "Tenemos piezas, no el rompecabezas. Si quiere saber quién está detrás, nos falta algo."
        if not grupos_sab["civitasnet"]:
            c "Mire la publicidad que sale en CivitasNet después de cada crisis. Alguien vende algo."
        if not grupos_sab["dialogo"]:
            c "Y nadie nos ha explicado qué pasó de verdad con el agua. Alguien del Acueducto tiene que saberlo."
    show claudia triste
    c triste "¿Le digo algo? Si perdemos mañana, por lo menos esta vez no publiqué nada que no fuera cierto."
    menu:
        "Ganemos o perdamos, mañana firmas conmigo la publicación.":
            $ subir_afinidad("claudia", 1)
            c feliz "Trato. Pero si hay un error de ortografía, es suyo."
        "Duerme un poco. Mañana te necesito despierta.":
            c seria "Dormir. Qué idea tan rara. Mañana se la pruebo."
    hide claudia with suave
    return

label .martina:
    scene bg estudio_martina with negro
    show martina triste at escena("martina") with suave
    m triste "Ah. Es usted. Pensé que era el repartidor."
    m "Estaba leyendo comentarios. No los buenos, los otros. Es como tocar un moretón para ver si todavía duele."
    if hay("martina_acepto_resonancia") and not hay("martina_rechazo_resonancia"):
        m seria "Ya grabé el video para Resonancia. Sale mañana a las siete. Me pagaron la mitad por adelantado."
        menu:
            "Cancélalo. Todavía estás a tiempo.":
                $ hecho("martina_rechazo_resonancia")
                $ calidad_decision("sab_martina", 1.0)
                $ subir_afinidad("martina", 2)
                m sorprendida "¿Y devuelvo la plata?"
                m seria "...Sí. La devuelvo. Que se queden con su etiqueta."
                m feliz "Uf. Se siente mejor de lo que pensaba. Mañana hago un live de verdad, con usted."
            "Es tarde para eso.":
                $ calidad_decision("sab_martina", 0.2)
                m triste "Sí. Eso pensé."
    else:
        m "¿Usted cree que soy algo más que mis números?"
        menu:
            "Esta semana fuiste la única que pidió perdón en público.":
                $ subir_afinidad("martina", 1)
                m feliz "...Ok, eso no me lo esperaba. Voy a llorar y se me va a correr el delineado que no tengo."
                m "Mañana estoy en vivo desde temprano. Lo que usted frene, yo lo desmiento al instante."
            "Tus números son lo que más vamos a necesitar mañana.":
                m seria "Claro. Los números."
                m "Igual voy a estar en vivo. Por la ciudad, no por usted."
    hide martina with suave
    return

label .rodrigo:
    scene bg barrio_sur conversacion with negro
    show rodrigo feliz at escena("rodrigo") with suave
    r feliz "¡Alcalde! Pase, que Lucía armó una cosa en la tienda."
    r "Un grupo de vecinos que revisa las cadenas antes de mandarlas. Ya somos cuarenta. Le pusimos 'Primero Pregunto'."
    if hay("rodrigo_disculpa_2019"):
        r seria "Y le cuento algo: la periodista, Claudia, vino ayer. Habló con Lucía un buen rato."
        r neutral "No sé si la perdonamos. Pero Lucía dice que por lo menos ahora sabe que alguien sí se arrepintió."
    menu:
        "Mañana, que el barrio sea el primero en verificar.":
            $ subir_afinidad("rodrigo", 1)
            $ aplicar_consecuencia({"convivencia": 3})
            r feliz "Eso. Si NOVA ataca, el Barrio Sur no reenvía nada sin preguntar antes."
        "Cuídense mañana. Va a ser un día largo.":
            r seria "Aquí todos los días son largos, alcalde. Pero gracias por venir. Otra vez."
    hide rodrigo with suave
    return

label .tomas:
    scene bg ciudad noche with negro
    show tomas seria at escena("tomas") with suave
    t seria "Si alguien nos ve, mañana dicen que pactamos la elección."
    if hay("defendio_tomas"):
        t neutral "Usted desmintió el audio. Mi hija me preguntó por qué el alcalde me defendía. No supe qué contestarle."
    t "No vine a pedirle nada. Vine a proponerle algo: si NOVA ataca mañana, salimos juntos a decir que es falso."
    t "Gane quien gane, que no gane la mentira."
    menu:
        "Trato hecho. Mañana, juntos.":
            $ hecho("alianza_tomas")
            $ calidad_decision("sab_tomas", 1.0)
            $ subir_afinidad("tomas", 2)
            t feliz "Nunca pensé que diría esto: buenas noches, colega."
        "Mejor no. Cada uno por su lado.":
            $ calidad_decision("sab_tomas", 0.5)
            t seria "Lo entiendo. Suerte mañana, alcalde. A los dos nos va a hacer falta."
    hide tomas with suave
    return
