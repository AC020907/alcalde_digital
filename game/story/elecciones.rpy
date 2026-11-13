## DOMINGO - Elecciones: Tomas (segun la semana), La Gran Viralizacion con el aliado que
## cultivaste, revision del expediente, silencio y finales.

label elecciones:
    call screen titulo_acto("DOMINGO", "Elecciones", "Hoy Ciudad Nova decide a quién creerle.")
    $ avanzar_momento(inv.DOMINGO)

    call viajar_a_mision("dom_elecciones")
    scene bg alcaldia at paneo with negro
    $ musica("conversacion")
    show screen hud_ciudad
    show screen tarjeta_lugar("DOMINGO  -  8:00 A.M.", "Frente a la Alcaldía")
    call domingo_tomas

    scene bg operaciones with negro
    show screen tarjeta_lugar("DOMINGO  -  9:40 A.M.", "Centro de Operaciones")
    $ musica("investigacion")
    show claudia seria at escena("claudia") with suave
    c seria "Todas las pantallas están encendidas. Si NOVA ataca hoy, lo vamos a ver aquí primero."
    if hay("martina_acepto_resonancia") and not hay("martina_rechazo_resonancia"):
        c "Y mire esto: Martina amaneció promocionando a Resonancia. Con la etiqueta de los rumores."
        call abrir_civitasnet("net_martina_patrocinio")
    hide claudia with suave
    call eventos_momento(inv.DOMINGO)
    call giro_nova_tardio
    call nueva_publicacion
    call duelo_transmision

    call domingo_ataque
    call revision_expediente

    stop music fadeout 2.0
    hide screen hud_ciudad
    scene negro with lento
    pause 2.0
    "{cps=18}Las urnas cierran.{/cps}"
    pause 1.0
    "{cps=18}Ciudad Nova cuenta sus votos... y también sus mentiras.{/cps}"
    pause 1.5
    jump finales


## Tomas en la manana de la eleccion: cambia segun lo que paso con el audio y el sabado.
label domingo_tomas:
    "Cuatro nombres en el tarjetón: tú, Tomás Vega, Juan Ortega y Elena Ruiz. Ciudad Nova vota hasta las cuatro de la tarde."
    if hay("uso_audio_tomas"):
        show tomas enojada at escena("tomas") with suave
        $ reaccionar("tomas", "temblor")
        t enojada "Mi hija de doce años escuchó ese audio en el colegio. Le preguntó a su profesora si su papá era un ladrón."
        t seria "Usted sabía que era falso. Todos lo sabían. Y lo compartió igual."
        t "Hoy probablemente gane. Felicitaciones. Lo que no va a poder es mirarme a la cara en el debate de dentro de cuatro años."
        hide tomas with suave
        return
    if hay("alianza_tomas"):
        show tomas feliz at escena("tomas") with suave
        t feliz "Colega. Ya preparé el comunicado conjunto. Si NOVA ataca, salimos los dos en vivo."
        t seria "Si mi equipo se entera de que dormí tranquilo por primera vez en un mes, me echan."
        $ hecho("domingo_juego_limpio")
        $ calidad_decision("dom_tomas", 1.0)
        hide tomas with suave
        return

    show tomas seria at escena("tomas") with suave
    if hay("defendio_tomas"):
        t neutral "Alcalde. El viernes desmintió el audio. No tenía por qué hacerlo."
    else:
        t seria "Alcalde. Supongo que ya vio lo que dicen de mí en Civitas."
        t "Que tengo vínculos con criminales. Que robé. Que pedí un soborno con una voz que ni siquiera es la mía."
    if hay("acuso_sin_evidencia"):
        t enojada "Y usted compartió una de esas acusaciones desde la cuenta de la alcaldía."
        $ reaccionar("tomas", "temblor")
        t seria "Mi abogado tiene la captura. Eso también es parte de esta semana."
    t "No le voy a pedir que me defienda. Le voy a pedir que hoy no use las mentiras de nadie."

    menu:
        "No voy a usar mentiras para ganar. Ni contra ti.":
            $ hecho("domingo_juego_limpio")
            $ calidad_decision("dom_tomas", 1.0)
            $ aplicar_consecuencia({"confianza": 3, "convivencia": 2})
            show tomas feliz
            t feliz "...Gracias. No esperaba eso de un rival. Que gane el mejor."
        "Lo que la gente crea ya no es mi problema.":
            $ hecho("domingo_indiferente")
            $ calidad_decision("dom_tomas", 0.1)
            $ aplicar_consecuencia({"conflictos": 3, "confianza": -2})
            show tomas enojada
            $ reaccionar("tomas", "temblor")
            t enojada "Entonces NOVA ya ganó, sin importar quién quede de alcalde."
    hide tomas with suave
    return


## La Gran Viralizacion: el aliado que cultivaste cambia la dificultad y lo que dice.
label domingo_ataque(base=None, reintento=True):
    $ sfx("alarma")
    $ interferencia()
    scene bg viral with destello
    $ musica("crisis", fadein=0.3)
    if nova_descubierto:
        n feliz "{cps=40}Les dije que nos veríamos hoy.{/cps}"
    "Todas las cuentas falsas despiertan al mismo tiempo. El rumor más grande de la semana cae sobre Ciudad Nova a dos horas de abrir las urnas."
    $ aliado = aliado_domingo()
    if aliado == "tomas":
        t "Alcalde, estoy en vivo con mi equipo. ¡Lo que usted frene, mi campaña lo desmiente con su firma y la mía!"
    elif aliado == "claudia":
        c "Tengo las pruebas listas. ¡Frénelo y yo publico todo en cuanto baje!"
    elif aliado == "martina":
        m "¡Alcalde! Estoy en vivo con cien mil personas. ¡Lo que usted frene, yo lo desmiento al instante!"
    elif aliado == "rodrigo":
        r "¡En el barrio nadie reenvía nada! Lucía y los de 'Primero Pregunto' están respondiendo cada cadena."
    elif aliado == "martina_patrocinada":
        "El video de Martina para Resonancia sale justo ahora. Sus seguidores repiten la etiqueta de los rumores sin saberlo."
    $ ayuda_viral = ajustes_viral(base)
    if aliado == "martina_patrocinada":
        $ renpy.notify("El video patrocinado de Martina alimenta a NOVA: tendrás menos tiempo dentro del sistema.")
    elif aliado:
        $ renpy.notify("Gracias a %s, NOVA tardará más en cerrarte la sesión." % NOMBRE_PERSONAJE[aliado])

    if reintento:
        call minijuego_con_reintento("evento_gran_viralizacion", ajustes=ayuda_viral)
    else:
        call evento_gran_viralizacion(ajustes=ayuda_viral)
    $ resultado_viral = _return
    if resultado_viral.get("evidencias_total"):
        call evidencias_rescatadas(resultado_viral)
    $ completar_mision("dom_elecciones")
    return


## Lo que se trajo del sistema de NOVA sirve despues: con todas las pruebas el desmentido es completo.
label evidencias_rescatadas(res):
    if res["evidencias"] >= res["evidencias_total"]:
        show claudia feliz at escena("claudia")
        c feliz "Lo tienes todo: la factura, la lista de cuentas y el análisis original. Esto lo publico ya, con cada documento."
        $ aplicar_consecuencia({"info_verificada": 3, "confianza": 2})
        $ renpy.notify("Evidencia completa: el desmentido llega con pruebas (+ información verificada, + confianza).")
    elif res["evidencias"] * 2 >= res["evidencias_total"]:
        show claudia seria at escena("claudia")
        c seria "Con lo que trajiste puedo desmentir lo principal. No todo, pero sí lo que más se compartió."
        $ aplicar_consecuencia({"info_verificada": 1})
    else:
        show claudia triste at escena("claudia")
        c triste "Saliste con muy poco. Vamos a tener que desmentir sin pruebas, y eso convence a menos gente."
    hide claudia
    return


## Duelo de Frecuencias: NOVA secuestra la transmision oficial del domingo. Ganarlo limpia la senal
## (la Gran Viralizacion sera mas facil); perderlo no bloquea nada, solo deja mas interferencia.
label duelo_transmision(modo="historia"):
    scene bg operaciones with negro
    show screen tarjeta_lugar("DOMINGO  -  10:15 A.M.", "Transmisión oficial de la alcaldía")
    $ musica("nova", fadein=0.4)
    $ aliado_duelo = aliado_domingo()
    $ aliado_duelo = aliado_duelo if aliado_duelo in ("claudia", "martina", "rodrigo", "tomas") else "claudia"
    show claudia seria at escena("claudia", 0.72) with suave
    c seria "Estamos al aire. Diez mil personas viendo el mensaje del alcalde antes de las urnas."
    $ interferencia()
    $ sfx("glitch")
    show nova feliz at escena("nova", 0.28) with Dissolve(0.08)
    n feliz "{cps=40}Qué bonita transmisión. ¿Les molesta si la acompaño con mi propia frecuencia?{/cps}"
    c sorprendida "¡Está metiendo ruido en la señal! Cada frase suya tapa la nuestra."
    c seria "Si respondemos al ritmo exacto, la señal limpia gana. Alcalde, tome los controles."
    hide claudia
    hide nova
    with suave
    call minijuego_ritmo(modo=modo, aliado=aliado_duelo)
    $ resultado_duelo_final = _return
    scene bg operaciones with negro
    if resultado_duelo_final["exito"]:
        show claudia feliz at escena("claudia") with suave
        $ reaccionar("claudia", "salto")
        c feliz "¡Señal limpia! La gente escuchó el mensaje completo, sin cortes."
        c "NOVA va a atacar igual antes de las urnas, pero ahora llega con menos fuerza."
        $ renpy.notify("Duelo ganado: el rumor necesitará más reposts para hacerse viral.")
    else:
        show claudia seria at escena("claudia") with suave
        c seria "Se cortó a ratos. La mitad de la gente vio más ruido que mensaje."
        c "No importa. Lo que viene ahora es lo que cuenta."
    hide claudia with suave
    return
