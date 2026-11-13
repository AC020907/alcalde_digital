## MODO FERIA: version condensada (10-12 min medidos: ~1.000 palabras, 4 minijuegos) para exhibicion.
## Incluye los 4 minijuegos (Moderacion, Caza-Rumores, Rastreador corto, Gran Viralizacion),
## CivitasNet, expediente, la oferta a Martina y el audio de Tomas (los cinco finales son alcanzables),
## el giro de NOVA y el final secreto. Termina en un final y vuelve al menu.

define FERIA_CONTENCION = {"duracion": 40.0}
define FERIA_VIRAL = {"nivel": "feria"}
define FERIA_RASTREO = dict(CASO_AGUA, eslabones=2, senuelos=2, tiempo=75.0)

label modo_feria:
    $ modo_feria_activo = True
    $ preparar_partida(feria=True)
    call prologo(corto=True)
    show screen hud_ciudad

    # ----- Lunes: primera publicacion y Moderacion -----
    $ avanzar_momento(inv.LUNES)
    call viajar_a_mision("lunes_plaza")
    scene bg ciudad at paneo with negro
    $ musica("conversacion", fadein=1.0)
    show screen tarjeta_lugar("LUNES  -  9:10 A.M.", "Plaza de la Alcaldía")
    call nueva_publicacion
    call comentario("claudia")
    call eventos_momento(inv.LUNES)
    $ completar_mision("lunes_plaza")

    call viajar_a_mision("lunes_martina")
    scene bg estudio_martina with suave
    show screen tarjeta_lugar("LUNES  -  11:30 A.M.", "Estudio de Martina")
    show martina seria at escena("martina") with suave
    m seria "¡Alcalde! Pregunté en una historia si lo del agua era cierto y ahora mis comentarios están llenos de bots."
    m "¿Me ayuda a limpiarlos? Ojo: la gente que me critica de verdad se queda. Solo borramos bots y mentiras."
    hide martina with suave
    call minijuego_moderador(cantidad=10)
    $ completar_mision("lunes_martina")
    if _return["exito"]:
        $ subir_afinidad("martina", 2)
        show martina feliz at escena("martina") with suave
        m feliz "¡Impecable! Ya publiqué el desmentido con el comunicado del Acueducto."
    else:
        show martina triste at escena("martina") with suave
        m triste "Borramos a gente real... Ya hay capturas diciendo que censuro."
    hide martina with suave

    # ----- Miercoles: consecuencias en CivitasNet, Caza-Rumores y la oferta a Martina -----
    $ avanzar_momento(inv.MIERCOLES)
    scene bg ciudad noche at paneo with negro
    "El lunes termina con el rumor del agua todavía vivo. Lo que hiciste esta mañana ya circula en Civitas."
    "Miércoles. Revisas CivitasNet antes de salir."
    call abrir_civitasnet("net_nos_mintieron" if hay("desmintio_sin_datos") else ("net_acueducto_informe" if hay("pidio_analisis") else None))

    call viajar_a_mision("mie_barrio_sur")
    scene bg barrio_sur at paneo with negro
    show screen tarjeta_lugar("MIÉRCOLES  -  10:20 A.M.", "Barrio Sur")
    pause 1.0
    scene bg barrio_sur conversacion with suave
    show rodrigo enojada at escena("rodrigo") with suave
    $ reaccionar("rodrigo", "temblor")
    r enojada "¡Alcalde! Todo el barrio dice que mañana cierran el hospital. ¡Y se está regando por todas partes!"
    if hay("desmintio_sin_datos"):
        r "Y lo del agua... usted dijo que era cien por ciento segura, y el Acueducto seguía revisando."
    menu:
        "¿Alguien del barrio sabe qué pasó de verdad con el agua?":
            show rodrigo seria
            r seria "Mi primo trabaja en el Acueducto: el papel decía 'repetir análisis', por una tubería rota. Nada de veneno."
            $ dar_pista("testimonio_acueducto")
        "Primero el hospital. Vamos.":
            pass
    call eventos_momento(inv.MIERCOLES)
    hide rodrigo with suave
    scene bg crisis with destello
    $ musica("crisis", fadein=0.5)
    call minijuego_contencion(ajustes=FERIA_CONTENCION)
    $ completar_mision("mie_barrio_sur")
    if _return["exito"]:
        $ subir_afinidad("rodrigo", 2)
    call oferta_resonancia(corto=True)

    # ----- Viernes: Rastreador, giro de NOVA y el audio de Tomas -----
    $ avanzar_momento(inv.VIERNES)
    scene bg ciudad tarde at paneo with negro
    "Dos días después, el rumor del agua vuelve a la tendencia. Alguien lo está empujando a propósito."
    call viajar_a_mision("vie_redaccion")
    scene bg redaccion with negro
    $ musica("investigacion", fadein=1.0)
    show screen tarjeta_lugar("VIERNES  -  4:05 P.M.", "Redacción de Noticias Nova")
    show claudia seria at escena("claudia") with suave
    c seria "El rumor del agua volvió a la tendencia. Si reconstruimos la cadena, llegamos a quien la empezó."
    c "Le pasé las fichas de las cuentas al tablero. Ordénelas antes de que borren el rastro."
    hide claudia with suave
    call minijuego_rastreador(ajustes=FERIA_RASTREO)
    $ completar_mision("vie_redaccion")
    if _return["exito"]:
        $ subir_afinidad("claudia", 2)
    call giro_nova(corto=True)
    call audio_tomas(corto=True)

    # ----- Domingo: Tomas, Gran Viralizacion y expediente -----
    $ avanzar_momento(inv.DOMINGO)
    scene negro with negro
    "{cps=24}Domingo. Día de elecciones. Todo lo que hiciste esta semana va a contar hoy.{/cps}"
    call viajar_a_mision("dom_elecciones")
    scene bg alcaldia at paneo with negro
    show screen tarjeta_lugar("DOMINGO  -  8:00 A.M.", "Frente a la Alcaldía")
    call domingo_tomas
    call duelo_transmision(modo="feria")
    call domingo_ataque(base=FERIA_VIRAL, reintento=False)
    call revision_expediente

    stop music fadeout 2.0
    hide screen hud_ciudad
    scene negro with lento
    pause 1.5
    "{cps=18}Las urnas cierran. Ciudad Nova cuenta sus votos... y sus mentiras.{/cps}"
    jump finales
