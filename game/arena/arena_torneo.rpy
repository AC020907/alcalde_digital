## Torneo de la Arena: tras el Consejo Civico, cada jugador juega en SU equipo los mismos minijuegos de la
## Historia (misma semilla, mismos ajustes, mismo chart). El cliente solo envia sus decisiones; el servidor
## las vuelve a puntuar (clases/arena/torneo.py), aplica las consecuencias a Ciudad Nova y publica la tabla.

init -4 python:
    from clases.arena import torneo as AT

    ARENA_MODOS = (("completo", "Torneo completo"), ("feria", "Torneo Feria"), ("clasica", "Solo Consejo"))
    ARENA_DESCRIPCION_MODO = {
        "completo": "5 rondas del Consejo Cívico y después 5 pruebas: Moderación Express, Rastreador, Caza-Rumores, Ruta de la Verdad (plataformas) y el Duelo de Frecuencias como final. Unos 25 minutos.",
        "feria": "Versión corta para la feria: 2 rondas del Consejo y las 5 pruebas con menos tiempo. Unos 12 minutos.",
        "clasica": "Solo las rondas del Consejo Cívico y la elección (la Arena original).",
    }
    ARENA_PRUEBAS = AT.PRUEBAS
    ARENA_NOMBRE_PRUEBA = AT.NOMBRE_PRUEBA
    ARENA_COMO_SE_PUNTUA = {
        "moderador": "Borra bots y ataques; deja las críticas reales. Censurar a una persona real resta más que dejar pasar un bot.",
        "contencion": "Frena el rumor antes de que se vuelva viral. Cuenta cuánto se propagó y cuántos rumores interceptaste.",
        "rastreador": "Reconstruye la cadena hasta la fuente. Encontrarla vale 620; el tiempo que te sobre suma hasta 380. Las pistas y las comprobaciones extra restan.",
        "plataformas": "Plataformas: recoge los fragmentos de evidencia y llega al archivo. Las evidencias y la meta son lo que más vale; el tiempo y las detecciones solo ajustan.",
        "ritmo": "Mismo chart para todos (Normal). Precisión 85 % y combo máximo 15 %: PERFECT 100 %, GREAT 70 %, GOOD 30 %, MISS 0 %.",
    }

    def arena_qa_auto():
        return bool(getattr(store, "qa_arena_torneo_auto", False))

    def arena_entregar(datos):
        try:
            AS.cliente.entregar_prueba(datos)
        except OSError:
            pass   # queda pendiente: al reconectar se reenvia con el mismo id (el servidor no lo duplica)

    def arena_datos_arcade(sim):
        return {"reposts": int(sim.reposts), "interceptados": int(sim.interceptados), "exito": bool(sim.exito())}

    def arena_datos_rastreo(p):
        return {"intentos": [[list(s), c] for s, c in p.intentos], "pistas": int(p.pistas_usadas),
                "segundos": round(max(2.0, min(p.tiempo_total, p.transcurrido)), 1)}

    def arena_fila(tabla, jid):
        for f in tabla or ():
            if f["id"] == jid:
                return f
        return None

label arena_jugar_prueba:
    $ spec_ar = AS.cliente.prueba if AS.cliente else None
    if spec_ar is None or AS.prueba_jugada == spec_ar["indice"]:
        return
    $ AS.prueba_jugada = spec_ar["indice"]
    if arena_qa_auto():
        $ import random as _qa_rnd
        $ arena_entregar(AT.payload_bot(spec_ar, 0.85, _qa_rnd.Random("%s|%s" % (spec_ar["semilla"], AS.cliente.jugador_id))))
        return
    $ clave_ar = spec_ar["clave"]
    if clave_ar == "moderador":
        call minijuego_moderador(spec_ar["semilla"], False, spec_ar["cantidad"])
        $ datos_ar = {"decisiones": [bool(b) for _p, b, _ok in moderacion.historial]}
    elif clave_ar == "contencion":
        call minijuego_contencion(spec_ar["focos"], spec_ar["semilla"], False, spec_ar["ajustes"])
        $ datos_ar = arena_datos_arcade(contencion)
    elif clave_ar == "rastreador":
        call minijuego_rastreador(spec_ar["semilla"], False, spec_ar["ajustes"])
        $ datos_ar = arena_datos_rastreo(puzzle_rastreo)
    elif clave_ar == "plataformas":
        call minijuego_plataformas(spec_ar["nivel"], False, None, True, False)
        $ datos_ar = {"traza": [list(seg) for seg in plataformas.traza]}
    else:
        call screen arena_duelo_intro(spec_ar)
        $ duelo_competitivo = True
        call minijuego_ritmo(spec_ar["modo"], False, None, "normal")
        $ duelo_competitivo = False
        $ datos_ar = {"dificultad": "normal", "juicios": [n["estado"] or "miss" for n in vista_duelo.duelo.notas]}
    $ arena_entregar(datos_ar)
    scene bg operaciones
    return

## ---------------- Prueba en curso: presentacion y espera ----------------
screen arena_prueba(c):
    $ s = c.prueba
    $ est = c.estado or {}
    $ entregaron = est.get("entregaron", [])
    $ restante = c.restante()
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xsize 1500
        vbox:
            spacing 16
            text "TORNEO · PRUEBA %d DE %d%s" % (s["indice"] + 1, s["total"], "  ·  FINAL" if s["clave"] == "ritmo" else "") style "arena_nota"
            text s["nombre"].upper() style "arena_titulo" size 52
            text s["contexto"] style "arena_texto"
            text ARENA_COMO_SE_PUNTUA[s["clave"]] style "arena_texto" color "#5b4f72"
            text "Todos juegan con la misma semilla y los mismos ajustes. El servidor vuelve a calcular cada resultado." style "arena_nota"
            hbox:
                spacing 18
                for j in est.get("jugadores", []):
                    frame:
                        background Frame(Solid(ARENA_COLOR_ROL[j["rol"]] + ("ff" if j["id"] in entregaron else "55")), 0, 0)
                        padding (14, 8)
                        text "%s · %s" % (j["nombre"], "terminó" if j["id"] in entregaron else ("desconectado" if not j["conectado"] else "jugando…")) size 20 bold True color "#ffffff"
            if restante is not None:
                text "Tiempo máximo para entregar: %d s" % restante style "arena_nota"
            if c.mi_resultado:
                frame:
                    style "arena_publicacion"
                    xfill True
                    vbox:
                        spacing 4
                        text "Tu resultado: %d / 1000" % c.mi_resultado["normalizado"] size 30 bold True color "#2f9e8f"
                        text c.mi_resultado["resumen"] size 22 color "#2b2440"
                        text "Esperando a que terminen los demás…" style "arena_nota"
            elif AS.prueba_jugada == s["indice"]:
                text "Enviando tu resultado al servidor…" style "arena_texto"
            else:
                textbutton ("¡A JUGAR!" if s["clave"] != "ritmo" else "¡AL DUELO FINAL!") style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return("prueba") default_focus True
            if c.error:
                text c.error style "arena_texto" color "#c0392b"

screen arena_duelo_intro(s):
    modal True
    add "bg operaciones"
    add Solid("#0b0714ee")
    vbox:
        align (0.5, 0.45)
        spacing 20
        text "DUELO DE FRECUENCIAS" size 72 bold True color "#facc15" xalign 0.5 outlines [(4, "#8c2f4b", 0, 0)] at arena_pulso
        text "FINAL DEL TORNEO" size 34 bold True color "#fbf6ee" xalign 0.5
        text "NOVA secuestra la transmisión. Todos juegan la misma canción con el mismo chart: %d notas en 4 carriles." % s["notas"] size 24 color "#c9b8d8" xalign 0.5
        hbox:
            xalign 0.5
            spacing 36
            for j, col in (("PERFECT", "#facc15"), ("GREAT", "#5eead4"), ("GOOD", "#f4b6c2"), ("MISS", "#8b84a8")):
                text j size 30 bold True color col
        text "Teclas D F J K, flechas o el mando. El combo se rompe con GOOD o MISS." size 22 color "#c9b8d8" xalign 0.5
        textbutton "¡LISTO!" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return() default_focus True

transform arena_pulso:
    zoom 1.0
    ease 0.6 zoom 1.05
    ease 0.6 zoom 1.0
    repeat

## ---------------- Resumen de cada prueba ----------------
screen arena_resumen_prueba(c):
    $ r = c.resumen
    $ tabla = r["clasificacion"]
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xsize 1600
        hbox:
            spacing 40
            vbox:
                xsize 760
                spacing 10
                text "RESULTADOS · %s" % r["nombre"].upper() style "arena_titulo"
                text "Gana la prueba: %s" % r["ganador_nombre"] size 34 bold True color "#8c2f4b"
                for jid, res in sorted(r["resultados"].items(), key=lambda kv: -kv[1]["normalizado"]):
                    $ fila = arena_fila(tabla, jid)
                    vbox:
                        hbox:
                            spacing 12
                            text (fila["nombre"] if fila else jid) size 22 bold True color (ARENA_COLOR_ROL[fila["rol"]] if fila else "#2b2440") min_width 230
                            bar value StaticValue(res["normalizado"], 1000) xsize 300 ysize 20 yalign 0.5 left_bar Solid("#8c2f4b" if jid == r["ganador"] else "#a7a5f2") right_bar Solid("#ece6f5")
                            text "%d" % res["normalizado"] size 22 bold True color "#2b2440"
                        text "   " + res["resumen"] size 18 color "#5b4f72"
                null height 6
                text "Ciudad Nova (media del grupo %d/100):" % r["media"] size 22 bold True color "#2b2440"
                if r["delta_ciudad"]:
                    text ", ".join("%s %+d" % (AR.NOMBRE_INDICADOR[k], v) for k, v in r["delta_ciudad"].items()) size 20 color "#2f9e8f"
                else:
                    text "Sin cambios: el grupo jugó en la media." size 20 color "#5b4f72"
            vbox:
                spacing 10
                text "CLASIFICACIÓN DEL TORNEO" style "arena_titulo"
                for f in tabla:
                    hbox:
                        spacing 12
                        text "%d." % f["posicion"] size 26 bold True color "#c58a1b" min_width 40
                        text f["nombre"] size 24 bold (f["id"] == c.jugador_id) color ARENA_COLOR_ROL[f["rol"]] min_width 260
                        text "%d pts" % f["total"] size 24 bold True color "#2b2440"
                text "Consejo Cívico (0–2000) + cada prueba (0–1000)." style "arena_nota"
                if c.soy_anfitrion():
                    textbutton ("Ir al Duelo final ›" if r["indice"] == 3 else ("Ver la elección ›" if r["indice"] == 4 else "Siguiente prueba ›")) style "boton_vn_compacto" text_style "boton_vn_text" action Function(c.enviar, "continuar") default_focus True
                else:
                    text "El anfitrión abrirá la siguiente prueba." style "arena_nota"

## ---------------- Final: eleccion + campeon (conceptos distintos) ----------------
screen arena_final_torneo(c):
    $ f = c.final
    $ t = f["torneo"]
    $ total = max(1, sum(f["votos"].values()))
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xsize 1760
        hbox:
            spacing 40
            vbox:
                xsize 800
                spacing 10
                text "CAMPEÓN DEL TORNEO" style "arena_titulo"
                text t["campeon_nombre"] size 52 bold True color "#c58a1b" at arena_pulso
                for fl in t["clasificacion"]:
                    vbox:
                        text "%d. %s (%s): %d pts" % (fl["posicion"], fl["nombre"], AR.NOMBRE_ROL[fl["rol"]], fl["total"]) size 22 bold True color ARENA_COLOR_ROL[fl["rol"]]
                        text "   Consejo %d · %s" % (fl["consejo"], " · ".join("%s %d" % (AT.NOMBRE_CORTO[k], fl["pruebas"].get(k, 0)) for k in ARENA_PRUEBAS)) size 17 color "#5b4f72"
                text "Ganadores por prueba: " + " · ".join("%s: %s" % (p["nombre"], p["ganador_nombre"]) for p in t["pruebas"]) style "arena_nota"
            vbox:
                spacing 10
                text "ELECCIÓN DE ALCALDE" style "arena_titulo"
                text "Gana %s" % f["ganador_nombre"] size 36 bold True color "#8c2f4b"
                for cid, nombre in AR.CANDIDATOS:
                    hbox:
                        spacing 10
                        text nombre size 20 bold (cid == f["ganador"]) color "#2b2440" min_width 200 yalign 0.5
                        bar value StaticValue(f["votos"][cid], total) xsize 300 ysize 18 yalign 0.5 left_bar Solid("#8c2f4b" if cid == f["ganador"] else "#a7a5f2") right_bar Solid("#ece6f5")
                        text "%d" % f["votos"][cid] size 18 color "#2b2440" yalign 0.5
                text "Ciudad: %s (%d/100)" % (f["ciudad"]["titulo"], f["ciudad"]["indice"]) size 24 bold True color "#2f9e8f"
                text t["mensaje"] style "arena_texto"
                text "¿Por qué?" size 22 bold True color "#2b2440"
                for e in f["explicacion"][-5:]:
                    text "· " + e size 17 color "#2b2440"
                textbutton "Volver al menú" style "boton_vn" text_style "boton_vn_text" action Return(False) default_focus True

style arena_modo:
    background Frame(Solid("#ffffff"), 0, 0)
    selected_background Frame(Solid("#8c2f4b"), 0, 0)
    hover_background Frame(Solid("#f3eefe"), 0, 0)
    padding (18, 10)
style arena_modo_texto is default:
    size 22
    bold True
    color "#2b2440"
    selected_color "#ffffff"
