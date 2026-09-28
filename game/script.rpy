# El script del juego comienza aqui.

label start:
    call intro_historia

    "Antes de comenzar, elige tu rol en Ciudad Nova:"
    menu:
        "Ciudadano - Interactua con informacion cotidianamente.":
            $ jugador.set_rol("Ciudadano")
        "Periodista - Detecta noticias falsas con mayor precision.":
            $ jugador.set_rol("Periodista")
        "Influencer - Tus decisiones tienen mayor alcance en Civitas.":
            $ jugador.set_rol("Influencer")
        "Candidato a Alcalde - Construye confianza y responde publicaciones.":
            $ jugador.set_rol("Candidato")

    "[jugador.get_desc_rol()]"
    "Rol seleccionado: [jugador.get_rol()]. La ciudad depende de tus decisiones."

    show screen sistema_civitas
    show screen hud_ciudad

    while banco.hay_mas():
        "Revisa tu telefono... puede aparecer una publicacion nueva en Civitas."

label evaluar_final:
    hide screen sistema_civitas
    hide screen hud_ciudad
    if ciudad.victoria(jugador):
        jump victoria
    else:
        $ razon_derrota = "Los indicadores no alcanzaron el minimo requerido."
        jump derrota

label victoria:
    "Ciudad Nova prospero gracias a tu gestion responsable de la informacion."
    "Puntos: [jugador.get_puntos()] | Reputacion: [jugador.get_reputacion()]%"
    "Tu rol fue: [jugador.get_rol()]. Ciudad Nova te lo agradece."
    return

label derrota:
    hide screen sistema_civitas
    hide screen hud_ciudad
    "[razon_derrota]"
    "Tu mandato ha llegado a su fin. Ciudad Nova ha caido en el caos informativo."
    return
