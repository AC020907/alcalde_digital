## Prologo: los primeros 30 segundos deben atrapar.
## Eres el alcalde, hay un conflicto, alguien te habla y tomas una decision antes del titulo.

label prologo(corto=False):
    $ avanzar_momento(inv.PROLOGO)
    scene negro
    stop music
    $ renpy.music.play("assets/audio/sfx/notificacion.wav", channel="ambiente", loop=False)
    call screen intro_notificaciones
    $ sfx("alarma")
    scene negro with Dissolve(0.08)
    pause 1.0

    scene bg despacho at paneo with negro
    $ musica("tension", fadein=2.0)
    show screen tarjeta_lugar("LUNES  -  6:47 A.M.", "Despacho del alcalde")
    "Tu teléfono no ha dejado de vibrar en toda la noche."
    if not corto:
        "Sobre el escritorio, el discurso de cierre de campaña sigue a medio escribir. Faltan seis días para las elecciones."
    "La puerta se abre sin que nadie llame."

    show claudia sorprendida at escena("claudia") with suave
    c sorprendida "Alcalde. ¿Ya vio Civitas?"
    show claudia seria
    c "Una cuenta dice que el agua de Ciudad Nova está envenenada.{w=0.4} Cuarenta mil reposts.{w=0.4} En una hora."
    c "En el supermercado de la 9 ya no queda agua embotellada. Mire."
    hide claudia with rapido
    call abrir_civitasnet("net_veneno")
    show claudia seria at escena("claudia") with rapido
    if not corto:
        c "Soy Claudia Reyes, de Noticias Nova, por si los de su equipo no se lo dijeron. Me pidieron ayudar esta semana."
        c "Acepté por una razón: yo también quiero saber quién está detrás de esto. No vine a escribirle comunicados bonitos."
    else:
        c "Claudia Reyes, de Noticias Nova. Esta semana trabajo con usted: alguien está fabricando miedo y quiero saber quién."
    c "La ciudad va a mirar lo primero que usted diga. ¿Qué hacemos?"

    menu:
        "Publicar un desmentido ahora mismo.":
            $ aplicar_consecuencia({"confianza": 2, "info_verificada": -2})
            $ hecho("desmintio_sin_datos")
            $ calidad_decision("prologo_agua", 0.4)
            show claudia seria
            $ reaccionar("claudia", "temblor")
            c "Rápido. Eso calma a la gente hoy."
            c "{cps=28}Ojalá no tengamos que tragarnos esas palabras si los análisis dicen otra cosa.{/cps}"
        "Pedir los análisis del agua antes de decir nada.":
            $ aplicar_consecuencia({"info_verificada": 3, "desinformacion": 2})
            $ hecho("pidio_analisis")
            $ calidad_decision("prologo_agua", 1.0)
            $ subir_afinidad("claudia", 1)
            show claudia feliz
            $ reaccionar("claudia", "salto")
            c feliz "Vaya. Alguien en este edificio que pregunta antes de hablar."
            c seria "Los pido ya. Pero el rumor no nos va a esperar: cada hora sin respuesta suma reposts."
        "Ignorarlo. Es solo un rumor más.":
            $ aplicar_consecuencia({"desinformacion": 4, "confianza": -2})
            $ hecho("ignoro_rumor_agua")
            $ calidad_decision("prologo_agua", 0.0)
            $ subir_afinidad("claudia", -1)
            show claudia enojada
            $ reaccionar("claudia", "temblor")
            c enojada "¿Un rumor más? Alcalde, hay señoras haciendo fila con tres botellones cada una."
            c "Los rumores no se cansan. Nosotros sí."

    show claudia seria
    c "Hay algo más. Rastreé la primera publicación que habla de veneno."
    c "Salió de una cuenta llamada @verdad.oculta. Sin foto. Sin historial."
    c "{cps=20}Y ayer... esa cuenta no existía.{/cps}"
    $ dar_pista("hip_nova_creo")
    $ sfx("pista")
    $ interferencia()
    pause 0.4
    if not corto:
        tu "¿Alguien la creó solo para esto?"
        c "O alguien tiene muchas como esa, esperando su turno."
    c "Faltan seis días para las elecciones. Alguien quiere que Ciudad Nova llegue a ese domingo con miedo."
    hide claudia with suave

    stop music fadeout 1.5
    call screen titulo_acto("CIUDAD NOVA  -  SEIS DÍAS ANTES DE LAS ELECCIONES", "ALCALDE DIGITAL", "Cada publicación cambia la ciudad.")

    scene bg alcaldia at paneo with lento
    $ musica("conversacion", fadein=2.0)
    show claudia at escena("claudia") with suave
    c "Una última cosa antes de salir."
    c "Esta semana la gente no va a escuchar lo que usted diga. Va a mirar cómo reacciona. ¿Qué clase de alcalde va a ser?"

    menu:
        "Cercano: hablo con la gente, no solo con los medios.":
            $ jugador.set_rol("Ciudadano")
            $ estilo_alcalde = "Cercano"
            c feliz "En los barrios lo van a notar. Allá nadie lee comunicados."
        "Analítico: primero los datos, luego la opinión.":
            $ jugador.set_rol("Periodista")
            $ estilo_alcalde = "Analítico"
            c feliz "Ese idioma lo hablo yo. Vamos a llevarnos bien."
        "Mediático: si no estoy en Civitas, no existo.":
            $ jugador.set_rol("Influencer")
            $ estilo_alcalde = "Mediático"
            c seria "Sus palabras van a llegar lejos. Las buenas... y las malas también."
        "Político: cada gesto cuenta para el domingo.":
            $ jugador.set_rol("Candidato")
            $ estilo_alcalde = "Político"
            c seria "Entonces no se equivoque en público. Allá afuera todo queda en captura."

    c "Revise su teléfono. Civitas no duerme, y hoy nosotros tampoco."
    hide claudia with suave
    show screen hud_ciudad with rapido
    return
