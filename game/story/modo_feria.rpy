## MODO FERIA: version condensada (~8 min) para exhibicion.
## Incluye los 4 minijuegos (Moderacion, Caza-Rumores, Rastreador corto, Gran Viralizacion),
## CivitasNet, expediente, consecuencias diferidas, el giro de NOVA y el final secreto.
## Termina en un final y vuelve al menu, listo para el siguiente jugador.

define FERIA_CONTENCION = {"duracion": 40.0}
define FERIA_VIRAL = {"duracion": 35.0}
define FERIA_RASTREO = dict(CASO_AGUA, eslabones=2, senuelos=2, tiempo=75.0)

label modo_feria:
    $ modo_feria_activo = True
    $ preparar_partida(feria=True)
    call prologo
    show screen hud_ciudad

    # ----- Lunes: primera publicacion y Moderacion -----
    $ avanzar_momento(inv.LUNES)
    scene bg ciudad at paneo with negro
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.0 if_changed
    show screen tarjeta_lugar("LUNES  -  9:10 A.M.", "Plaza de la Alcaldía")
    call nueva_publicacion
    call comentario("claudia")
    call eventos_momento(inv.LUNES)

    scene bg estudio_martina with suave
    show screen tarjeta_lugar("LUNES  -  11:30 A.M.", "Estudio de Martina")
    show martina seria at escena("martina") with suave
    m seria "¡Alcalde! Mis comentarios están llenos de bots repitiendo lo del agua. ¿Me ayuda a limpiarlos?"
    m "Ojo: la gente que me critica de verdad se queda. Solo borramos bots y mentiras."
    hide martina with suave
    call minijuego_moderador(cantidad=10)
    if _return["exito"]:
        $ subir_afinidad("martina", 2)
        show martina feliz at escena("martina") with suave
        m feliz "¡Impecable! Ya publiqué el desmentido. Cuente conmigo el domingo."
    else:
        show martina triste at escena("martina") with suave
        m triste "Borramos a gente real... Ya hay capturas diciendo que censuro."
    hide martina with suave

    # ----- Miercoles: consecuencias en CivitasNet y Caza-Rumores -----
    $ avanzar_momento(inv.MIERCOLES)
    "Miércoles. Revisas CivitasNet antes de salir."
    call abrir_civitasnet("net_nos_mintieron" if hay("desmintio_sin_datos") else ("net_acueducto_informe" if hay("pidio_analisis") else None))

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
    play music "assets/audio/music/tema_tension.wav" fadein 0.5
    call minijuego_contencion(ajustes=FERIA_CONTENCION)
    if _return["exito"]:
        $ subir_afinidad("rodrigo", 2)

    # ----- Viernes: Rastreador y giro de NOVA -----
    $ avanzar_momento(inv.VIERNES)
    scene bg redaccion with negro
    play music "assets/audio/music/tema_ciudad.wav" fadein 1.0
    show screen tarjeta_lugar("VIERNES  -  4:05 P.M.", "Redacción de Noticias Nova")
    show claudia seria at escena("claudia") with suave
    c seria "El rumor del agua volvió a la tendencia. Si reconstruimos la cadena, llegamos a quien la empezó."
    c "Le pasé las fichas de las cuentas al tablero. Ordénelas antes de que borren el rastro."
    hide claudia with suave
    call minijuego_rastreador(ajustes=FERIA_RASTREO)
    if _return["exito"]:
        $ subir_afinidad("claudia", 2)
    call giro_nova(corto=True)

    # ----- Domingo: Gran Viralizacion y expediente -----
    $ avanzar_momento(inv.DOMINGO)
    if hay("moderacion_limpia"):
        m "¡Alcalde! Estoy en vivo. ¡Lo que usted frene, yo lo desmiento al instante!"
        $ viral_feria = dict(FERIA_VIRAL, umbral_viral=17000)
    else:
        $ viral_feria = FERIA_VIRAL
    call evento_gran_viralizacion(ajustes=viral_feria)
    call revision_expediente

    stop music fadeout 2.0
    hide screen hud_ciudad
    scene negro with lento
    pause 1.5
    "{cps=18}Las urnas cierran. Ciudad Nova cuenta sus votos... y sus mentiras.{/cps}"
    jump finales
