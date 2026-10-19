## Eventos variables: se eligen al empezar la partida (preparar_partida) y quedan
## guardados en memoria["eventos"]. Nunca quitan pistas necesarias para el giro ni
## para el final secreto, y el puzzle no depende de ellos.
## QA: ALCALDE_SEMILLA=123 o ALCALDE_EVENTOS="1:cuenta_secundaria,2:ninguno"

label eventos_momento(momento):
    $ evento_actual = evento_en(momento)
    if evento_actual:
        call expression "evento_" + evento_actual
    return

label evento_cuenta_secundaria:
    play sound "assets/audio/sfx/notificacion.wav"
    "Una cuenta con diez mil seguidores se suma al rumor del agua: \"mi tía trabaja en el Acueducto\"."
    $ aplicar_consecuencia({"desinformacion": 3})
    c seria "Una tía sin nombre no es una fuente. Pero la gente le cree porque @eco.urbano lo dice."
    return

label evento_filtracion_martina:
    show martina sorprendida
    m sorprendida "Espere. Alguien me acaba de mandar esto por privado: el memo del Acueducto."
    m seria "Pero mire... está cortado. Le falta la última línea."
    menu:
        "Pídele que no lo publique hasta tener el documento completo.":
            $ subir_afinidad("martina", 1)
            $ dar_pista("filtracion_parcial")
            m "Ok. Lo guardo. Si alguien me lo manda cortado, por algo será."
        "Que lo publique: la gente merece saber.":
            $ hecho("martina_publico_filtracion")
            $ aplicar_consecuencia({"desinformacion": 4})
            $ dar_pista("filtracion_parcial")
            m triste "Listo... Ya lo están compartiendo como prueba del veneno. Eso no era lo que quería."
    show martina seria
    return

label evento_foto_descontextualizada:
    play sound "assets/audio/sfx/notificacion.wav"
    "Una foto de una calle inundada circula con el texto \"así está el Barrio Sur HOY\"."
    $ aplicar_consecuencia({"conflictos": 3})
    "Se puede revisar en CivitasNet antes de creerla."
    return

label evento_testimonio_verificable:
    play sound "assets/audio/sfx/notificacion.wav"
    "@vecina.ana sube un video midiendo el agua de su casa con el kit del colegio. Se ven la hora y la dirección."
    $ aplicar_consecuencia({"confianza": 2, "desinformacion": -2})
    return

label evento_rectificacion_salud:
    c feliz "Buenas noticias: llamé a @salud.nova. Van a publicar una rectificación sobre el memo del lunes."
    $ dar_pista("rectificacion_salud")
    $ aplicar_consecuencia({"desinformacion": -3, "info_verificada": 2})
    return

label evento_captura_falsa:
    play sound "assets/audio/sfx/notificacion.wav"
    "Circula una captura de una supuesta publicación de la alcaldía: \"se cancelan las elecciones\"."
    $ aplicar_consecuencia({"desinformacion": 3})
    call abrir_civitasnet("net_captura_falsa")
    if tiene_pista("captura_falsa"):
        $ aplicar_consecuencia({"desinformacion": -3, "confianza": 2})
        "Respondes con la captura anotada: otra tipografía, y una hora que no existe."
    return
