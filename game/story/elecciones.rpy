## DOMINGO - Elecciones: La Gran Viralizacion, silencio y resultados.

label elecciones:
    call screen titulo_acto("DOMINGO", "Elecciones", "Hoy Ciudad Nova decide a quién creerle.")
    $ avanzar_momento(inv.DOMINGO)

    scene bg alcaldia at paneo with negro
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.5 if_changed
    show screen hud_ciudad
    show screen tarjeta_lugar("DOMINGO  -  8:00 A.M.", "Frente a la Alcaldía")
    show tomas seria at escena("tomas") with suave
    t seria "Alcalde. Tomás Vega, de la oposición. Supongo que ya vio lo que dicen de mí en Civitas."
    t "Que tengo vínculos con criminales. Que robé. Que mi familia huyó del país."
    t "No le voy a pedir que me defienda. Le voy a pedir que no lo use."
    if hay("acuso_sin_evidencia"):
        t enojada "Aunque usted ya lo usó. Compartió una de esas acusaciones desde la cuenta de la alcaldía."
        $ reaccionar("tomas", "temblor")
        t seria "Mi abogado tiene la captura. Eso también es parte de esta semana."

    menu:
        "No voy a usar mentiras para ganar. Ni contra ti.":
            $ aplicar_consecuencia({"confianza": 3, "convivencia": 2})
            show tomas feliz
            t feliz "...Gracias. No esperaba eso de un rival. Que gane el mejor."
        "Lo que la gente crea ya no es mi problema.":
            $ aplicar_consecuencia({"conflictos": 3, "confianza": -2})
            show tomas enojada
            $ reaccionar("tomas", "temblor")
            t enojada "Entonces NOVA ya ganó, sin importar quién quede de alcalde."

    hide tomas with suave
    scene bg operaciones with negro
    show screen tarjeta_lugar("DOMINGO  -  9:40 A.M.", "Centro de Operaciones")
    show claudia seria at escena("claudia") with suave
    c seria "Todas las pantallas están encendidas. Si NOVA ataca hoy, lo vamos a ver aquí primero."
    hide claudia with suave
    call eventos_momento(inv.DOMINGO)
    call giro_nova_tardio
    call nueva_publicacion

    play sound "assets/audio/sfx/alarma_viral.wav"
    $ interferencia()
    scene bg viral with destello
    play music "assets/audio/music/tema_tension.wav"
    if nova_descubierto:
        n feliz "{cps=40}Les dije que nos veríamos hoy.{/cps}"
    "Todas las cuentas falsas despiertan al mismo tiempo. El rumor más grande de la semana cae sobre Ciudad Nova a dos horas de abrir las urnas."
    if afinidad.get("martina", 0) >= 2:
        m "¡Alcalde! Estoy en vivo con cien mil personas. ¡Lo que usted frene, yo lo desmiento al instante!"
        $ ayuda_viral = {"umbral_viral": 17000}
    elif afinidad.get("claudia", 0) >= 3:
        c "Tengo las pruebas listas. ¡Frénelo y yo publico todo en cuanto baje!"
        $ ayuda_viral = {"umbral_viral": 16500}
    else:
        $ ayuda_viral = None

    call minijuego_con_reintento("evento_gran_viralizacion", ajustes=ayuda_viral)
    $ resultado_viral = _return
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
