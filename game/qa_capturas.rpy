## QA visual: renderiza escenas y pantallas nuevas y guarda capturas reales del motor.
## Inerte salvo con ALCALDE_QA=capturas y ALCALDE_QA_CAPTURAS=<carpeta>. No entra en las builds.

init -10 python:
    QA_CARPETA = _qa_os.environ.get("ALCALDE_QA_CAPTURAS", "qa_capturas")

    class _QaOpcion(object):
        def __init__(self, caption):
            self.caption = caption
            self.action = NullAction()
            self.chosen = False
            self.kwargs = {}
            self.args = ()

    def qa_captura(nombre):
        if not _qa_os.path.isdir(QA_CARPETA):
            _qa_os.makedirs(QA_CARPETA)
        renpy.screenshot(_qa_os.path.join(QA_CARPETA, nombre + ".png"))

screen qa_disparo(nombre, espera=1.1):
    timer espera action Function(qa_captura, nombre)

# Pantalla llamada por encima de todo: las pantallas modales (expediente, resultados) no la bloquean.
screen qa_disparo_llamada(nombre, espera):
    zorder 999
    timer espera action [Function(qa_captura, nombre), Return()]

label qa_foto(nombre, espera=1.1):
    $ qa_call_screen_original("qa_disparo_llamada", nombre, espera)
    return

label qa_capturas:
    $ preparar_partida(feria=False)
    $ persistent.finales_vistos = {"informada", "mandato"}
    $ persistent.alias = "Vecina-2048"

    show screen main_menu
    call qa_foto("01_menu_principal", 2.0)
    hide screen main_menu

    scene bg ciudad noche at paneo
    show screen hud_ciudad
    show claudia neutral at escena("claudia")
    show screen qa_disparo("02_dialogo_claudia_balcon", 1.4)
    c neutral "En 2019, durante la inundación, yo trabajaba en el turno de noche de Noticias Nova.{w=1.8}{nw}"
    hide screen qa_disparo

    scene bg operaciones
    show rodrigo seria at escena("rodrigo", 0.83, 0.84)
    show claudia triste at escena("claudia", 0.17, 0.84)
    show screen qa_disparo("03_dialogo_dos_personajes", 1.4)
    c triste "Usted es el señor de la tienda. El esposo de...{w=1.8}{nw}"
    hide screen qa_disparo

    show screen choice([_QaOpcion("Claudia, creo que le debes algo a Rodrigo."), _QaOpcion("No es el momento. Tenemos un rumor que frenar.")])
    call qa_foto("04_decision", 1.4)
    hide screen choice
    hide claudia
    hide rodrigo

    $ avanzar_momento(inv.VIERNES)
    $ dar_pista("audio_tomas", aviso=False)
    show nova neutral at escena("nova")
    show screen qa_disparo("05_nova_audio", 1.4)
    n neutral "{cps=38}Si lo comparte desde su cuenta, mañana nadie se acuerda del agua. El domingo gana usted.{/cps}{w=1.8}{nw}"
    hide screen qa_disparo
    hide nova

    show screen civitasnet(llamada=True, destacar="net_audio_tomas")
    call qa_foto("06_civitasnet_audio", 1.6)
    hide screen civitasnet

    show screen expediente
    call qa_foto("07_expediente", 1.4)
    hide screen expediente

    $ resultado_qa = {"verificacion": 260, "decisiones": 210, "minijuegos": 170, "investigacion": 120, "ciudad": 74, "total": 834}
    $ estado_envio = ("ok", "Puesto 3 en la clasificación (Vecina-2048)")
    $ registro_minijuegos.update({"moderador": {"exito": True, "calificacion": "S"}, "contencion": {"exito": True, "calificacion": "A"},
                                  "rastreador": {"exito": True, "calificacion": "B"}, "viralizacion": {"exito": False, "calificacion": "D"}})
    $ modo_feria_activo = True
    show screen pantalla_resultados("informada", resultado_qa, True)
    call qa_foto("08_resultados", 2.2)
    hide screen pantalla_resultados

    show screen archivo_destinos("mandato")
    call qa_foto("09_archivo_destinos", 1.6)
    hide screen archivo_destinos

    $ persistent.top_cache = {"historia": [
        {"rank": 1, "alias": "Cronista-1180", "score": 962, "final_title": "Fuente Abierta"},
        {"rank": 2, "alias": "Vecina-2048", "score": 834, "final_title": "Ciudad Informada"},
        {"rank": 3, "alias": "Testigo-7731", "score": 512, "final_title": "Mandato Prestado"}]}
    $ persistent.mejor_local = {"historia": {"score": 834, "final": "informada"}}
    show screen leaderboard_pantalla
    call qa_foto("10_clasificacion", 1.4)
    hide screen leaderboard_pantalla

    show screen elegir_alias
    call qa_foto("11_alias", 1.2)
    hide screen elegir_alias

    $ persistent.controles_tactiles = True
    show screen mapa_viaje("centro")
    call qa_foto("12_mapa_tactil", 1.6)
    hide screen mapa_viaje
    $ persistent.controles_tactiles = False
    $ renpy.quit()
