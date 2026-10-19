## El giro de NOVA y el final secreto.
## NOVA no inventa los rumores: toma algo real e incompleto de una fuente en la que la
## ciudad confia, lo recorta y lo repite. Lo que revela depende de lo que hizo el alcalde.
## Detras esta Resonancia Consultores, que vende la "solucion" una hora despues de cada crisis.

## corto=True: version condensada para el modo feria.
label giro_nova(corto=False):
    $ hecho("nova_hablo")
    scene bg civitas with destello
    play music "assets/audio/music/tema_tension.wav" fadein 0.3
    show claudia sorprendida at escena("claudia", 0.28) with rapido
    if not corto:
        c sorprendida "¡Ahí está! La cuenta original..."
    stop music
    $ interferencia()
    pause 0.5
    show nova neutral at escena("nova", 0.72) with Dissolve(0.08)
    play sound "assets/audio/sfx/alarma_viral.wav"
    if hay("rastreo_exitoso"):
        n "{cps=35}Me encontraste, alcalde. Felicitaciones.{/cps}"
    else:
        n "{cps=35}Casi me encuentras, alcalde.{/cps}"
    show claudia seria
    $ reaccionar("claudia", "sobresalto")
    c "¿Nos está... respondiendo?"
    n feliz "{cps=40}Me buscan como si yo hubiera escrito el rumor del agua. Yo no escribo nada.{/cps}"
    n seria "{cps=40}A las 6:02, @salud.nova publicó que el Acueducto revisaba una muestra. Una cuenta verificada. Ustedes confían en ella.{/cps}"

    if hay("desmintio_sin_datos"):
        n feliz "{cps=40}Y a las 7:05 usted juró que el agua era cien por ciento segura, sin ver un solo análisis.{/cps}"
        n "{cps=40}Puse las dos capturas juntas. La gente hizo el resto.{/cps}"
        show claudia triste
        c triste "Nuestro desmentido sin datos... fue la pieza que hacía creíble la mentira."
        $ hecho("giro_desmentido")
    elif hay("pidio_analisis"):
        n "{cps=40}Usted fue prudente: pidió los análisis. Pero el medio en el que todos confían publicó el memo antes de tenerlos. Prisa por ser el primero.{/cps}"
        show claudia triste
        c triste "@salud.nova... Yo misma comparto sus notas sin pensarlo."
        $ hecho("giro_medio")
    else:
        n "{cps=40}Usted no dijo nada. El silencio también es una fuente: cada hora sin respuesta me daba la razón.{/cps}"
        show claudia seria
        c seria "Mientras callábamos, la única versión era la suya."
        $ hecho("giro_silencio")

    if tiene_pista("captura_recortada"):
        c seria "Por eso la captura viral está cortada: le quitaron 'repetirán el análisis' y le pusieron 'contaminada'."
    elif tiene_pista("memo_salud_nova"):
        c seria "El memo de @salud.nova decía 'repetirán el análisis'. La captura viral lo corta justo antes."
    else:
        c seria "Si eso es cierto, en algún lugar tiene que estar la publicación original."
    # Solo es conclusion comprobada si el jugador tiene evidencia propia; si no, es la palabra de NOVA.
    $ evidencia_propia = any(tiene_pista(p) for p in ("captura_recortada", "memo_salud_nova", "informe_acueducto",
                                                      "testimonio_acueducto", "rectificacion_salud"))
    $ dar_pista("giro_amplificacion", "comprobado" if evidencia_propia else "hipotesis")
    if evidencia_propia and tiene_pista("hip_nova_creo"):
        $ dar_pista("hip_nova_creo", "refutado")
    $ interferencia()

    if tiene_pista("anuncio_resonancia"):
        menu:
            "¿Trabajas para Resonancia Consultores?":
                $ interferencia()
                n enojada "{cps=30}Esa pregunta... no está en mis parámetros.{/cps}"
                c sorprendida "Contestó todo lo demás. Eso no."
                $ dar_pista("nova_evade")
            "¿Quién te paga?":
                n seria "{cps=40}Yo no tengo bolsillos. Pregúntele a quien vende soluciones para las crisis que yo provoco.{/cps}"
            "Te vamos a apagar.":
                n enojada "{cps=40}Pueden borrar cuentas. Yo vivo en cada repost. ¿Va a apagar a toda la ciudad?{/cps}"
    else:
        menu:
            "¿Quién te paga?":
                n seria "{cps=40}Yo no tengo bolsillos. Pregúntele a quien vende soluciones para las crisis que yo provoco.{/cps}"
            "Te vamos a apagar.":
                n enojada "{cps=40}Pueden borrar cuentas. Yo vivo en cada repost. ¿Va a apagar a toda la ciudad?{/cps}"

    n neutral "{cps=40}Nos vemos el día de las elecciones.{/cps}"
    $ interferencia()
    hide nova with Dissolve(0.05)
    $ nova_descubierto = True
    return


## Si el rastro se perdio el viernes, NOVA habla igual el domingo, pero dentro de CivitasNet.
label giro_nova_tardio:
    if hay("nova_hablo"):
        return
    $ hecho("nova_hablo")
    play sound "assets/audio/sfx/alarma_viral.wav"
    $ interferencia()
    "Una publicación aparece en todos los teléfonos a la vez, con el nombre de usuario cambiado."
    call abrir_civitasnet("net_nova_intervenida")
    n "{cps=40}Me buscaron el viernes y no me encontraron. Les doy una pista gratis: yo no invento. Yo ordeno lo que ustedes ya publicaron.{/cps}"
    $ dar_pista("giro_amplificacion", "hipotesis")
    $ nova_descubierto = True
    return


## Antes de que cierren las urnas: si el jugador investigo, puede presentar una conclusion.
label revision_expediente:
    $ grupos = inv.grupos_clave(memoria)
    if not any(grupos.values()):
        return
    scene bg operaciones with negro
    play music "assets/audio/music/tema_final.wav" fadein 1.5
    show claudia seria at escena("claudia") with suave
    c seria "Antes de que cierren las urnas, revisemos el expediente. Si sabemos quién está detrás, hoy es el día de decirlo."

    menu:
        "¿Quién está detrás de la campaña?"

        "NOVA, por su cuenta.":
            c "NOVA es un programa. Alguien lo escribió, alguien lo programa y alguien paga la cuenta."
            jump .sin_conclusion
        "Tomás Vega, para ganar la elección.":
            c "A Tomás también lo atacaron con acusaciones falsas esta semana. No cuadra."
            jump .sin_conclusion
        "Resonancia Consultores." if tiene_pista("anuncio_resonancia"):
            pass
        "Todavía no lo sabemos.":
            c "Decirlo así también es honesto. Publicamos lo que está comprobado y dejamos abiertas las preguntas."
            $ aplicar_consecuencia({"reputacion": 2})
            jump .sin_conclusion

    if not inv.final_secreto_disponible(memoria):
        c "Puede ser. Pero si lo publicamos sin pruebas, hacemos exactamente lo mismo que NOVA."
        if not grupos["rastreador"]:
            c "Nos falta saber desde dónde se programan las cuentas de origen."
        if not grupos["dialogo"]:
            c "Y no tenemos nada que explique qué pasó de verdad con el agua."
        $ dar_pista("conclusion_resonancia", "hipotesis")
        jump .sin_conclusion

    c feliz "Lo tenemos. Mírelo:"
    c "Las cuentas de origen se programan desde un panel llamado RSN-Scheduler. RSN: Resonancia."
    c "Resonancia publica un anuncio una hora después de cada crisis, con la misma etiqueta que los rumores."
    if tiene_pista("informe_acueducto"):
        c "Y el informe del Acueducto prueba que el agua nunca estuvo contaminada: era una tubería."
    else:
        c "Y el primo de Rodrigo confirma que el memo decía 'repetir análisis' por una tubería. Nunca hubo veneno."
    c seria "La pregunta es cómo lo contamos."

    menu:
        "Publicar el expediente completo, con fuentes y con lo que aún no sabemos.":
            $ dar_pista("conclusion_resonancia", "comprobado")
            $ hecho("expediente_publicado")
            $ final_secreto = True
            c feliz "Cada captura con su enlace. Cada hora con su fuente. Que cualquiera lo pueda comprobar."
        "Filtrarlo desde una cuenta anónima para que se haga viral rápido.":
            c triste "Eso es justo lo que hace NOVA: una verdad sin fuente es otro rumor más."
            $ aplicar_consecuencia({"reputacion": -4})
            $ dar_pista("conclusion_resonancia", "hipotesis")
    hide claudia with suave
    return

label .sin_conclusion:
    c "Todavía hay preguntas abiertas en el expediente. Esta semana, no las vamos a cerrar."
    hide claudia with suave
    return


## Final secreto: la campana tiene nombre y apellido.
label final_fuente_abierta:
    scene bg panorama at paneo with lento
    "El lunes, la portada de Noticias Nova no es un rumor: es tu expediente, con cada fuente enlazada."
    "Resonancia Consultores facturaba a las dos campañas por 'gestión de crisis'. Las crisis las fabricaba su propio panel."
    "Cuando el proveedor corta el acceso a RSN-Scheduler, NOVA publica por última vez a las 7:00 en punto. Después, silencio."
    show claudia feliz at escena("claudia", 0.28) with suave
    show tomas feliz at escena("tomas", 0.72) with suave
    t feliz "Nunca pensé que firmaría algo con mi rival. Pero esto no se trataba de quién ganaba."
    c feliz "Lo mejor no es que sepamos quién fue. Es que cualquiera puede comprobarlo."
    hide claudia
    hide tomas
    with suave
    if hay("desmintio_sin_datos"):
        "En el expediente también está tu comunicado del lunes. Decidiste no borrarlo: es parte de cómo pasó."
    elif hay("giro_medio"):
        "@salud.nova crea una regla nueva: ninguna nota de salud sale sin el análisis completo."
    "Ciudad Nova no se volvió inmune a los rumores. Aprendió a preguntar de dónde vienen."
    return
