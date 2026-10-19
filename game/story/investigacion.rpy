## Estado de la investigacion: una sola fuente de verdad (memoria) para CivitasNet,
## el expediente, los hechos narrativos y los eventos variables.
## El contenido inmutable y las consultas puras estan en clases/Investigacion.py.

init -2 python:
    import os
    from clases import Investigacion as inv

default memoria = {"momento": 0, "hechos": [], "hechos_momento": {}, "pistas": {}, "pistas_nuevas": [],
                   "posts_vistos": [], "eventos": {}, "semilla": 0}
default final_secreto = False

init -1 python:

    def mem():
        """Acceso defensivo: completa claves si la partida es de una version anterior."""
        m = store.memoria
        for clave, inicial in (("momento", 0), ("hechos", []), ("hechos_momento", {}), ("pistas", {}),
                               ("pistas_nuevas", []), ("posts_vistos", []), ("eventos", {}), ("semilla", 0)):
            if clave not in m:
                m[clave] = inicial
        return m

    def hay(hecho_id):
        return hecho_id in mem()["hechos"]

    def hecho(hecho_id):
        """Registra un hecho narrativo una sola vez. Avisa si hace aparecer publicaciones."""
        if hecho_id not in inv.HECHOS:
            raise KeyError("Hecho desconocido: %s" % hecho_id)
        m = mem()
        if hecho_id in m["hechos"]:
            return False
        antes = len(inv.posts_nuevos(m))
        m["hechos"].append(hecho_id)
        m["hechos_momento"][hecho_id] = m["momento"]
        if len(inv.posts_nuevos(m)) > antes:
            renpy.notify("CivitasNet: hay publicaciones nuevas")
        return True

    def tiene_pista(pista_id):
        return pista_id in mem()["pistas"]

    def dar_pista(pista_id, estado=None, aviso=True):
        """Agrega o actualiza una ficha del expediente. Nunca la duplica."""
        if pista_id not in inv.PISTAS:
            raise KeyError("Pista desconocida: %s" % pista_id)
        m = mem()
        ficha = inv.PISTAS[pista_id]
        nuevo_estado = estado or ficha["estado"]
        if pista_id in m["pistas"]:
            if estado is None or m["pistas"][pista_id] == estado:
                return False
            m["pistas"][pista_id] = estado
            texto = "Expediente actualizado: %s" % ficha["titulo"]
        else:
            m["pistas"][pista_id] = nuevo_estado
            texto = "Nueva pista: %s" % ficha["titulo"]
        if pista_id not in m["pistas_nuevas"]:
            m["pistas_nuevas"].append(pista_id)
        if aviso:
            renpy.notify(texto)
            sonar("assets/audio/sfx/rastreo_paso.wav")
        return True

    def avanzar_momento(momento):
        m = mem()
        if momento > m["momento"]:
            m["momento"] = momento
            if momento == inv.MIERCOLES and hay("pidio_analisis"):
                hecho("informe_publicado")

    def evento_en(momento):
        return mem()["eventos"].get(momento)

    def preparar_partida(feria=False):
        """Elige la semilla y los eventos variables al empezar; QA: ALCALDE_SEMILLA y ALCALDE_EVENTOS."""
        m = mem()
        semilla_qa = os.environ.get("ALCALDE_SEMILLA")
        m["semilla"] = int(semilla_qa) if semilla_qa else renpy.random.randint(1, 999999)
        forzados = {}
        for par in os.environ.get("ALCALDE_EVENTOS", "").split(","):
            if ":" in par:
                momento, evento = par.split(":", 1)
                forzados[int(momento)] = None if evento in ("", "ninguno") else evento
        m["eventos"] = inv.elegir_eventos(m["semilla"], feria, forzados)

    def feed_sin_ver():
        return len(inv.posts_nuevos(mem()))

    def pistas_sin_ver():
        return len(mem()["pistas_nuevas"])

    def marcar_feed_visto():
        m = mem()
        for post_id in inv.posts_nuevos(m):
            m["posts_vistos"].append(post_id)

    def marcar_expediente_visto():
        del mem()["pistas_nuevas"][:]

    # ----- Efectos narrativos de decisiones y minijuegos -----

    EFECTOS_MINIJUEGO = {
        "moderador": ("moderacion_limpia", "moderacion_fallida"),
        "contencion": ("crisis_contenida", "crisis_desbordada"),
        "rastreador": ("rastreo_exitoso", "rastro_perdido"),
        "viralizacion": ("viral_frenado", "viral_desbordado"),
    }
    ACUSACIONES = ("@investigador.nova", "@ciudadano", "@sol.y.limon")

    def efectos_narrativos(resultado):
        exito, fallo = EFECTOS_MINIJUEGO[resultado["minijuego"]]
        hecho(exito if resultado["exito"] else fallo)
        if resultado["minijuego"] == "rastreador" and resultado["exito"]:
            dar_pista("panel_programacion")
            if resultado.get("inferencia"):
                dar_pista("captura_recortada")
                if tiene_pista("hip_nova_creo"):
                    dar_pista("hip_nova_creo", "refutado")

    def registrar_decision_publicacion(pub, accion):
        compartio_falsa = accion in ("compartir", "verificar_si") and pub.es_falsa
        if compartio_falsa:
            hecho("publico_sin_verificar")
            if pub.autor in ACUSACIONES:
                hecho("acuso_sin_evidencia")
        elif accion == "verificar_no" and pub.es_falsa:
            hecho("verifico_y_desmintio")
        elif accion == "verificar_no" and not pub.es_falsa:
            hecho("reporto_verdad")
