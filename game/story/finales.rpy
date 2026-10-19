## Finales: tres desenlaces segun los indicadores, un final secreto por investigacion
## (ver novagiro.rpy: revision_expediente) y epilogos por afinidad.

default final_forzado = None
default persistent.finales_vistos = set()

init python:

    TITULO_FINAL = {
        "informada": "Ciudad Informada",
        "dividida": "Ciudad Dividida",
        "caos": "Caos Informativo",
        "secreto": "Fuente Abierta",
    }
    FINALES_NORMALES = ("informada", "dividida", "caos")

    def calcular_final():
        if store.final_forzado:
            return store.final_forzado
        if ciudad.derrota_inmediata():
            return "caos"
        # Exige las tres evidencias del expediente y publicarlo con fuentes (revision_expediente).
        if store.final_secreto and inv.final_secreto_disponible(store.memoria):
            return "secreto"
        viral_ok = store.registro_minijuegos.get("viralizacion", {}).get("exito", False)
        if ciudad.get_desinformacion() >= 65 or (not viral_ok and ciudad.get_confianza() < 45):
            return "caos"
        if (viral_ok and ciudad.get_desinformacion() <= 45 and ciudad.get_confianza() >= 55
                and jugador.get_reputacion() >= 55):
            return "informada"
        return "dividida"

    NOMBRE_MINIJUEGO = {"moderador": "Moderación Express", "contencion": "Caza-Rumores",
                        "rastreador": "Rastreador", "viralizacion": "La Gran Viralización"}

    def lineas_minijuegos():
        lineas = []
        for clave in ("moderador", "contencion", "rastreador", "viralizacion"):
            r = store.registro_minijuegos.get(clave)
            if r:
                nota = r.get("calificacion") or ("S" if r.get("perfecto") else ("A" if r["exito"] else "D"))
                lineas.append((NOMBRE_MINIJUEGO[clave], nota, r["exito"]))
        return lineas


label final_caos:
    $ final_forzado = "caos"
    $ renpy.set_return_stack([])
    jump finales

label finales:
    $ final_actual = calcular_final()
    $ persistent.finales_vistos.add(final_actual)
    hide screen hud_ciudad
    play music "assets/audio/music/tema_final.wav" fadein 2.0

    if final_actual == "secreto":
        call final_fuente_abierta
    elif final_actual == "informada":
        scene bg panorama at paneo with lento
        "El lunes amanece despejado sobre Ciudad Nova."
        "Las cuentas de NOVA siguen ahí, pero ya casi nadie les responde. La gente aprendió a preguntar de dónde viene cada cosa."
        "Ganes o pierdas en las urnas, la ciudad que entregas es una ciudad que verifica."
    elif final_actual == "dividida":
        scene bg ciudad tarde at paneo with lento
        "Los resultados llegan apretados. Media ciudad celebra y la otra media sospecha."
        "El rumor más grande se apagó, pero dejó grietas: vecinos que ya no se hablan, grupos de chat que se partieron en dos."
        "Ciudad Nova sobrevivió a la semana. Sanar va a tomar más que siete días."
    else:
        scene bg ciudad noche at paneo with lento
        $ interferencia()
        "Nadie sabe quién ganó. Cada bando tiene sus propios resultados, sus propias capturas, sus propias verdades."
        "NOVA sigue publicando cada siete minutos exactos. Ya no necesita esforzarse: la ciudad repite sola."
        "Ciudad Nova cayó en el caos informativo."

    call epilogos

    $ ocultar_avisos_juego()
    call screen pantalla_resultados(final_actual)
    return

label epilogos:
    $ af = afinidad
    if af.get("claudia", 0) >= 2:
        show claudia feliz at escena("claudia") with suave
        c feliz "Mi investigación sobre NOVA salió en primera página. Y la firmaste conmigo. No lo olvido."
        hide claudia with suave
    elif af.get("claudia", 0) <= -1:
        show claudia seria at escena("claudia") with suave
        c seria "Voy a seguir investigando. Sola, si hace falta."
        hide claudia with suave

    if af.get("martina", 0) >= 2:
        show martina feliz at escena("martina") with suave
        m feliz "Ahora tengo una sección fija: 'Antes de compartir'. Es mi contenido con más vistas. ¿Quién lo diría?"
        hide martina with suave
    elif af.get("martina", 0) <= -1:
        show martina triste at escena("martina") with suave
        m triste "Perdí cincuenta mil seguidores esta semana. Tal vez me lo merecía."
        hide martina with suave

    if af.get("rodrigo", 0) >= 2:
        show rodrigo feliz at escena("rodrigo") with suave
        r feliz "En el barrio armamos un grupo para verificar cadenas antes de mandarlas. Ya somos ochenta."
        hide rodrigo with suave
    elif af.get("rodrigo", 0) <= -1:
        show rodrigo triste at escena("rodrigo") with suave
        r triste "La tienda sigue abierta. La confianza en la alcaldía... esa no tanto."
        hide rodrigo with suave
    return


transform resultado_fila(retraso):
    alpha 0.0 xoffset -30
    pause retraso
    easein 0.35 alpha 1.0 xoffset 0

screen pantalla_resultados(final_actual):
    modal True
    add "bg panorama"
    add Solid("#1b1426d8")
    frame:
        align (0.5, 0.5)
        xsize 1100
        background Frame("gui/frame.png", 30, 30)
        padding (60, 46)
        vbox:
            spacing 12
            xfill True
            text "FINAL" size 22 bold True color "#e86a7e" xalign 0.5 kerning 6
            text TITULO_FINAL[final_actual] size 64 bold True color "#2b2440" xalign 0.5 at resultado_fila(0.1)
            $ normales_vistos = len([f for f in persistent.finales_vistos if f in FINALES_NORMALES])
            text ("Finales descubiertos: %d de 3%s" % (normales_vistos, "  +  final secreto" if "secreto" in persistent.finales_vistos else "")) size 20 color "#8b84a8" xalign 0.5
            $ claves = inv.grupos_clave(memoria)
            text ("Expediente: %d de %d evidencias decisivas" % (sum(claves.values()), len(claves)) if final_actual != "secreto" else "Expediente publicado con todas sus fuentes") size 18 color "#8c2f4b" xalign 0.5
            null height 10
            hbox:
                xalign 0.5
                spacing 60
                for i, (nombre, valor, color, critico) in enumerate(indicadores_hud()):
                    vbox at resultado_fila(0.3 + i * 0.1):
                        text nombre size 18 color "#5b4f72" xalign 0.5
                        text "[valor]" size 44 bold True color color xalign 0.5
            null height 6
            for i, (nombre, nota, exito) in enumerate(lineas_minijuegos()):
                hbox at resultado_fila(0.7 + i * 0.1):
                    xalign 0.5
                    spacing 20
                    text nombre size 24 color "#2b2440" min_width 380
                    text nota size 30 bold True color ("#2f9e8f" if exito else "#c0392b")
            null height 14
            textbutton "VOLVER AL MENÚ":
                style "boton_vn"
                text_style "boton_vn_text"
                xalign 0.5
                action Return()
