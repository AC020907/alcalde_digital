## Finales: cinco desenlaces con escena, musica y personajes propios (logica en clases/Destinos.py),
## epilogos que dependen de las rutas intermedias, y la pantalla de resultados.

default final_forzado = None
default persistent.finales_vistos = set()

init python:

    TITULO_FINAL = {f: destinos.DESTINOS[f]["titulo"] for f in destinos.FINALES}

    def indicadores_ciudad():
        c = store.ciudad
        return {"info_verificada": c.info_verificada, "confianza": c.confianza, "convivencia": c.convivencia,
                "bienestar": c.bienestar, "desinformacion": c.desinformacion, "conflictos": c.conflictos}

    def calcular_final():
        estado = {
            "forzado": store.final_forzado,
            "derrota": bool(ciudad.derrota_inmediata()),
            "secreto_publicado": store.final_secreto,
            "secreto_disponible": inv.final_secreto_disponible(store.memoria),
            "uso_audio": hay("uso_audio_tomas"),
            "viral_ok": store.registro_minijuegos.get("viralizacion", {}).get("exito", False),
            "desinformacion": ciudad.get_desinformacion(),
            "confianza": ciudad.get_confianza(),
            "reputacion": jugador.get_reputacion(),
            "salud_ciudad": puntuacion.puntos_ciudad(**indicadores_ciudad()),
            "falsas_compartidas": falsas_compartidas(),
        }
        return destinos.decidir_final(estado)

    def falsas_compartidas():
        return sum(1 for _r, falsa, accion in store.decisiones_pub if falsa and accion in ("compartir", "verificar_si"))

    def puntuacion_partida(final):
        return puntuacion.calcular(
            store.decisiones_pub, store.decisiones_calidad, store.registro_minijuegos,
            list(mem()["pistas"]), inv.PISTAS_CLAVE, indicadores_ciudad(), final=final)

    NOMBRE_MINIJUEGO = {"moderador": "Moderación Express", "contencion": "Caza-Rumores",
                        "rastreador": "Rastreador", "viralizacion": "Ruta de la Verdad",
                        "ritmo": "Duelo de Frecuencias"}

    def lineas_minijuegos():
        lineas = []
        for clave in ("moderador", "contencion", "rastreador", "ritmo", "viralizacion"):
            r = store.registro_minijuegos.get(clave)
            if r:
                nota = r.get("calificacion") or ("S" if r.get("perfecto") else ("A" if r["exito"] else "D"))
                lineas.append((NOMBRE_MINIJUEGO[clave], nota, r["exito"]))
        return lineas

    def escrutinio_partida(final):
        from clases.Eleccion import escrutinio_historia
        return escrutinio_historia(final, indicadores_ciudad(), jugador.get_reputacion(), mem().get("semilla", 0))

    def finales_descubiertos():
        return [f for f in destinos.FINALES if f in persistent.finales_vistos]


label final_caos:
    $ final_forzado = "caos"
    $ renpy.set_return_stack([])
    jump finales

label finales:
    $ final_actual = calcular_final()
    $ final_nuevo = final_actual not in persistent.finales_vistos
    $ persistent.finales_vistos.add(final_actual)
    $ resultado_partida = puntuacion_partida(final_actual)
    hide screen hud_ciudad
    $ musica("final_" + final_actual, fadein=2.5)
    call screen final_cartela(final_actual)

    if final_actual == "secreto":
        call final_fuente_abierta
    elif final_actual == "informada":
        call final_informada
    elif final_actual == "mandato":
        call final_mandato
    elif final_actual == "dividida":
        call final_dividida
    else:
        call final_caos_escena

    call epilogos(final_actual)

    ## Escrutinio: los cuatro candidatos y por que salio este resultado (rubrica §12).
    $ escrutinio_final = escrutinio_partida(final_actual)
    call screen escrutinio_historia(escrutinio_final)

    $ ocultar_avisos_juego()
    if final_nuevo:
        $ sfx("logro")
    if leaderboard_activo():
        $ asegurar_identidad()
        call screen elegir_alias
    $ enviar_resultado_partida(final_actual, resultado_partida)
    call screen pantalla_resultados(final_actual, resultado_partida, final_nuevo)
    call screen cierre_civitas(final_actual)
    return


label final_informada:
    scene bg panorama at fin_informada with lento
    "El lunes amanece despejado sobre Ciudad Nova."
    "Los resultados no los decidió una captura. Llegaron tarde, se contaron dos veces y nadie gritó fraude."
    show claudia feliz at escena("claudia", 0.28) with suave
    show rodrigo feliz at escena("rodrigo", 0.72) with suave
    r feliz "¿Sabe qué compartió hoy mi hermana? El informe del Acueducto. Completo. Con el enlace."
    c feliz "Eso es más difícil que ganar una elección, Rodrigo. Se lo juro."
    hide claudia
    hide rodrigo
    with suave
    "Las cuentas de NOVA siguen publicando cada siete minutos. Ya casi nadie les responde."
    "Ganes o pierdas en las urnas, la ciudad que entregas es una ciudad que pregunta de dónde viene cada cosa."
    return

label final_dividida:
    scene bg ciudad tarde at fin_dividida with lento
    show fin_capa_grieta
    "Los resultados llegan apretados: cuatro mil votos de diferencia. Media ciudad celebra y la otra media sospecha."
    show claudia seria at escena("claudia") with suave
    c seria "Frenamos lo peor. Pero mire los grupos de vecinos: la mitad se partió en dos esta semana."
    c "La mentira del agua ya nadie la cree. Lo que se quedó es la costumbre de no creerle a nadie."
    hide claudia with suave
    "El rumor más grande se apagó, pero dejó grietas: familias que ya no hablan de política en la mesa, amigos que se silenciaron."
    "Ciudad Nova sobrevivió a la semana. Sanar va a tomar más que siete días."
    return

label final_caos_escena:
    scene bg ciudad noche at fin_caos with lento
    show fin_capa_caos
    $ interferencia()
    "Nadie sabe quién ganó. Cada bando tiene sus propios resultados, sus propias capturas y sus propias verdades."
    "Afuera de la registraduría hay dos grupos gritando cifras distintas. Los dos tienen pruebas. Ninguna es real."
    show nova neutral at escena("nova") with Dissolve(0.08)
    n neutral "{cps=36}Ya no tengo que esforzarme, alcalde. La ciudad repite sola.{/cps}"
    n seria "{cps=36}Mañana a las 7:00 publico otra vez. Y la ciudad va a hacer el resto.{/cps}"
    $ interferencia()
    hide nova with Dissolve(0.05)
    "Ciudad Nova cayó en el caos informativo."
    return

label final_mandato:
    scene bg alcaldia at fin_mandato with lento
    show fin_capa_franjas at fin_franjas
    "Ganas por once puntos. La plaza está llena, las pantallas repiten tu nombre y las encuestas acertaron por primera vez en años."
    "Subes al balcón. Lees el discurso que tu equipo escribió. La gente aplaude en los lugares correctos."
    show tomas seria at escena("tomas") with suave
    t seria "Felicitaciones, alcalde. El peritaje del audio sale mañana en todos los medios."
    t "No va a cambiar el resultado. Solo va a cambiar cómo lo recuerden."
    hide tomas with suave
    scene bg despacho at fin_mandato with negro
    show fin_capa_franjas
    $ musica("final_mandato")
    "Esa noche, en el despacho, llega un correo con el asunto 'Gestión de crisis - semana electoral'."
    "Remitente: Resonancia Consultores. Adjunto: una factura. Concepto: 'amplificación de contenido de terceros (audio)'."
    $ interferencia()
    show nova feliz at escena("nova") with Dissolve(0.08)
    n feliz "{cps=34}Fue un placer trabajar con usted, alcalde.{/cps}"
    n neutral "{cps=34}Nos vemos en cuatro años. Para entonces, la ciudad ya va a saber cómo funciona.{/cps}"
    hide nova with Dissolve(0.05)
    "Ganaste la alcaldía. NOVA ganó la costumbre."
    return


## Epilogos: cada personaje cierra su arco segun lo que vivio contigo esta semana.
label epilogos(final_actual):
    $ af = afinidad
    if final_actual == "mandato":
        show claudia seria at escena("claudia") with suave
        c seria "Renuncié a ayudarlo. Voy a publicar el peritaje del audio con mi firma."
        c "No es personal. Bueno, sí lo es. Ya cometí una vez el error de quedarme callada."
        hide claudia with suave
    elif af.get("claudia", 0) >= 2:
        show claudia feliz at escena("claudia") with suave
        if hay("rodrigo_disculpa_2019"):
            c feliz "Lucía me pidió que le enseñara a verificar fotos. Empezamos el martes. Con la foto de 2019, de primer ejercicio."
        else:
            c feliz "Mi investigación sobre NOVA salió en primera página. Y la firmó conmigo. No lo olvido."
        hide claudia with suave
    elif af.get("claudia", 0) <= -1:
        show claudia seria at escena("claudia") with suave
        c seria "Voy a seguir investigando. Sola, si hace falta."
        hide claudia with suave

    if hay("martina_acepto_resonancia") and not hay("martina_rechazo_resonancia"):
        show martina triste at escena("martina") with suave
        m triste "Resonancia me pagó completo. Después salió quiénes eran. Perdí doscientos mil seguidores en un día."
        m "Lo peor es que me lo merecía. Y que nadie me lo dijo a tiempo."
        hide martina with suave
    elif hay("martina_expuso_oferta"):
        show martina feliz at escena("martina") with suave
        m feliz "Mi video exponiendo a Resonancia es el más visto de mi vida. Me ofrecieron un programa en Noticias Nova."
        m "Se llama 'Antes de compartir'. Sí, el nombre fue idea suya."
        hide martina with suave
    elif af.get("martina", 0) >= 2:
        show martina feliz at escena("martina") with suave
        m feliz "Ahora tengo una sección fija: 'Antes de compartir'. Es mi contenido con más vistas. ¿Quién lo diría?"
        hide martina with suave
    elif af.get("martina", 0) <= -1:
        show martina triste at escena("martina") with suave
        m triste "Perdí cincuenta mil seguidores esta semana. Tal vez me lo merecía."
        hide martina with suave

    if af.get("rodrigo", 0) >= 2:
        show rodrigo feliz at escena("rodrigo") with suave
        r feliz "'Primero Pregunto' ya tiene trescientos vecinos. Lucía quiere llevarlo a otros barrios."
        hide rodrigo with suave
    elif af.get("rodrigo", 0) <= -1:
        show rodrigo triste at escena("rodrigo") with suave
        r triste "La tienda sigue abierta. La confianza en la alcaldía... esa no tanto."
        hide rodrigo with suave

    if final_actual not in ("mandato", "secreto"):
        if hay("alianza_tomas") or hay("defendio_tomas"):
            show tomas feliz at escena("tomas") with suave
            t feliz "Vamos a presentar juntos una ley para que las cuentas automáticas se identifiquen. Primera vez que firmo algo con un rival."
            hide tomas with suave
        elif hay("domingo_indiferente") or hay("acuso_sin_evidencia"):
            show tomas seria at escena("tomas") with suave
            t seria "La demanda sigue. No por el resultado, alcalde. Por lo que esta ciudad aprendió a hacer."
            hide tomas with suave
    return


transform resultado_fila(retraso):
    alpha 0.0 xoffset -30
    pause retraso
    easein 0.35 alpha 1.0 xoffset 0

screen pantalla_resultados(final_actual, resultado, final_nuevo=False):
    modal True
    add "bg panorama"
    add Solid("#1b1426d8")
    $ destino = destinos.DESTINOS[final_actual]
    $ claves = inv.grupos_clave(memoria)
    $ vistos = finales_descubiertos()
    frame:
        align (0.5, 0.5)
        xsize 1480
        background Frame("gui/frame.png", 30, 30)
        padding (56, 40)
        has vbox
        spacing 14
        xfill True
        hbox:
            xfill True
            vbox:
                text "FINAL" size 22 bold True color "#e86a7e" kerning 6
                text destino["titulo"] size 60 bold True color "#2b2440" at resultado_fila(0.1)
                text destino["descripcion"] size 22 color "#5b4f72" xmaximum 820 at resultado_fila(0.2)
                if final_nuevo:
                    text "¡Nuevo destino desbloqueado!" size 22 bold True color destino["color"] at resultado_fila(0.3)
            vbox:
                xalign 1.0
                text "PUNTUACIÓN CÍVICA" size 20 bold True color "#8c2f4b" xalign 1.0 kerning 3
                text str(resultado["total"]) size 96 bold True color "#5b5bd6" xalign 1.0 at resultado_fila(0.25)
                text "de 1000" size 20 color "#8b84a8" xalign 1.0
        hbox:
            spacing 26
            xalign 0.5
            for i, (clave, etiqueta) in enumerate([("verificacion", "Verificación"), ("decisiones", "Decisiones"),
                    ("minijuegos", "Minijuegos"), ("investigacion", "Investigación"), ("ciudad", "Ciudad")]):
                vbox at resultado_fila(0.4 + i * 0.08):
                    xsize 220
                    text etiqueta size 18 color "#5b4f72" xalign 0.5
                    text ("%d / %d" % (resultado[clave], puntuacion.MAXIMOS[clave])) size 30 bold True color "#2b2440" xalign 0.5
                    bar value StaticValue(resultado[clave], puntuacion.MAXIMOS[clave]) xsize 200 ysize 8 xalign 0.5 left_bar Solid("#5b5bd6") right_bar Solid("#e6e0f2")
        hbox:
            xalign 0.5
            spacing 40
            text ("Evidencias decisivas: %d de %d" % (sum(claves.values()), len(claves))) size 20 color "#8c2f4b"
            text ("Destinos descubiertos: %d de %d" % (len(vistos), len(destinos.FINALES))) size 20 color "#8c2f4b"
        hbox:
            xalign 0.5
            spacing 34
            for nombre, nota, exito in lineas_minijuegos():
                hbox:
                    spacing 10
                    text nombre size 20 color "#2b2440"
                    text nota size 24 bold True color ("#2f9e8f" if exito else "#c0392b")
        use estado_envio_leaderboard
        if modo_feria_activo:
            hbox:
                xalign 0.5
                spacing 24
                if renpy.loadable("gui/qr_web.png"):
                    add Transform("gui/qr_web.png", xysize=(150, 150)) yalign 0.5
                vbox:
                    yalign 0.5
                    text "¿Te quedaste con ganas?" size 26 bold True color "#8c2f4b"
                    if renpy.loadable("gui/qr_web.png"):
                        text "Escanea el código y sigue la historia completa en tu teléfono." size 21 color "#2b2440"
                    else:
                        text "Pide en el stand el código para jugar la historia completa en tu teléfono." size 21 color "#2b2440"
        if len(vistos) < len(destinos.FINALES):
            text ("Quedan %d destinos por descubrir. ¿Qué habría pasado si elegías distinto?" % (len(destinos.FINALES) - len(vistos))) size 22 italic True color "#5b4f72" xalign 0.5
        hbox:
            xalign 0.5
            spacing 30
            textbutton "ARCHIVO DE DESTINOS":
                style "boton_vn"
                text_style "boton_vn_text"
                action Show("archivo_destinos", destacar=final_actual)
            textbutton "CLASIFICACIÓN":
                style "boton_vn"
                text_style "boton_vn_text"
                action Show("leaderboard_pantalla")
            textbutton "VOLVER AL MENÚ":
                style "boton_vn"
                text_style "boton_vn_text"
                action Return()
                default_focus True


## escrutinio_historia: ver story/finales_cine.rpy (version cinematografica, mismos datos).
