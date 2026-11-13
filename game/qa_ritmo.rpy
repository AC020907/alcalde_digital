## QA del Duelo de Frecuencias dentro del motor real: audio real, reloj real, pantallas reales.
## Un jugador automatico pulsa segun el reloj de la cancion. Inerte salvo con ALCALDE_QA=ritmo.
##   ALCALDE_QA_PASOS = perfecto | mitad | nada      ALCALDE_QA_MODO = historia | feria

init python:
    import json as _qar_json
    qar_obs = {"pos_none": 0, "frames": 0, "capturas": []}

    def qar_instalar(perfil):
        original = VistaDuelo.render

        def render(self, width, height, st, at):
            pos = renpy.music.get_pos(channel="ritmo")
            qar_obs["frames"] += 1
            ahora = _time_ritmo.time()
            if qar_obs.get("ultimo_frame"):
                hueco = (ahora - qar_obs["ultimo_frame"]) * 1000
                qar_obs["hueco_max_ms"] = round(max(qar_obs.get("hueco_max_ms", 0), hueco), 1)
                if hueco > 100:
                    qar_obs.setdefault("tirones", []).append((round(self.t), round(hueco)))
            qar_obs["ultimo_frame"] = ahora
            if pos is None:
                qar_obs["pos_none"] += 1
            muestras = qar_obs.setdefault("muestras", [])
            if not muestras or ahora - muestras[-1][0] > 0.25:
                muestras.append((round(ahora, 2), pos, round(self.t), self.duelo.estado))
            rv = original(self, width, height, st, at)
            d = self.duelo
            if d.estado == "playing" and perfil != "nada":
                for i, n in enumerate(d.notas):
                    if n["estado"] is None and n["time_ms"] <= self.t:
                        if perfil in ("mando", "teclado"):
                            if not n.get("_qa_enviada"):
                                n["_qa_enviada"] = True
                                if perfil == "mando":
                                    qa_pad_evento(("dpleft", "dpdown", "dpup", "dpright")[n["lane"]], "press")
                                else:
                                    qa_pad_evento("key:K_" + "dfjk"[n["lane"]], None)
                        elif perfil == "perfecto" or i % 2 == 0:
                            self.pulsar(n["lane"])
            # renpy.screenshot congela ~400 ms: con ALCALDE_QA_SIN_CAPTURAS se mide el juego sin ese tiron.
            for etiqueta, t_cap in (() if _qa_os.environ.get("ALCALDE_QA_SIN_CAPTURAS") else (("durante", 20000), ("cuenta_atras", 1500))):
                if etiqueta not in qar_obs["capturas"] and self.t >= t_cap and d.estado == "playing":
                    qar_obs["capturas"].append(etiqueta)
                    qa_captura("ritmo_%s_%s" % (perfil, etiqueta))
            return rv

        VistaDuelo.render = render

screen qar_eleccion(valor):
    timer 0.8 action Return(valor)

screen qar_cierre(res):
    timer 1.2 action [Function(qa_captura, "ritmo_%s_resultados" % _qa_os.environ.get("ALCALDE_QA_PASOS", "perfecto")), Return(res)]

label qa_ritmo_motor:
    $ perfil_qar = _qa_os.environ.get("ALCALDE_QA_PASOS", "perfecto")
    $ modo_qar = _qa_os.environ.get("ALCALDE_QA_MODO", "feria")
    $ qar_instalar(perfil_qar)
    $ preparar_partida(feria=(modo_qar == "feria"))
    $ vista_qar = VistaDuelo(modo_qar, "normal")
    show screen duelo_pantalla(vista_qar, "claudia")
    $ inicio_qar = _time_ritmo.time()
    while vista_qar.duelo.estado not in ("results", "aborted") and _time_ritmo.time() - inicio_qar < 150:
        $ qa_call_screen_original("qa_espera", 0.5)
    $ qa_call_screen_original("qar_cierre", vista_qar.duelo.resultado())
    python:
        d = vista_qar.duelo
        qar_obs.update({"estado": d.estado, "resultado": d.resultado(), "drift_max_ms": round(vista_qar.reloj.drift_max(), 1),
                        "segundos": round(_time_ritmo.time() - inicio_qar, 1), "notas": len(d.notas),
                        "fallos": [(n["time_ms"], n["lane"]) for n in d.notas if n["estado"] == "miss"]})
        with open(QA_SALIDA, "w", encoding="utf-8") as f:
            _qar_json.dump(qar_obs, f, ensure_ascii=False, indent=1)
    $ renpy.quit()
