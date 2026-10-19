## Piezas narrativas reutilizables: reintentos de minijuegos, reacciones de
## los personajes a cada publicacion e intro de notificaciones.

define config.side_image_only_not_showing = True

default nova_descubierto = False
default confio_en = None
default estilo_alcalde = "Cercano"

## ---------------- Minijuegos con segunda oportunidad ----------------
## Las consecuencias solo se aplican al resultado final, asi reintentar no acumula castigos.

label minijuego_con_reintento(cual, **parametros):
    $ intentos_minijuego = 0
label .intento:
    call expression cual pass (aplicar=False, **parametros)
    $ resultado_intento = _return
    if not resultado_intento["exito"] and intentos_minijuego == 0:
        menu:
            "No salió bien. ¿Lo intentas otra vez?"

            "Intentarlo de nuevo":
                $ intentos_minijuego += 1
                jump .intento

            "Seguir adelante":
                pass
    $ aplicar_consecuencia(resultado_intento["consecuencia"])
    $ efectos_narrativos(resultado_intento)
    return resultado_intento

## ---------------- Reacciones a la ultima publicacion ----------------

label comentario(quien):
    if ultima_accion is None:
        return
    $ compartio_falsa = ultima_accion in ("compartir", "verificar_si") and ultima_publicacion_falsa
    $ reporto_falsa = ultima_accion == "verificar_no" and ultima_publicacion_falsa
    $ reporto_verdadera = ultima_accion == "verificar_no" and not ultima_publicacion_falsa
    $ ignoro = ultima_accion == "ignorar"

    if quien == "claudia":
        if compartio_falsa:
            c enojada "Compartiste eso sin revisar. Alcalde, así es exactamente como empiezan los incendios."
            $ subir_afinidad("claudia", -1)
        elif reporto_falsa:
            c feliz "Lo reportaste. Bien. Ese tipo de cosas no se ven, pero salvan semanas de caos."
            $ subir_afinidad("claudia", 1)
        elif reporto_verdadera:
            c seria "Reportaste algo que era cierto. Si la alcaldía desmiente verdades, el día que diga algo importante nadie le va a creer."
            $ subir_afinidad("claudia", -1)
        elif ignoro:
            c seria "Ignorar también es una decisión. A veces la peor."
        else:
            c "Buen criterio. Sigamos."
    elif quien == "martina":
        if compartio_falsa:
            m sorprendida "Uy... eso no era cierto, ¿verdad? Mis seguidores ya lo están repitiendo."
        elif reporto_falsa:
            m feliz "¿Lo reportaste? Ok, eso fue elegante. Debería hacer eso más seguido."
            $ subir_afinidad("martina", 1)
        elif reporto_verdadera:
            m sorprendida "¿Reportaste eso? Pero si era real... ahora todos van a decir que la alcaldía censura."
        elif ignoro:
            m "Si nadie lo responde, el algoritmo lo responde por ti. Así funciona esto."
        else:
            m feliz "Eso sí da gusto compartirlo."
    elif quien == "rodrigo":
        if compartio_falsa:
            r enojada "¡Lo compartió hasta usted! ¿Y entonces a quién le creemos los del barrio?"
            $ subir_afinidad("rodrigo", -1)
        elif reporto_falsa:
            r sorprendida "¿Era mentira? Uf... yo ya se lo había mandado a mi hermana."
            $ subir_afinidad("rodrigo", 1)
        elif reporto_verdadera:
            r enojada "¿Cómo que lo reportó? ¡Eso sí pasó! Lo vimos todos en el barrio."
            $ subir_afinidad("rodrigo", -1)
        elif ignoro:
            r triste "En el barrio todos están hablando de eso, y nadie de la alcaldía dice nada."
        else:
            r "Bueno, por lo menos eso sí es verdad."
    return

## ---------------- Intro: notificaciones que saturan la pantalla ----------------

transform notif_entrada(x, y, retraso):
    xpos x ypos y
    alpha 0.0 zoom 0.8
    pause retraso
    easein 0.18 alpha 1.0 zoom 1.0

screen intro_notificaciones():
    add Solid("#0b0812")
    for i, (texto, x, y) in enumerate([
            ("@verdad.oculta: el agua de Ciudad Nova está envenenada", 120, 120),
            ("37 personas compartieron tu mención", 980, 210),
            ("@preocupado99: ¿ES VERDAD LO DEL AGUA???", 320, 330),
            ("Tendencia: #AguaEnvenenada", 1100, 420),
            ("@noticias.nova: estamos verificando", 180, 520),
            ("1.204 reposts en 10 minutos", 860, 610),
            ("@bot.4521: NO LA TOMEN. COMPARTAN.", 420, 700),
            ("Tienes 99+ notificaciones sin leer", 1040, 790),
            ("@vecina.ana: alcalde, ¿qué está pasando?", 140, 870),
            ("@NovaLibre: LOS MEDIOS CALLAN", 760, 950),
            ("#AguaEnvenenada  #AguaEnvenenada", 1280, 110),
            ("Civitas: 4.812 publicaciones nuevas", 560, 250),
        ]):
        frame:
            at notif_entrada(x, y, 0.15 + i * max(0.06, 0.32 - i * 0.025))
            background Frame("gui/frame.png", 30, 30)
            padding (22, 12)
            hbox:
                spacing 10
                add circulo("#e86a7e", "#fbf6ee", 9) yalign 0.5
                text texto size 22 color "#2b2440"
    timer 3.6 action Return()
    key "dismiss" action Return()
