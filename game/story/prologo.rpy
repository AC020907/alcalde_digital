## Prologo: los primeros 30 segundos deben atrapar.

label prologo:
    $ avanzar_momento(inv.PROLOGO)
    scene negro
    stop music
    $ renpy.music.play("assets/audio/sfx/notificacion.wav", channel="ambiente", loop=False)
    call screen intro_notificaciones
    play sound "assets/audio/sfx/alarma_viral.wav"
    scene negro with Dissolve(0.08)
    pause 1.0

    scene bg despacho at paneo with negro
    play music "assets/audio/music/tema_tension.wav" fadein 2.0
    show screen tarjeta_lugar("LUNES  -  6:47 A.M.", "Despacho del alcalde")
    "Tu teléfono no ha dejado de vibrar en toda la noche."
    "Antes de que puedas abrirlo, la puerta se abre de golpe."

    show claudia sorprendida at escena("claudia") with suave
    c sorprendida "Alcalde. ¿Ya vio Civitas?"
    show claudia seria
    c "Una cuenta dice que el agua de Ciudad Nova está envenenada.{w=0.4} Cuarenta mil reposts.{w=0.4} En una hora."
    c "La gente está comprando agua embotellada como si se acabara el mundo. Mire."
    hide claudia with rapido
    call abrir_civitasnet("net_veneno")
    show claudia seria at escena("claudia") with rapido
    c "¿Qué hacemos?"

    menu:
        "Publicar un desmentido ahora mismo.":
            $ aplicar_consecuencia({"confianza": 2, "info_verificada": -2})
            $ hecho("desmintio_sin_datos")
            show claudia seria
            $ reaccionar("claudia", "temblor")
            c "Rápido. Me gusta.{w=0.3} Ojalá no tengamos que tragarnos esas palabras si aparece algo raro en los análisis."
        "Pedir los análisis del agua antes de decir nada.":
            $ aplicar_consecuencia({"info_verificada": 3, "desinformacion": 2})
            $ hecho("pidio_analisis")
            $ subir_afinidad("claudia", 1)
            show claudia feliz
            $ reaccionar("claudia", "salto")
            c feliz "Por fin alguien en este edificio que pregunta antes de hablar."
            c "Los pido ya. Pero el rumor no va a esperarnos."
        "Ignorarlo. Es solo un rumor más.":
            $ aplicar_consecuencia({"desinformacion": 4, "confianza": -2})
            $ hecho("ignoro_rumor_agua")
            $ subir_afinidad("claudia", -1)
            show claudia enojada
            $ reaccionar("claudia", "temblor")
            c enojada "¿Un rumor más?{w=0.3} Alcalde, los rumores no se cansan. Nosotros sí."

    show claudia seria
    c "Hay algo más. Rastreé la primera publicación que habla de veneno."
    c "Salió de una cuenta llamada @verdad.oculta. Sin foto. Sin historial."
    c "{cps=20}Y ayer... esa cuenta no existía.{/cps}"
    $ dar_pista("hip_nova_creo")
    play sound "assets/audio/sfx/rastreo_paso.wav"
    $ interferencia()
    pause 0.4

    c "Faltan seis días para las elecciones. Alguien quiere que Ciudad Nova llegue a ese domingo con miedo."
    hide claudia with suave

    stop music fadeout 1.5
    call screen titulo_acto("CIUDAD NOVA  -  SEIS DÍAS ANTES DE LAS ELECCIONES", "ALCALDE DIGITAL", "Cada publicación cambia la ciudad.")

    scene bg alcaldia at paneo with lento
    play music "assets/audio/music/tema_ciudad.wav" fadein 2.0
    show claudia at escena("claudia") with suave
    c "Una última cosa antes de empezar el día."
    c "Esta semana la gente va a mirar cómo reacciona. ¿Qué clase de alcalde va a ser?"

    menu:
        "Cercano: hablo con la gente, no solo con los medios.":
            $ jugador.set_rol("Ciudadano")
            $ estilo_alcalde = "Cercano"
            c feliz "La gente de los barrios lo va a notar."
        "Analítico: primero los datos, luego la opinión.":
            $ jugador.set_rol("Periodista")
            $ estilo_alcalde = "Analítico"
            c feliz "Ese idioma lo hablo yo. Bien."
        "Mediático: si no estoy en Civitas, no existo.":
            $ jugador.set_rol("Influencer")
            $ estilo_alcalde = "Mediático"
            c seria "Sus palabras van a llegar lejos. Las buenas... y las malas también."
        "Político: cada gesto cuenta para el domingo.":
            $ jugador.set_rol("Candidato")
            $ estilo_alcalde = "Político"
            c seria "Entonces no se equivoque en público."

    c "Revise su teléfono. Civitas no duerme, y hoy nosotros tampoco."
    hide claudia with suave
    show screen hud_ciudad with rapido
    return
