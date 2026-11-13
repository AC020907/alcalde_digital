## Revision visual (solo desarrollo): se abre desde el laboratorio (Shift+L en el menu
## principal con config.developer). Sirve para revisar sprites, encuadres y fondos.

define FONDOS_REVISION = ["despacho", "redaccion", "operaciones", "estudio_martina", "ciudad", "barrio_sur", "civitas"]

label revision_visual:
    $ hablante = None
    menu:
        "Revisión visual de personajes"

        "Seis expresiones de cada personaje":
            call revision_expresiones
        "Un personaje, dos y tres sobre cada fondo":
            call revision_composiciones
        "Aparición, cambio de expresión y salida":
            call revision_transiciones
        "Volver":
            return
    jump revision_visual

label revision_expresiones:
    python:
        for _nombre, _fondo in (("claudia", "despacho"), ("martina", "estudio_martina"), ("rodrigo", "barrio_sur"),
                                ("tomas", "ciudad"), ("nova", "operaciones")):
            renpy.scene()
            renpy.show("bg " + _fondo)
            for _expr in EXPRESIONES:
                renpy.show((_nombre, _expr), at_list=[escena(_nombre)])
                store.hablante = _nombre
                renpy.say(None, "%s  —  %s" % (NOMBRE_PERSONAJE[_nombre], _expr))
    return

label revision_composiciones:
    python:
        for _fondo in FONDOS_REVISION:
            renpy.scene()
            renpy.show("bg " + _fondo)
            renpy.show(("claudia", "seria"), at_list=[escena("claudia")])
            store.hablante = "claudia"
            renpy.say(c, "Un personaje sobre %s." % _fondo)
            renpy.scene()
            renpy.show("bg " + _fondo)
            renpy.show(("claudia", "seria"), at_list=[escena("claudia", 0.28)])
            renpy.show(("nova", "enojada"), at_list=[escena("nova", 0.72)])
            store.hablante = "nova"
            renpy.say(n, "Dos personajes: el que habla queda en foco.")
            renpy.scene()
            renpy.show("bg " + _fondo)
            renpy.show(("claudia", "seria"), at_list=[escena("claudia", 0.17, 0.84)])
            renpy.show(("martina", "feliz"), at_list=[escena("martina", 0.5, 0.84)])
            renpy.show(("rodrigo", "seria"), at_list=[escena("rodrigo", 0.83, 0.84)])
            store.hablante = "martina"
            renpy.say(m, "Tres personajes y la caja de diálogo al mismo tiempo, con un texto largo para comprobar que nada se tapa.")
    return

label revision_transiciones:
    scene bg redaccion with suave
    show claudia neutral at escena("claudia") with suave
    c "Aparición: entra con un fundido corto y sube a su lugar."
    c feliz "Cambio de expresión por atributo de diálogo: la figura no se mueve."
    show claudia sorprendida
    $ reaccionar("claudia", "sobresalto")
    c "Reacción de sobresalto."
    show claudia enojada
    $ reaccionar("claudia", "temblor")
    c "Reacción de temblor."
    hide claudia with suave
    "Salida: sin personajes fantasma."
    return
